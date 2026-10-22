#!/usr/bin/env python3
"""Bound APB periodic ULog traffic using this build's generated uORB structs."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SIZES = {"bool": 1, "char": 1, "float": 4, "double": 8}
SIZES.update({prefix + str(bits) + "_t": bits // 8
              for prefix in ("int", "uint") for bits in (8, 16, 32, 64)})


def topic_size(text, name):
    body = text.split("struct __EXPORT " + name + "_s {", 1)[1].split("#ifdef __cplusplus", 1)[0]
    total = 0
    for line in body.splitlines():
        line = line.split("//", 1)[0].strip()
        if not line or line.startswith("#") or line.startswith("struct "):
            continue
        match = re.fullmatch(r"(\w+)\s+\w+(?:\[(\d+)\])?;", line)
        if not match or match[1] not in SIZES:
            raise ValueError("unrecognized field in {}: {}".format(name, line))
        total += SIZES[match[1]] * int(match[2] or 1)
    if not total:
        raise ValueError("empty message: " + name)
    return total  # includes generated padding, conservative for ULog


def check(build):
    profile = (ROOT / "boards/orqa/apb/src/logging_topics.inc").read_text()
    topics = re.findall(r'^add_topic\("(\w+)", (\d+)\);$', profile, re.M)
    if len(topics) != profile.count("add_topic(") or not topics:
        raise ValueError("unexpected or unbounded APB topic declaration")
    rates = []
    headers = {}
    for path in (build / "uORB/topics").glob("*.h"):
        text = path.read_text()
        for topic in re.findall(r"ORB_DECLARE\((\w+)\)", text):
            headers[topic] = (path.stem, text)
    for name, interval in topics:
        interval = int(interval)
        if interval < 100:
            raise ValueError("APB topic interval below 100 ms: " + name)
        actual_name, text = headers[name]  # e.g. vehicle_gps_position aliases sensor_gps
        size = topic_size(text, actual_name)
        rates.append((name, (size + 5) * 1000 / interval))
    total = sum(rate for _, rate in rates)
    # ULog nominal wire budget is 0.7 * (230400 / 20) = 8064 B/s.
    # Reserve >2.5 KB/s for packet overhead, events and parameter bursts.
    if total > 5500:
        raise ValueError("APB periodic log budget exceeded: {:.0f} > 5500 B/s".format(total))
    print("PASS: {} topics; conservative periodic ULog {:.0f}/5500 B/s; nominal stream budget 8064 B/s".format(len(topics), total))
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    check(parser.parse_args().build)

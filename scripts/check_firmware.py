#!/usr/bin/env python3
"""Reject mismatched firmware, wrong load addresses and exhausted flash budgets."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]


def validate(bundle, raw, board, label, elf):
    if bundle["board_id"] != board["board_id"]:
        raise ValueError("Firmware board ID does not match the target")
    image = zlib.decompress(base64.b64decode(bundle["image"], validate=True))
    if image != raw or bundle["image_size"] != len(raw):
        raise ValueError("Packaged image does not match the raw binary")
    if bundle["image_maxsize"] != board["app_size"]:
        raise ValueError("Firmware prototype disagrees with the application partition")
    origin = board["app_origin"] if label == "default" else 0x08000000
    limit = board["app_size"] if label == "default" else board["app_origin"] - origin
    minimum = board["min_free"] if label == "default" else 0
    if len(raw) < 8 or len(raw) > limit - minimum:
        raise ValueError("Firmware exceeds partition or minimum free-space budget")
    stack, reset = struct.unpack_from("<II", raw)
    if stack & 3 or not 0x20000000 <= stack <= 0x40000000:
        raise ValueError("Invalid initial stack pointer")
    if not reset & 1 or not origin <= reset - 1 < origin + len(raw):
        raise ValueError("Reset vector does not point inside the firmware partition")
    if elf[:7] != b"\x7fELF\x01\x01\x01" or struct.unpack_from("<H", elf, 18)[0] != 40:
        raise ValueError("Expected a 32-bit little-endian ARM ELF")
    phoff = struct.unpack_from("<I", elf, 28)[0]
    phsize, phnum = struct.unpack_from("<HH", elf, 42)
    loads = []
    for index in range(phnum):
        kind, offset, vaddr, paddr, filesz, memsz, flags, align = struct.unpack_from(
            "<8I", elf, phoff + index * phsize)
        if kind == 1 and filesz and 0x08000000 <= paddr < 0x08200000:
            loads.append((paddr, paddr + filesz))
    if not loads or min(start for start, end in loads) != origin:
        raise ValueError("ELF load address does not match the bootloader layout")
    if max(end for start, end in loads) > origin + len(raw):
        raise ValueError("ELF flash segments exceed the binary")
    return {"board_id": board["board_id"], "load_address": hex(origin),
            "image_bytes": len(raw), "partition_bytes": limit,
            "free_bytes": limit - len(raw), "minimum_free_bytes": minimum}


def revision(path):
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("px4", type=Path)
    parser.add_argument("target")
    args = parser.parse_args()
    config = json.loads((ROOT / "build-config.json").read_text())
    try:
        vendor, name, label = args.target.split("_")
        if vendor != "orqa" or label not in ("default", "bootloader"):
            raise ValueError("Unknown target")
        board = config["boards"][name]
        if name == "f405pro" and label == "bootloader":
            raise ValueError("F405 uses the factory bootloader")
        build = args.px4 / "build" / args.target
        raw_path = build / (args.target + ".bin")
        bundle_path = build / (args.target + ".px4")
        bundle = json.loads(bundle_path.read_text())
        if revision(args.px4) != config["px4_revision"] or bundle["git_hash"] != config["px4_revision"]:
            raise ValueError("Firmware was not built from the pinned PX4 revision")
        report = validate(bundle, raw_path.read_bytes(), board, label,
                          (build / (args.target + ".elf")).read_bytes())
        report.update({"target": args.target, "px4_revision": config["px4_revision"],
                       "port_revision": revision(ROOT), "container": config["container"],
                       "hardware_validated": False})
        report["sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (raw_path, bundle_path)}
        # Include the exact installed patch/overlay digest even for local dirty builds.
        report["source_sha256"] = {}
        for base, directory in ((ROOT, ROOT / "patches"), (args.px4, args.px4 / "boards/orqa")):
            for path in directory.rglob("*"):
                if path.is_file():
                    report["source_sha256"][str(path.relative_to(base))] = hashlib.sha256(path.read_bytes()).hexdigest()
        output = build / (args.target + ".manifest.json")
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print("{}: {} bytes free; bundle, board ID and ELF layout verified".format(
            args.target, report["free_bytes"]))
    except (ValueError, KeyError, OSError, struct.error, zlib.error, subprocess.CalledProcessError) as error:
        print("ERROR: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

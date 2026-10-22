"""Host-only probe of two native mavlink-router v4 processes, no hardware."""
import argparse
import json
import os
import pathlib
import signal
import socket
import struct
import subprocess
import tempfile
import time
import importlib.util
import threading
from types import SimpleNamespace
from unittest.mock import patch

from pymavlink.dialects.v20 import common as mav
from pyulog import ULog

ROOT = pathlib.Path(tempfile.mkdtemp(prefix="orqa-router-probe-"))
BIN = pathlib.Path(os.environ["MAVLINK_ROUTER_BIN"])


def port():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def record(kind, payload):
    return struct.pack("<HB", len(payload), ord(kind)) + payload


def probe(mode):
    case = pathlib.Path(tempfile.mkdtemp(prefix=mode + "-", dir=ROOT))
    logdir = case / "card-mount" / "px4"
    fc_port, recorder_port = port(), port()
    while recorder_port == fc_port:
        recorder_port = port()
    gcs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gcs.bind(("127.0.0.1", 0))
    gcs.settimeout(0.1)
    fc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fc.bind(("127.0.0.1", 0))
    fc.settimeout(0.05)
    tx = mav.MAVLink(None, srcSystem=1, srcComponent=1)
    rx = mav.MAVLink(None)
    blocked = case / "blocked"
    if mode == "open-failure":
        blocked.write_text("A regular file, not a directory\n")
        logdir = blocked / "logs"
    core = case / "core.conf"
    core.write_text(f"""[General]
TcpServerPort=0
[UdpEndpoint fc]
Mode=Server
Address=127.0.0.1
Port={fc_port}
[UdpEndpoint recorder]
Mode=Normal
Address=127.0.0.1
Port={recorder_port}
[UdpEndpoint gcs]
Mode=Normal
Address=127.0.0.1
Port={gcs.getsockname()[1]}
""")
    recorder = case / "recorder.conf"
    log_option = "" if mode == "disabled" else f"Log={logdir}\n"
    recorder.write_text(f"""[General]
TcpServerPort=0
MavlinkDialect=auto
{log_option}LogMode=always
MinFreeSpace=0
MaxLogFiles=0
LogTelemetry=false
[UdpEndpoint fc]
Mode=Server
Address=127.0.0.1
Port={recorder_port}
""")
    (case / "empty-config.d").mkdir()
    processes = []
    handles = []
    messages = []
    worker = None
    shutdown = threading.Event()
    identity_patch = None

    def send(msg):
        fc.sendto(msg.pack(tx), ("127.0.0.1", fc_port))
        tx.seq = (tx.seq + 1) % 256

    def heartbeat():
        send(mav.MAVLink_heartbeat_message(mav.MAV_TYPE_QUADROTOR,
             mav.MAV_AUTOPILOT_PX4, 0, 0, mav.MAV_STATE_STANDBY, 3))

    def pump(seconds, predicate=lambda _: False):
        deadline = time.monotonic() + seconds
        next_hb = 0
        while time.monotonic() < deadline:
            if time.monotonic() >= next_hb:
                heartbeat()
                next_hb = time.monotonic() + 0.2
            try:
                data, _ = fc.recvfrom(65535)
            except socket.timeout:
                continue
            for msg in rx.parse_buffer(data) or []:
                messages.append(msg)
                if predicate(msg):
                    return msg
        return None

    def is_start(msg):
        return msg.get_type() == "COMMAND_LONG" and msg.command == mav.MAV_CMD_LOGGING_START

    def data_msg(seq, payload, ack=True, offset=0):
        klass = mav.MAVLink_logging_data_acked_message if ack else mav.MAVLink_logging_data_message
        return klass(2, 0, seq, len(payload), offset,
                     list(payload.ljust(249, b"\0")))

    def is_ack(seq):
        return lambda m: m.get_type() == "LOGGING_ACK" and m.sequence == seq

    try:
        if mode == "supervisor":
            spec = importlib.util.spec_from_file_location("recorder", pathlib.Path(__file__).resolve().parents[1] / "companion/apb/recorder.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logdir.parent.mkdir()
            runtime = case / "runtime"
            runtime.mkdir()
            device = logdir.parent.stat().st_dev
            # Only physical SD identity is mocked. Production guard, fd
            # pinning, configuration and native subprocess are exercised.
            identity_patch = patch.object(module, "card_identity", return_value=("42", f"{os.major(device)}:{os.minor(device)}"))
            identity_mock = identity_patch.start()
            args = SimpleNamespace(mount=logdir.parent, reserve_mib=1, runtime=runtime,
                                   port=recorder_port, system_id=1, router=str(BIN))
            worker = threading.Thread(target=module.supervise, args=(args, shutdown))
            worker.start()
        for config in ((core,) if mode == "supervisor" else (recorder, core)):
            out = open(case / (config.stem + ".log"), "w")
            handles.append(out)
            processes.append(subprocess.Popen([str(BIN), "-c", str(config), "-d",
                str(case / "empty-config.d")], stdout=out, stderr=subprocess.STDOUT))
        start = pump(3.0, is_start)
        assert all(p.poll() is None for p in processes), "router exited unexpectedly"
        if mode in ("disabled", "open-failure"):
            assert start is None, "unexpected logging request"
            if mode == "open-failure":
                blocked.unlink()
                blocked.mkdir()
                assert pump(2, is_start) is None, "logger unexpectedly recovered"
            outcome = "no request without Log" if mode == "disabled" else "open failure disables logging until recorder restart"
        else:
            assert start is not None, "no logging start request"
            send(mav.MAVLink_command_ack_message(mav.MAV_CMD_LOGGING_START,
                mav.MAV_RESULT_ACCEPTED, 0, 0, start.get_srcSystem(), start.get_srcComponent()))
            initial = (b"ULog\x01\x12\x35\x01" + struct.pack("<Q", 1000000)
                + record("B", bytes(40))
                + record("F", b"probe:uint64_t timestamp;float value;")
                + record("A", struct.pack("<BH", 0, 7) + b"probe"))
            first = record("D", struct.pack("<HQf", 7, 1000001, 1.25))
            second = record("D", struct.pack("<HQf", 7, 1000002, 2.5))
            payload = initial + first
            assert len(payload) < 249
            send(data_msg(0, payload))
            assert pump(1, is_ack(0)), "header was not acknowledged"
            send(data_msg(0, payload))  # reliable header retransmission
            assert pump(1, is_ack(0)), "duplicate header was not acknowledged"
            if mode == "split":
                send(data_msg(1, second[:5], ack=False))
                send(data_msg(2, second[5:], ack=False, offset=255))
            elif mode == "gap":
                send(data_msg(1, second[:5], ack=False))
                # Sequence 2 is lost; resume on a complete message at offset 3.
                send(data_msg(3, b"abc" + second, ack=False, offset=3))
            else:
                send(data_msg(1, second, ack=False))
            pump(0.4)
            files = list(logdir.glob("*.ulg"))
            assert len(files) == 1, files
            assert files[0].read_bytes() == initial + first + second, "ULog reconstruction differs"
            assert ULog(str(files[0])).get_dataset("probe").data["value"].tolist() == [1.25, 2.5]
            assert not logdir.parent.is_mount(), "test path unexpectedly mounted"
            outcome = "ULog exact bytes, ACK, duplicate suppression, " + mode
            if mode == "supervisor":
                identity_mock.side_effect = module.NotReady("simulated card removal")
                assert pump(3, lambda m: m.get_type() == "COMMAND_LONG" and m.command == mav.MAV_CMD_LOGGING_STOP), "removal did not stop stream"
                assert processes[-1].poll() is None, "core stopped with card"
                identity_mock.side_effect = None
                identity_mock.return_value = ("43", f"{os.major(device)}:{os.minor(device)}")
                assert pump(9, is_start), "recorder did not recover after card return"
                send(mav.MAVLink_command_ack_message(mav.MAV_CMD_LOGGING_START, mav.MAV_RESULT_ACCEPTED, 0, 0, 2, 0))
                send(data_msg(0, payload))
                assert pump(1, is_ack(0)), "recovered header was not acknowledged"
                pump(0.3)
                assert len(list(logdir.glob("*.ulg"))) == 2, "recovery did not create a new log"
                outcome += "; card removal stops stream, return creates fresh log"
                with patch.object(module, "check_space", side_effect=module.NotReady("simulated full card")):
                    assert pump(3, lambda m: m.get_type() == "COMMAND_LONG" and m.command == mav.MAV_CMD_LOGGING_STOP), "low space did not stop stream"
                    assert processes[-1].poll() is None
                    assert len(list(logdir.glob("*.ulg"))) == 2, "low space deleted evidence"
                outcome += "; low space stops recording without deleting logs"
        gcs_parser = mav.MAVLink(None)
        got_heartbeat = False
        try:
            while True:
                data, _ = gcs.recvfrom(65535)
                got_heartbeat |= any(m.get_type() == "HEARTBEAT"
                                     for m in gcs_parser.parse_buffer(data) or [])
        except socket.timeout:
            pass
        assert got_heartbeat, "core did not forward heartbeat to GCS"
        if mode in ("normal", "supervisor"):
            if worker:
                shutdown.set()
                worker.join(timeout=10)
                assert not worker.is_alive(), "supervisor did not stop"
            else:
                processes[0].send_signal(signal.SIGTERM)
                processes[0].wait(timeout=3)
            heartbeat()
            data, _ = gcs.recvfrom(65535)
            assert any(m.get_type() == "HEARTBEAT" for m in gcs_parser.parse_buffer(data) or [])
            assert processes[-1].poll() is None
            outcome += "; core survives recorder stop"
            if mode == "normal":
                outcome += "; unmounted path accepted (unsafe without guard)"
        return {"mode": mode, "result": "PASS", "detail": outcome, "evidence": str(case)}
    finally:
        shutdown.set()
        if worker:
            worker.join(timeout=12)
            assert not worker.is_alive(), "supervisor cleanup failed"
        if identity_patch:
            identity_patch.stop()
        for process in reversed(processes):
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        for handle in handles:
            handle.close()
        fc.close()
        gcs.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("modes", nargs="*", default=["disabled", "normal", "split", "gap", "open-failure", "supervisor"])
    args = parser.parse_args()
    for mode in args.modes:
        print(json.dumps(probe(mode)), flush=True)

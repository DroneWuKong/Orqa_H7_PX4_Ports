#!/usr/bin/env python3
"""Supervise an isolated mavlink-router v4 ULog recorder on a real SD mount.

Never mounts/formats media, changes FC parameters, deletes logs, opens the
UART, or restarts the main router. Python standard library only.
"""
import argparse
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import threading
import time


class NotReady(RuntimeError):
    pass


def unescape(value):
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), value)


def mount_record(text, path):
    found = None
    for line in text.splitlines():
        left, right = line.split(" - ", 1)
        fields, extra = left.split(), right.split()
        if unescape(fields[4]) == str(path):
            if "rw" not in fields[5].split(",") or "rw" not in extra[2].split(","):
                raise NotReady("SD mount is read-only")
            found = (fields[0], fields[2])  # mount ID and major:minor
    if found is None:
        raise NotReady("SD is not mounted (a directory is not sufficient)")
    return found


def card_identity(path):
    if path.is_symlink() or path.resolve() != path:
        raise NotReady("SD path must not contain symlinks")
    ident = mount_record(Path("/proc/self/mountinfo").read_text(), path)
    device = Path("/sys/dev/block", ident[1]).resolve(strict=True)
    if (device / "partition").exists():
        device = device.parent
    if (device / "device/type").read_text().strip() != "SD":
        raise NotReady("mounted device is not an SD card (eMMC/root rejected)")
    return ident


def check_space(fd, minimum):
    fs = os.fstatvfs(fd)
    if fs.f_flag & os.ST_RDONLY:
        raise NotReady("SD filesystem became read-only")
    if fs.f_bavail * fs.f_frsize < minimum:
        raise NotReady("SD free space below reserve; no logs will be deleted")


def open_card(path, minimum):
    """Pin the directory to the checked filesystem, even across unmount races."""
    before = card_identity(path)
    parent = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    fd = None
    try:
        stat = os.fstat(parent)
        if "{}:{}".format(os.major(stat.st_dev), os.minor(stat.st_dev)) != before[1]:
            raise NotReady("SD device changed while opening")
        check_space(parent, minimum)
        try:
            os.mkdir("px4", 0o750, dir_fd=parent)
        except FileExistsError:
            pass
        fd = os.open("px4", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        if os.fstat(fd).st_dev != stat.st_dev or card_identity(path) != before:
            raise NotReady("SD mount changed while opening log directory")
        # Native router marks old files read-only; reject symlinks before it
        # scans the directory. The card/log directory must remain trusted.
        if any(os.path.islink("/proc/self/fd/{}/{}".format(fd, name)) for name in os.listdir(fd)):
            raise NotReady("symlink in dedicated log directory")
        return fd, before
    except BaseException:
        if fd is not None:
            os.close(fd)
        raise
    finally:
        os.close(parent)


def configuration(fd, port, system_id):
    # Using an inherited descriptor avoids path re-resolution into rootfs.
    return """[General]
TcpServerPort=0
MavlinkDialect=common
Log=/proc/self/fd/{fd}
LogMode=always
LogSystemId={system_id}
LogTelemetry=false
MinFreeSpace=0
MaxLogFiles=0
[UdpEndpoint fc]
Mode=Server
Address=127.0.0.1
Port={port}
""".format(fd=fd, port=port, system_id=system_id)


def watch_output(pipe, failed):
    errors = ("Unable to write", "Could not open log dir", "Unable to open Log",
              "fsync failed", "Invalid ULog", "Not enough bandwidth")
    try:
        for line in pipe:
            print("router: " + line.rstrip(), flush=True)
            if any(error in line for error in errors):
                failed.set()
    finally:
        pipe.close()


def stop_child(child):
    if child.poll() is None:
        # ULog::stop sends LOGGING_STOP and closes the log on SIGTERM.
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)  # Never spawn another recorder over a stuck one.


def supervise(args, shutdown):
    previous = None
    while not shutdown.is_set():
        fd, child = None, None
        reader = None
        try:
            fd, identity = open_card(args.mount, args.reserve_mib * 1024 * 1024)
            with tempfile.TemporaryDirectory(prefix="recorder-", dir=args.runtime) as run:
                run = Path(run)
                (run / "empty.d").mkdir()
                conf = run / "recorder.conf"
                conf.write_text(configuration(fd, args.port, args.system_id))
                failed = threading.Event()
                child = subprocess.Popen([args.router, "-c", str(conf), "-d", str(run / "empty.d")],
                    pass_fds=(fd,), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, errors="replace")
                reader = threading.Thread(target=watch_output, args=(child.stdout, failed), daemon=True)
                reader.start()
                print("SD ready; recorder started (mount {}, FC {})".format(identity, args.system_id), flush=True)
                previous = None
                last_size, last_progress = 0, time.monotonic()
                try:
                    while not shutdown.wait(1):
                        if child.poll() is not None or failed.is_set():
                            raise NotReady("recorder exited or reported a write/protocol error")
                        if card_identity(args.mount) != identity:
                            raise NotReady("SD mount changed")
                        check_space(fd, args.reserve_mib * 1024 * 1024)
                        size = sum(os.stat(name, dir_fd=fd, follow_symlinks=False).st_size
                                   for name in os.listdir(fd) if name.endswith(".ulg"))
                        if size != last_size:
                            last_size, last_progress = size, time.monotonic()
                        elif time.monotonic() - last_progress > 30:
                            raise NotReady("no log growth for 30 seconds (check PX4 logger/link)")
                finally:
                    stop_child(child)
                    reader.join(timeout=2)
        except (NotReady, OSError) as error:
            message = str(error)
            if message != previous:
                print("Recording paused: " + message, flush=True)
                previous = message
        finally:
            if child is not None:
                stop_child(child)
            if fd is not None:
                os.close(fd)
        shutdown.wait(5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mount", type=Path, default=Path("/sdcard"))
    parser.add_argument("--runtime", type=Path, default=Path("/run/orqa-px4-recorder"))
    parser.add_argument("--router", default="/usr/bin/mavlink-routerd")
    parser.add_argument("--port", type=int, default=14560)
    parser.add_argument("--system-id", type=int, default=1)
    parser.add_argument("--reserve-mib", type=int, default=256)
    parser.add_argument("--check", action="store_true", help="check SD readiness, do not start recording")
    args = parser.parse_args()
    if not args.mount.is_absolute() or args.mount == Path("/"):
        parser.error("mount must be a dedicated absolute SD path")
    if not 1 <= args.system_id <= 255 or args.system_id == 2:
        parser.error("FC ID must be 1..255 excluding router v4's reserved logging ID 2")
    if not 1024 <= args.port <= 65535 or args.reserve_mib < 32:
        parser.error("invalid unprivileged UDP port or reserve below 32 MiB")
    if args.check:
        try:
            fd, identity = open_card(args.mount, args.reserve_mib * 1024 * 1024)
            os.close(fd)
            print("Ready: {} {}".format(args.mount, identity))
            return 0
        except (NotReady, OSError) as error:
            print("Not ready: " + str(error))
            return 1
    version = subprocess.run([args.router, "-V"], capture_output=True, text=True, timeout=5, check=True)
    if not re.search(r"^mavlink-router version v4\s*$", version.stdout + version.stderr, re.M):
        parser.error("use the tested mavlink-router v4 build")
    args.runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    shutdown = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: shutdown.set())
    supervise(args, shutdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

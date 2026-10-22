#!/usr/bin/env python3
"""Install APB logging files, preserving the known vendor helper. No restarts."""
import argparse
import hashlib
from pathlib import Path
import shutil

VENDOR_HASH = "501cf034fb6afb04f4fb8036139ab9b131d005c19863d522c95a76d8616452f6"
FILES = {
    "recorder.py": "usr/local/lib/orqa-px4/recorder.py",
    "mount_sd.py": "usr/local/lib/orqa-px4/mount_sd.py",
    "orqa-px4-recorder.service": "etc/systemd/system/orqa-px4-recorder.service",
    "90-orqa-px4-logging.conf": "etc/mavlink-router/config.d/90-orqa-px4-logging.conf",
    "orqa-drive-mounting.sh": "etc/udev/scripts/orqa-drive-mounting.sh",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(root, source):
    root = root.resolve()
    helper = root / FILES["orqa-drive-mounting.sh"]
    backup = helper.with_name(helper.name + ".pre-px4-logging")
    # Preflight every destination before any write. This is not a generic
    # updater: unknown site customizations require review, never overwrite.
    for name, target in FILES.items():
        dest = root / target
        if any(p.is_symlink() for p in (dest, *dest.parents)):
            raise ValueError("symlinked destination: " + str(dest))
        if dest.exists() and digest(dest) != digest(source / name):
            if dest != helper or digest(dest) != VENDOR_HASH:
                raise ValueError("preserve/review existing file: " + str(dest))
    if backup.is_symlink() or (backup.exists() and digest(backup) != VENDOR_HASH):
        raise ValueError("unexpected vendor backup")
    if not helper.exists() or (not backup.exists() and digest(helper) != VENDOR_HASH):
        raise ValueError("requires the inspected Scarthgap v1.0.5 vendor helper")
    if not backup.exists():
        shutil.copy2(helper, backup)
    for name, target in FILES.items():
        dest = root / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Same-directory replacement prevents consumers seeing a partial file.
        import tempfile
        with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as staging:
            staging.write((source / name).read_bytes())
            stage = Path(staging.name)
        stage.chmod(0o755 if name.endswith(".sh") else 0o644)
        stage.replace(dest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/"), help="alternate root for image staging")
    args = parser.parse_args()
    install(args.root, Path(__file__).resolve().parent)
    print("Installed; no services restarted. Read companion/apb/README.md before activation.")

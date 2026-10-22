#!/usr/bin/env python3
"""Install the Orqa overlay and reviewed patches into the pinned PX4 checkout."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(px4, *args, check=True):
    return subprocess.run(["git", "-C", str(px4), *args], check=check,
                          text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def install(px4):
    px4 = px4.resolve()
    config = json.loads((ROOT / "build-config.json").read_text())
    if git(px4, "rev-parse", "HEAD").stdout.strip() != config["px4_revision"]:
        raise ValueError("PX4 must be at {} ({})".format(config["px4_version"], config["px4_revision"]))
    tag = git(px4, "rev-parse", config["px4_version"] + "^{commit}", check=False)
    if tag.returncode or tag.stdout.strip() != config["px4_revision"]:
        raise ValueError("Fetch the matching PX4 {} tag for version generation".format(config["px4_version"]))
    if Path(git(px4, "rev-parse", "--show-toplevel").stdout.strip()).resolve() != px4:
        raise ValueError("Pass the PX4 repository root")

    source = ROOT / "boards/orqa"
    destination = px4 / "boards/orqa"
    if destination.is_symlink():
        raise ValueError("Refusing a symlinked boards/orqa directory")
    state_path = Path(git(px4, "rev-parse", "--git-path", "orqa-overlay.json").stdout.strip())
    if not state_path.is_absolute():
        state_path = px4 / state_path
    previous = json.loads(state_path.read_text()) if state_path.exists() else {}
    incoming = {str(p.relative_to(source)): digest(p) for p in source.rglob("*") if p.is_file()}
    existing = {}
    if destination.exists():
        for path in destination.rglob("*"):
            if path.is_symlink():
                raise ValueError("Refusing symlink in overlay: {}".format(path))
            if path.is_file():
                name = str(path.relative_to(destination))
                existing[name] = digest(path)
                if existing[name] not in (previous.get(name), incoming.get(name)):
                    raise ValueError("Preserve local board changes before installing: {}".format(path))

    # Check every patch and destination before making any change. Never guess
    # how to resolve a modified upstream file or an unknown board checkout.
    pending = []
    for patch in sorted((ROOT / "patches").glob("*.patch")):
        if git(px4, "apply", "--check", str(patch), check=False).returncode == 0:
            pending.append(patch)
        elif git(px4, "apply", "--reverse", "--check", str(patch), check=False).returncode != 0:
            raise ValueError("Patch conflicts with local source changes: {}".format(patch.name))

    for patch in pending:
        git(px4, "apply", str(patch))
    for name in existing.keys() - incoming.keys():
        (destination / name).unlink()  # Only unchanged files owned by a previous installation.
    shutil.copytree(source, destination, dirs_exist_ok=True)
    state_path.write_text(json.dumps(incoming, indent=2, sort_keys=True) + "\n")
    print("Installed Orqa boards and storage patch on PX4 {}".format(config["px4_version"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("px4", type=Path)
    args = parser.parse_args()
    try:
        install(args.px4)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print("ERROR: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

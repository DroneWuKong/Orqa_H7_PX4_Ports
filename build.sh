#!/usr/bin/env bash
# build.sh — single-command Docker build for orqa/h7quadcore
#
# Requires:
#   - Docker running (Docker Desktop on Windows with WSL2, or Docker on Linux/macOS)
#   - PX4-Autopilot cloned at ../PX4-Autopilot (tag v1.15.4) as a sibling of this directory
#
# Usage:
#   ./build.sh                          Build default app firmware (orqa_h7quadcore_default)
#   ./build.sh orqa_h7quadcore_default  Same as above (explicit)
#   ./build.sh orqa_h7quadcore_bootloader  Build PX4 NuttX bootloader
#
# Output artifacts:
#   ../PX4-Autopilot/build/orqa_h7quadcore_default/orqa_h7quadcore_default.px4
#   ../PX4-Autopilot/build/orqa_h7quadcore_bootloader/orqa_h7quadcore_bootloader.bin
#
# DFU flash procedure (see .planning/phases/01-scaffold-and-build/01-01-PLAN.md):
#   Step 1: ./build.sh orqa_h7quadcore_bootloader
#           dfu-util -a 0 --dfuse-address 0x08000000 -D \
#             ../PX4-Autopilot/build/orqa_h7quadcore_bootloader/orqa_h7quadcore_bootloader.bin
#   Step 2: Unplug/replug USB (no BOOT button) then flash via QGroundControl or:
#           ./build.sh orqa_h7quadcore_default upload

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PX4_SRC="$(cd "${SCRIPT_DIR}/../PX4-Autopilot" && pwd)"
CCACHE_DIR="${HOME}/.ccache"
TARGET="${1:-orqa_h7quadcore_default}"

if [ ! -d "${PX4_SRC}" ]; then
  echo "ERROR: PX4-Autopilot not found at ${PX4_SRC}"
  echo "Clone PX4-Autopilot at tag v1.15.4 as a sibling directory of this project:"
  echo "  cd $(dirname "${SCRIPT_DIR}")"
  echo "  git clone --branch v1.15.4 --recurse-submodules https://github.com/PX4/PX4-Autopilot.git"
  exit 1
fi

mkdir -p "${CCACHE_DIR}"

echo "========================================"
echo "  Orqa H7 QuadCore PX4 Build"
echo "========================================"
echo "  Target:     ${TARGET}"
echo "  PX4 source: ${PX4_SRC}"
echo "  Docker:     px4io/px4-dev-nuttx-focal:2022-08-12"
echo "========================================"

docker run --rm \
  --env=LOCAL_USER_ID="$(id -u)" \
  --env=CCACHE_DIR="${CCACHE_DIR}" \
  --volume="${PX4_SRC}:${PX4_SRC}:rw" \
  --volume="${CCACHE_DIR}:${CCACHE_DIR}:rw" \
  --workdir="${PX4_SRC}" \
  px4io/px4-dev-nuttx-focal:2022-08-12 \
  /bin/bash -c "make ${TARGET}"

echo "========================================"
echo "  Build complete: ${TARGET}"
echo "========================================"

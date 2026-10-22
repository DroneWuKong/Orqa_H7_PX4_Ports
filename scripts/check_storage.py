#!/usr/bin/env python3
"""Exercise patched storage failure paths and boot policy without a flight board."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run_shell(script, expected, prefix):
    result = subprocess.run(["bash", "-c", prefix + "\n" + script], check=True,
                            text=True, stdout=subprocess.PIPE)
    for word in ("FORMAT", "FLASH", "SD", "RAM"):
        actual = word in result.stdout.splitlines()
        if actual != (word in expected):
            raise RuntimeError("Boot policy failed: {} (expected {})".format(result.stdout, expected))


def check_boot(px4):
    startup = (px4 / "ROMFS/px4fmu_common/init.d/rcS").read_text()
    # Execute the real format/mount-failure branch with commands stubbed; never
    # mount or format any host device. NSH's 'set name value' is emulated here.
    format_branch = startup[startup.index("\tif [ $SDCARD_FORMAT = yes ]"):
                            startup.index("\tif [ $SDCARD_AVAILABLE = yes ]")]
    prefix = '''
set() { export "$1=$2"; }
mkfatfs() { echo FORMAT; return 1; }
mount() { return 1; }
'''
    run_shell(format_branch, set(), prefix + "SDCARD_FORMAT=no; SDCARD_AVAILABLE=no")
    run_shell(format_branch, {"FORMAT"}, prefix + "SDCARD_FORMAT=yes; SDCARD_AVAILABLE=no")
    run_shell(format_branch, set(), prefix + "SDCARD_FORMAT=no; SDCARD_AVAILABLE=yes")

    start = startup.index("\tif param compare -s SYS_DM_BACKEND 1")
    end = startup.index("\n\t#\n", start)
    mission_branch = startup[start:end]
    prefix = '''
param() { [ "${@: -1}" = "$BACKEND" ]; }
mft() { [ "$HAS_FLASH" = yes ]; }
dataman() {
  case "$*" in
    'start -r') echo RAM;;
    'start -f /fs/mtd_waypoints') echo FLASH;;
    start) echo SD;;
    *) exit 42;;
  esac
}
'''
    for backend, flash, expected in ((0, "yes", {"FLASH"}), (0, "no", {"SD"}),
                                     (1, "yes", {"RAM"}), (-1, "yes", set())):
        run_shell(mission_branch, expected, prefix + "BACKEND={}; HAS_FLASH={}".format(backend, flash))
    print("PASS: failed SD mount never formats; explicit format and mission backend choices respected")


def check_driver(px4):
    source = (px4 / "platforms/nuttx/src/px4/common/px4_mtd.cpp").read_text()
    probe = source[source.index("static int spi_nor_attach("):source.index("static int ramtron_attach(")]
    geometry = source[source.index("int px4_mtd_get_geometry("):source.index("/*\n  get partition size")]
    with tempfile.TemporaryDirectory(prefix="orqa-storage-test-") as directory:
        path = Path(directory)
        (path / "mtd_functions.inc").write_text(probe + geometry)
        for flag in ([], ["-DCONFIG_MTD_W25"]):
            binary = path / "storage_probe"
            subprocess.run(["g++", "-std=c++14", "-Wall", "-Wextra", "-Werror",
                            "-Wno-unused-parameter", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                            *flag, "-I", str(path), str(ROOT / "tests/storage_probe.cpp"),
                            "-o", str(binary)], check=True)
            subprocess.run([str(binary)], check=True)
    print("PASS: W25 attach success, missing bus/chip/driver, geometry failure and zero-partition initialization")


def check_boards(px4):
    layouts = json.loads((ROOT / "build-config.json").read_text())["boards"]
    for name in ("h7quadcore", "h7wingcore", "apb", "f405pro"):
        board = px4 / "boards/orqa" / name
        config = (board / "nuttx-config/nsh/defconfig").read_text().splitlines()
        for option in ("CONFIG_MTD_W25=y", "CONFIG_BCH=y", "CONFIG_MTD_PARTITION=y",
                       "CONFIG_W25_SPIFREQUENCY=10000000"):
            if option not in config:
                raise RuntimeError("{} lacks {}".format(name, option))
        if "CONFIG_W25_SECTOR512=y" in config:
            raise RuntimeError("W25 partition units changed")
        if name in ("h7quadcore", "h7wingcore"):
            for option in ("CONFIG_STM32H7_SDMMC1=y", "CONFIG_MMCSD=y", "CONFIG_MMCSD_SDIO=y"):
                if option not in config:
                    raise RuntimeError("Incomplete SD support: {} {}".format(name, option))
        elif "CONFIG_MMCSD=y" in config:
            raise RuntimeError("SD enabled on board without a verified SD connection")
        defaults = (board / "init/rc.board_defaults").read_text()
        if "param load $PARAM_FILE" in defaults or "\n\treboot\n" in defaults:
            raise RuntimeError("Automatic legacy SD parameter migration restored")
        header = (board / "src/board_config.h").read_text()
        if not re.search(r'#define RC_SERIAL_PORT\s+"/dev/ttyS0"', header):
            raise RuntimeError("{} has no RCInput startup port".format(name))
        prototype = json.loads((board / "firmware.prototype").read_text())
        layout = layouts[name]
        if prototype["board_id"] != layout["board_id"] or prototype["image_maxsize"] != layout["app_size"]:
            raise RuntimeError("Firmware prototype disagrees with flash layout: " + name)
        if name != "f405pro":
            # Check the bootloader's erase/CRC bounds, not just its own ELF.
            with tempfile.TemporaryDirectory(prefix="orqa-layout-test-") as directory:
                source = Path(directory) / "layout.cpp"
                source.write_text('''
#include "hw_config.h"
static_assert(APP_LOAD_ADDRESS == %du, "application address");
static_assert(BOARD_TYPE == %du, "board ID");
static_assert(BOARD_FLASH_SIZE - 128 * 1024 - APP_RESERVATION_SIZE == %du, "bootloader CRC bounds");
static_assert(BOARD_FLASH_SECTORS * 128 * 1024 == %du, "erase size");
static_assert(0x08000000 + BOARD_FIRST_FLASH_SECTOR_TO_ERASE * 128 * 1024 == APP_LOAD_ADDRESS, "erase start");
''' % (layout["app_origin"], layout["board_id"], layout["app_size"], layout["app_size"]))
                subprocess.run(["g++", "-std=c++14", "-fsyntax-only", "-I", str(board / "src"), str(source)], check=True)
    print("PASS: board storage configuration and parameter preservation")
    print("PASS: RC startup ports, board IDs and H7 bootloader erase/CRC bounds")


def check_manifest(px4):
    # Compile the installed common manifest against PX4's real manifest types.
    # Stub only hardware includes; no device is accessed by this host test.
    with tempfile.TemporaryDirectory(prefix="orqa-manifest-test-") as directory:
        path = Path(directory)
        (path / "nuttx/spi").mkdir(parents=True)
        (path / "nuttx/config.h").write_text("#pragma once\n")
        (path / "board_config.h").write_text(
            '#pragma once\n#include <sys/cdefs.h>\n#define __EXPORT\n')
        (path / "nuttx/spi/spi.h").write_text("#pragma once\n#define SPIDEV_FLASH(n) (n)\n")
        for flag in ([], ["-DFLASH_BASED_PARAMS"]):
            binary = path / "manifest_probe"
            subprocess.run(["g++", "-std=c++14", "-Wall", "-Wextra", "-Werror", *flag,
                            "-I", str(path), "-I", str(px4 / "platforms/common/include"),
                            str(px4 / "boards/orqa/common/mtd.cpp"),
                            str(ROOT / "tests/manifest_probe.cpp"), "-o", str(binary)], check=True)
            subprocess.run([str(binary)], check=True)
    print("PASS: real H7/F405 manifests use SPI NOR and correctly sized, erase-aligned partitions")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("px4", type=Path)
    args = parser.parse_args()
    check_boot(args.px4)
    check_driver(args.px4)
    check_boards(args.px4)
    check_manifest(args.px4)


if __name__ == "__main__":
    main()

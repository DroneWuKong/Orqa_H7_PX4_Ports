import base64
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("install")
firmware = load("check_firmware")


class FirmwareTests(unittest.TestCase):
    def setUp(self):
        self.board = {"board_id": 1204, "app_origin": 0x08060000,
                      "app_size": 1572864, "min_free": 16384}
        self.raw = struct.pack("<II", 0x24001000, 0x08060009) + bytes(56)
        self.bundle = {"magic": "PX4FWv1", "board_id": 1204, "image_maxsize": 1572864, "image_size": len(self.raw),
                       "image": base64.b64encode(zlib.compress(self.raw)).decode()}
        self.elf = bytearray(164)
        self.elf[:7] = b"\x7fELF\x01\x01\x01"
        struct.pack_into("<H", self.elf, 18, 40)
        struct.pack_into("<I", self.elf, 28, 52)
        struct.pack_into("<I", self.elf, 32, 84)
        struct.pack_into("<HH", self.elf, 42, 32, 1)
        struct.pack_into("<HH", self.elf, 46, 40, 2)
        struct.pack_into("<8I", self.elf, 52, 1, 0, 0x08060000, 0x08060000, 64, 64, 5, 32)
        struct.pack_into("<10I", self.elf, 124, 0, 1, 6, 0x08060000, 0, 64, 0, 0, 32, 0)

    def validate(self):
        return firmware.validate(self.bundle, self.raw, self.board, "default", self.elf)

    def test_valid(self):
        self.assertEqual(self.validate()["free_bytes"], 1572800)

    def test_nuttx_initial_stack_low_bits(self):
        self.raw = struct.pack("<II", 0x24001002, 0x08060009) + bytes(56)
        self.bundle["image"] = base64.b64encode(zlib.compress(self.raw)).decode()
        self.validate()

    def test_f405_elf_segment_padding_before_application(self):
        self.board.update(board_id=1155, app_origin=0x0800C000, app_size=999424)
        self.raw = struct.pack("<II", 0x20001002, 0x0800C009) + bytes(56)
        self.bundle.update(board_id=1155, image_maxsize=999424,
                           image=base64.b64encode(zlib.compress(self.raw)).decode())
        self.elf.extend(bytes(0xC040 - len(self.elf)))
        struct.pack_into("<8I", self.elf, 52, 1, 0, 0x08000000, 0x08000000, 0xC040, 0xC040, 5, 0x10000)
        struct.pack_into("<10I", self.elf, 124, 0, 1, 6, 0x0800C000, 0xC000, 64, 0, 0, 32, 0)
        self.assertEqual(self.validate()["load_address"], "0x800c000")

    def test_wrong_board(self):
        self.bundle["board_id"] = 1013
        with self.assertRaisesRegex(ValueError, "board ID"):
            self.validate()

    def test_wrong_package_format(self):
        self.bundle["magic"] = "wrong"
        with self.assertRaisesRegex(ValueError, "package format"):
            self.validate()

    def test_wrong_partition(self):
        self.bundle["image_maxsize"] = 1966080
        with self.assertRaisesRegex(ValueError, "partition"):
            self.validate()

    def test_corrupted_raw(self):
        self.raw += b"corruption"
        with self.assertRaisesRegex(ValueError, "raw binary"):
            self.validate()

    def test_flash_budget(self):
        self.board["min_free"] = 1572864
        with self.assertRaisesRegex(ValueError, "budget"):
            self.validate()

    def test_wrong_link_address(self):
        struct.pack_into("<I", self.elf, 64, 0x08020000)
        with self.assertRaisesRegex(ValueError, "load address"):
            self.validate()

    def test_wrong_reset_vector(self):
        self.raw = struct.pack("<II", 0x24001000, 0x08020009) + bytes(56)
        self.bundle["image"] = base64.b64encode(zlib.compress(self.raw)).decode()
        with self.assertRaisesRegex(ValueError, "Reset vector"):
            self.validate()

    def test_obsolete_startup_parameter(self):
        with tempfile.TemporaryDirectory(prefix="orqa-parameter-test-") as directory:
            path = Path(directory)
            xml = path / "parameters.xml"
            defaults = path / "rc.board_defaults"
            xml.write_text('<parameters><group><parameter name="PWM_MAIN_TIM0"/></group></parameters>')
            defaults.write_text("param set-default PWM_MAIN_TIM0 -4\n")
            firmware.check_defaults(xml, defaults)
            defaults.write_text("param set-default DSHOT_CONFIG 300\n")
            with self.assertRaisesRegex(ValueError, "DSHOT_CONFIG"):
                firmware.check_defaults(xml, defaults)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="orqa-installer-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.px4 = self.base / "px4"
        self.px4.mkdir()
        self.port = self.base / "port"
        (self.port / "boards/orqa/test").mkdir(parents=True)
        (self.port / "patches").mkdir()
        (self.port / "boards/orqa/test/board.h").write_text("new board\n")
        self.git("init", "-q")
        (self.px4 / "core.txt").write_text("before\n")
        self.git("add", "core.txt")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")
        sha = self.git("rev-parse", "HEAD").strip()
        self.git("tag", "fixture")
        (self.port / "build-config.json").write_text(json.dumps({"px4_revision": sha, "px4_version": "fixture"}))
        (self.port / "patches/001.patch").write_text(
            "diff --git a/core.txt b/core.txt\n--- a/core.txt\n+++ b/core.txt\n@@ -1 +1 @@\n-before\n+after\n")
        self.root_patch = patch.object(installer, "ROOT", self.port)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.px4), *args], text=True)

    def test_install_and_repeat(self):
        installer.install(self.px4)
        installer.install(self.px4)
        self.assertEqual((self.px4 / "core.txt").read_text(), "after\n")

    def test_managed_update_removes_stale_file(self):
        installer.install(self.px4)
        (self.port / "boards/orqa/test/board.h").unlink()
        (self.port / "boards/orqa/test/new.h").write_text("updated\n")
        installer.install(self.px4)
        self.assertFalse((self.px4 / "boards/orqa/test/board.h").exists())

    def test_local_board_edit_is_preserved(self):
        installer.install(self.px4)
        local = self.px4 / "boards/orqa/test/board.h"
        local.write_text("user edit\n")
        with self.assertRaisesRegex(ValueError, "local board changes"):
            installer.install(self.px4)
        self.assertEqual(local.read_text(), "user edit\n")

    def test_generated_bootloader_preserved_on_repeat_install(self):
        (self.port / "boards/orqa/test/bootloader.px4board").write_text("bootloader fixture\n")
        installer.install(self.px4)
        target = "orqa_test_bootloader"
        build = self.px4 / "build" / target
        build.mkdir(parents=True)
        (build / (target + ".bin")).write_bytes(b"built bootloader")
        extras = self.px4 / "boards/orqa/test/extras"
        extras.mkdir()
        output = extras / (target + ".bin")
        output.write_bytes(b"built bootloader")
        installer.install(self.px4)
        self.assertEqual(output.read_bytes(), b"built bootloader")
        output.write_bytes(b"locally edited bootloader")
        with self.assertRaisesRegex(ValueError, "local board changes"):
            installer.install(self.px4)
        self.assertEqual(output.read_bytes(), b"locally edited bootloader")

    def test_patch_conflict_changes_nothing(self):
        (self.px4 / "core.txt").write_text("user edit\n")
        with self.assertRaisesRegex(ValueError, "conflicts"):
            installer.install(self.px4)
        self.assertFalse((self.px4 / "boards/orqa").exists())
        self.assertEqual((self.px4 / "core.txt").read_text(), "user edit\n")

    def test_wrong_revision(self):
        (self.port / "build-config.json").write_text(json.dumps({"px4_revision": "wrong", "px4_version": "fixture"}))
        with self.assertRaisesRegex(ValueError, "must be at"):
            installer.install(self.px4)
        self.assertEqual((self.px4 / "core.txt").read_text(), "before\n")

    def test_symlink_is_refused(self):
        (self.px4 / "boards").mkdir()
        (self.px4 / "boards/orqa").symlink_to(self.port / "boards/orqa", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            installer.install(self.px4)


if __name__ == "__main__":
    unittest.main()

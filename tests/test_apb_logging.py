import importlib.util
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "companion/apb" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rec = load("recorder")
mount = load("mount_sd")
installer = load("install")

budget_spec = importlib.util.spec_from_file_location("budget", ROOT / "scripts/check_apb_logging.py")
budget = importlib.util.module_from_spec(budget_spec)
budget_spec.loader.exec_module(budget)


class ProfileTests(unittest.TestCase):
    def test_generated_size_counts_padding_conservatively(self):
        header = "struct __EXPORT sample_s {\nuint64_t timestamp;\nfloat data[3];\nuint8_t _padding0[4];\n#ifdef __cplusplus\n"
        self.assertEqual(budget.topic_size(header, "sample"), 24)

    def test_unknown_field_fails_closed(self):
        with self.assertRaises(ValueError):
            budget.topic_size("struct __EXPORT sample_s {\nunknown_t data;\n#ifdef __cplusplus", "sample")

    def test_apb_backend_and_sd_guard(self):
        defaults = (ROOT / "boards/orqa/apb/init/rc.board_defaults").read_text()
        self.assertIn('set LOGGER_ARGS "-m mavlink"', defaults)
        self.assertNotIn("param set SDLOG_MODE", defaults)
        header = (ROOT / "boards/orqa/apb/nuttx-config/include/board.h").read_text()
        self.assertIn('#  error "APB microSD is companion-owned', header)
        self.assertNotIn("#define GPIO_SDMMC2", header)


class RecorderTests(unittest.TestCase):
    def test_mount_not_directory(self):
        with self.assertRaises(rec.NotReady):
            rec.mount_record("1 0 8:1 / / rw - ext4 /dev/sda1 rw\n", Path("/sdcard"))

    def test_mount_escape_and_identity(self):
        line = "42 1 179:1 / /sd\\040card rw - vfat /dev/mmcblk1p1 rw\n"
        self.assertEqual(rec.mount_record(line, Path("/sd card")), ("42", "179:1"))

    def test_readonly_mount(self):
        for options in ("ro - vfat /dev/mmcblk1p1 rw", "rw - vfat /dev/mmcblk1p1 ro"):
            with self.assertRaises(rec.NotReady):
                rec.mount_record("42 1 179:1 / /sdcard " + options, Path("/sdcard"))

    def test_root_and_emmc_rejected(self):
        with self.assertRaises(rec.NotReady):
            rec.card_identity(Path("/tmp"))
        with patch.object(rec, "mount_record", return_value=("1", "8:1")), \
             patch.object(Path, "read_text", side_effect=["mountinfo", "MMC"]), \
             patch.object(Path, "resolve", side_effect=lambda **_: Path("/sdcard")):
            with self.assertRaises(rec.NotReady):
                rec.card_identity(Path("/sdcard"))

    def test_space_and_readonly(self):
        for flags, available in ((os.ST_RDONLY, 1000), (0, 0)):
            fs = Mock(f_flag=flags, f_bavail=available, f_frsize=4096)
            with patch.object(os, "fstatvfs", return_value=fs), self.assertRaises(rec.NotReady):
                rec.check_space(1, 4096)

    def test_pinned_directory_and_no_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            dev = path.stat().st_dev
            ident = ("42", "{}:{}".format(os.major(dev), os.minor(dev)))
            with patch.object(rec, "card_identity", return_value=ident):
                fd, _ = rec.open_card(path, 1)
                try:
                    path.rename(path.with_name(path.name + "-moved"))
                    path.mkdir()
                    self.assertNotEqual(os.fstat(fd).st_ino, path.stat().st_ino)
                    self.assertIn("Log=/proc/self/fd/{}".format(fd), rec.configuration(fd, 14560, 1))
                finally:
                    os.close(fd)
                    moved = path.with_name(path.name + "-moved")
                    (moved / "px4").rmdir()
                    moved.rmdir()
                (path / "px4").symlink_to("/tmp", target_is_directory=True)
                with self.assertRaises(OSError):
                    rec.open_card(path, 1)

    def test_mount_changed_during_open(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            dev = path.stat().st_dev
            ident = ("42", "{}:{}".format(os.major(dev), os.minor(dev)))
            with patch.object(rec, "card_identity", side_effect=[ident, ("43", ident[1])]):
                with self.assertRaises(rec.NotReady):
                    rec.open_card(path, 1)

    def test_config_cannot_touch_uart_or_delete_logs(self):
        text = rec.configuration(9, 14560, 1)
        self.assertIn("Address=127.0.0.1", text)
        self.assertIn("MinFreeSpace=0\nMaxLogFiles=0", text)
        self.assertNotIn("UartEndpoint", text)
        self.assertIn("LogSystemId=1", text)

    def test_write_error_signals_restart(self):
        import io
        failed = threading.Event()
        rec.watch_output(io.StringIO("Unable to write to ULog file: No space left\n"), failed)
        self.assertTrue(failed.is_set())

    def test_stuck_recorder_is_killed_before_retry(self):
        import subprocess
        child = Mock()
        child.poll.return_value = None
        child.wait.side_effect = [subprocess.TimeoutExpired("recorder", 5), 0]
        rec.stop_child(child)
        child.terminate.assert_called_once()
        child.kill.assert_called_once()
        self.assertEqual(child.wait.call_count, 2)


class MountTests(unittest.TestCase):
    def test_reject_device_injection(self):
        with self.assertRaises(ValueError):
            mount.handle("sda1-mount; rm")

    def test_emmc_never_mounted(self):
        with patch.object(mount, "current_source", return_value=""), \
             patch.object(Path, "read_text", return_value="MMC\n"), \
             patch.object(mount.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                mount.handle("mmcblk0p1-mount")
            run.assert_not_called()

    def test_unmount_only_matching_device(self):
        with patch.object(mount, "current_source", return_value="/dev/mmcblk1p1"), \
             patch.object(mount.subprocess, "run") as run:
            mount.handle("mmcblk0p1-unmount")
            run.assert_not_called()
            mount.handle("mmcblk1p1-unmount")
            self.assertEqual(run.call_args[0][0], ["systemd-umount", "--collect", "/sdcard"])

    def test_mount_waits_and_checks_result(self):
        with patch.object(mount, "current_source", side_effect=["", "/dev/mmcblk1p1"]), \
             patch.object(Path, "read_text", return_value="SD\n"), \
             patch.object(Path, "is_symlink", return_value=False), \
             patch.object(Path, "mkdir"), patch.object(mount.subprocess, "run") as run:
            mount.handle("mmcblk1p1-mount")
            self.assertNotIn("--no-block", run.call_args[0][0])
            self.assertTrue(run.call_args[1]["check"])

    def test_mount_failure_cannot_mark_success(self):
        with patch.object(mount, "current_source", side_effect=["", ""]), \
             patch.object(Path, "read_text", return_value="SD\n"), \
             patch.object(Path, "is_symlink", return_value=False), \
             patch.object(Path, "mkdir"), patch.object(mount.subprocess, "run"):
            with self.assertRaises(RuntimeError):
                mount.handle("mmcblk1p1-mount")


class InstallTests(unittest.TestCase):
    def test_unknown_vendor_helper_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / installer.FILES["orqa-drive-mounting.sh"]
            target.parent.mkdir(parents=True)
            target.write_text("custom vendor helper")
            with self.assertRaises(ValueError):
                installer.install(root, ROOT / "companion/apb")
            self.assertEqual(target.read_text(), "custom vendor helper")
            self.assertFalse((root / "usr/local/lib/orqa-px4").exists())

    def test_install_preserves_backup_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / installer.FILES["orqa-drive-mounting.sh"]
            target.parent.mkdir(parents=True)
            target.write_text("fixture vendor helper")
            with patch.object(installer, "VENDOR_HASH", installer.digest(target)):
                installer.install(root, ROOT / "companion/apb")
                installer.install(root, ROOT / "companion/apb")
            self.assertEqual(target.with_name(target.name + ".pre-px4-logging").read_text(), "fixture vendor helper")
            self.assertEqual(target.read_bytes(), (ROOT / "companion/apb/orqa-drive-mounting.sh").read_bytes())


if __name__ == "__main__":
    unittest.main()

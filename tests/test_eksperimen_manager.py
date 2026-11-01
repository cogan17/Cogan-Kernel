#!/usr/bin/env python3
"""Offline tests for the experiment ZIP (owner 2026-11-01): the manager rides in the kernel ZIP and is
updated at boot through ksud, only when that manager is already installed."""
import os
import re
import struct
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from kernel.scripts import apk_package

ROOT = Path(__file__).resolve().parents[1]
AK = ROOT / "kernel/anykernel"


def manifest(package, utf8=True):
    """A minimal binary AndroidManifest.xml: <manifest package="...">."""
    names = ["manifest", "package", package]
    blob, offsets = b"", []
    for name in names:
        offsets.append(len(blob))
        if utf8:
            raw = name.encode()
            blob += bytes([len(name), len(raw)]) + raw + b"\0"
        else:
            blob += struct.pack("<H", len(name)) + name.encode("utf-16-le") + b"\0\0"
    blob += b"\0" * (-len(blob) % 4)
    start = 28 + 4 * len(names)
    pool = struct.pack("<HHIIIIII", 0x0001, 28, start + len(blob), len(names), 0, 0x100 if utf8 else 0, start, 0)
    pool += struct.pack(f"<{len(names)}I", *offsets) + blob
    attribute = struct.pack("<IIIHBBI", 0xFFFFFFFF, 1, 2, 8, 0, 3, 2)
    element = struct.pack("<HHIIIIIHHHHHH", 0x0102, 16, 36 + len(attribute), 1, 0xFFFFFFFF, 0xFFFFFFFF, 0,
                          20, 20, 1, 0, 0, 0) + attribute
    body = pool + element
    return struct.pack("<HHI", 0x0003, 8, 8 + len(body)) + body


class ApkPackageTest(unittest.TestCase):
    def test_package_name_is_read_from_the_binary_manifest(self):
        for utf8 in (True, False):
            self.assertEqual(apk_package.package(manifest("com.resukisu.resukisu", utf8)), "com.resukisu.resukisu")

    def test_cli_reads_an_apk_and_fails_on_a_broken_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            apk = Path(tmp, "m.apk")
            with zipfile.ZipFile(apk, "w") as out:
                out.writestr("AndroidManifest.xml", manifest("com.rifsxd.ksunext"))
            self.assertEqual(apk_package.main([str(apk)]), 0)
            with zipfile.ZipFile(apk, "w") as out:
                out.writestr("AndroidManifest.xml", b"<manifest/>")
            self.assertEqual(apk_package.main([str(apk)]), 1)


class ExperimentScriptsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.adb, self.ak, self.bin = self.root / "adb", self.root / "ak", self.root / "bin"
        for path in (self.adb, self.ak / "cogan", self.bin):
            path.mkdir(parents=True)
        (self.ak / "cogan/manager.apk").write_bytes(b"apk" * 100)
        (self.ak / "cogan/package").write_text("com.rifsxd.ksunext\n")
        for name in ("eksperimen-manager.sh", "cogan-manager-boot.sh"):
            (self.ak / "cogan" / name).write_text((AK / name).read_text())
        # pm: "installed" lists the installed packages; install records the streamed size.
        (self.bin / "pm").write_text('#!/bin/sh\nif [ "$1" = path ]; then grep -qx "$2" "$INSTALLED"; exit; fi\n'
                                     'echo "$*" > "$PM_CALL"; wc -c > "$PM_BYTES"; echo Success\n')
        (self.bin / "pm").chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}", COGAN_ADB=str(self.adb), AKHOME=str(self.ak),
                        INSTALLED=str(self.root / "installed"), PM_CALL=str(self.root / "call"),
                        PM_BYTES=str(self.root / "bytes"))
        (self.root / "installed").write_text("com.rifsxd.ksunext\n")

    def tearDown(self):
        self.tmp.cleanup()

    def flash(self):
        script = 'ui_print() { for line in "$@"; do echo "$line"; done; }\n. "$AKHOME/cogan/eksperimen-manager.sh"\n'
        return subprocess.run(["sh", "-c", script], env=self.env, capture_output=True, text=True, check=True).stdout

    def boot(self):
        script = self.adb / "boot-completed.d/cogan-manager.sh"
        subprocess.run(["sh", str(script)], env=self.env, check=True)
        return (self.adb / "cogan-manager/log.txt").read_text()

    def test_flash_stages_and_boot_updates_the_installed_manager_once(self):
        (self.adb / "ksud").write_text("ksud")
        self.assertIn("manager com.rifsxd.ksunext diperbarui saat HP menyala", self.flash())
        self.assertEqual((self.adb / "cogan-manager/package").read_text().strip(), "com.rifsxd.ksunext")
        log = self.boot()
        self.assertIn("pm install exit: 0", log)
        self.assertEqual((self.root / "call").read_text().split(), ["install", "-r", "-S", "300"])
        self.assertEqual((self.root / "bytes").read_text().strip(), "300")
        self.assertFalse((self.adb / "boot-completed.d/cogan-manager.sh").exists())  # runs once
        self.assertFalse((self.adb / "cogan-manager/manager.apk").exists())

    def test_a_manager_that_is_not_installed_is_left_alone(self):
        # e.g. only the spoofed manager (another package name): no second manager appears.
        (self.adb / "ksud").write_text("ksud")
        (self.root / "installed").write_text("fafooh.wnrldn.vxwjsm\n")
        self.flash()
        self.assertIn("skip: com.rifsxd.ksunext not installed", self.boot())
        self.assertFalse((self.root / "call").exists())
        self.assertFalse((self.adb / "boot-completed.d/cogan-manager.sh").exists())

    def test_without_ksud_or_data_nothing_is_written(self):
        self.assertIn("pasang APK manager dari Android", self.flash())
        self.assertEqual(list(self.adb.iterdir()), [])

    def test_build_adds_the_hook_before_the_end_of_the_install(self):
        build = (ROOT / "kernel/build.sh").read_text()
        command = re.search(r"sed -i ('s\|\^## end boot install\$\|.*?\|')", build)[1]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp, "anykernel.sh")
            target.write_text((AK / "anykernel.sh").read_text())
            subprocess.run(["sh", "-c", f"sed -i {command} {target}"], check=True)
            lines = target.read_text().splitlines()
        self.assertEqual(lines[-2:], [". $AKHOME/cogan/eksperimen-manager.sh; # Eksperimen: manager via TWRP",
                                      "## end boot install"])
        self.assertEqual(lines[-3], "flash_boot;")


if __name__ == "__main__":
    unittest.main()

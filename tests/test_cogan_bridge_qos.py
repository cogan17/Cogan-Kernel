#!/usr/bin/env python3
"""Cogan Bridge's CPU limit watchdog, run in user space against a mock kernel API (audit 2026-11-18, T4).

kernel/patches/cogan_bridge.c is compiled as it is with tests/fixtures/cogan_bridge_mock: a frequency QoS
update that fails once, or keeps failing, must not leave the bridge's lower limit behind once the TTL is over."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOCK = ROOT / "tests/fixtures/cogan_bridge_mock"
HEADERS = ("capability", "cpu", "cpufreq", "init", "kernel", "kobject", "ktime", "list", "mutex", "of",
           "pm_qos", "slab", "sysfs", "utsname", "workqueue")


@unittest.skipUnless(shutil.which("cc"), "no C compiler")
class CoganBridgeQosTests(unittest.TestCase):
    def test_failed_release_is_retried_and_bounded(self):
        with tempfile.TemporaryDirectory() as temp:
            include = Path(temp) / "include"
            for name in HEADERS:
                (include / "linux").mkdir(parents=True, exist_ok=True)
                (include / "linux" / f"{name}.h").write_text(f'#include "{MOCK / "kmock.h"}"\n')
            (include / "generated").mkdir()
            (include / "generated/utsrelease.h").write_text('#define UTS_RELEASE "6.1.0-mock"\n')
            binary = Path(temp) / "harness"
            subprocess.run(["cc", "-std=gnu11", "-Wall", "-Werror", "-Wno-unused-function", "-Wno-unused-variable",
                            "-I", str(include), "-I", str(ROOT / "kernel/patches"), str(MOCK / "harness.c"),
                            "-o", str(binary)], check=True, capture_output=True, text=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "OK\n")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline tests for install_cogan_bridge.py: an additive, repeatable driver overlay."""
import re
import tempfile
import unittest
from pathlib import Path

from kernel.scripts import install_cogan_bridge as bridge

ROOT = Path(__file__).resolve().parents[1]


def source(tmp):
    misc = Path(tmp) / "drivers/misc"
    misc.mkdir(parents=True)
    for name in ("Makefile", "Kconfig"):
        (misc / name).write_text("# upstream\n")
    return Path(tmp), misc


class InstallTests(unittest.TestCase):
    def test_repeatable_and_rejects_a_foreign_bridge(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, misc = source(tmp)
            bridge.install(src, "rothko")
            first = {name: (misc / name).read_bytes() for name in ("Makefile", "Kconfig", "cogan_bridge.c")}
            bridge.install(src, "rothko")
            self.assertEqual(first, {name: (misc / name).read_bytes() for name in first})
            (misc / "cogan_bridge.c").write_text("unreviewed\n")
            with self.assertRaises(ValueError):
                bridge.install(src, "rothko")

    def test_device_codename_is_compiled_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, misc = source(tmp)
            bridge.install(src, "rothko")
            self.assertIn("CFLAGS_cogan_bridge.o += -DCOGAN_BRIDGE_DEVICE='\"rothko\"'", (misc / "Makefile").read_text())
            self.assertIn("config COGAN_BRIDGE", (misc / "Kconfig").read_text())

    def test_generic_build_has_no_device(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, misc = source(tmp)
            bridge.install(src, "generic")
            self.assertNotIn("COGAN_BRIDGE_DEVICE", (misc / "Makefile").read_text())

    def test_unsafe_codename_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, misc = source(tmp)
            for bad in ("Rothko", "rothko'; rm -rf /", "a" * 33):
                with self.assertRaises(ValueError):
                    bridge.install(src, bad)
            self.assertFalse((misc / "cogan_bridge.c").exists())


class DriverSourceTests(unittest.TestCase):
    def test_abi_1_attributes_including_device_and_soc(self):
        text = (ROOT / "kernel/patches/cogan_bridge.c").read_text()
        attrs = re.findall(r"__ATTR\((\w+), (0[46]00)", text)
        self.assertEqual(dict(attrs), {"abi": "0400", "release": "0400", "banner": "0400", "features": "0400",
                                       "device": "0400", "soc": "0400", "limits": "0600", "policies": "0400",
                                       "power_client": "0600", "thermal_client": "0600"})
        self.assertNotIn("EXPORT_SYMBOL", text)   # nothing new in the KMI


if __name__ == "__main__":
    unittest.main()

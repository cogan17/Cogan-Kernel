#!/usr/bin/env python3
"""Kernel identity disguise (owner 2026-11-01), off by default: when on, uname and /proc/version show what
the phone's own stock kernel shows (kernel/configs/stock-identity.env, read from the owner's stock
boot.img), with the real 6.1.N version and the real ACK commit. Display only; the ZIP name, build.env and
the KMI gate keep the real identity."""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
BUILD = (ROOT / "kernel/build.sh").read_text()
# The identity decision block: from CC_TEXT="" up to (not including) the scripts/config call.
BLOCK = re.search(r'^CC_TEXT=""\n.*?(?=^scripts/config )', BUILD, re.S | re.M)[0]
MKCOMPILE = (ROOT / "tests/fixtures/mkcompile_h-6.1.176").read_text()  # Linux 6.1.176, unchanged
ACK = "6d8630162a371a04152cf5778f8a5b90e49f30a6"  # ACK android14-6.1-2026-09_r5
STOCK_CC = ("Android (10087095, +pgo, +bolt, +lto, -mlgo, based on r487747c) clang version 17.0.2 "
            "(https://android.googlesource.com/toolchain/llvm-project d9f89f4d16663d5012e5c09495f3b30ece3d2362)")


def decide(disguise, mkcompile=MKCOMPILE):
    """Run the block in a throwaway kernel-like tree; return its variables and the generated compile.h."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", tmp], check=True)
        Path(tmp, "build.config.common").write_text("KMI_GENERATION=11\n")
        Path(tmp, "scripts").mkdir()
        Path(tmp, "scripts/mkcompile_h").write_text(mkcompile)
        for args in (["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
            subprocess.run(["git", "-C", tmp, *args], check=True)
        script = ('set -euo pipefail\nlog() { echo "[+] $*" >&2; }\nfail() { echo "FAIL $*"; exit 1; }\n'
                  f'DISGUISE={disguise}\nNAME=Cogan-Rothko-ACK\nREVISION=r16\nSUBLEVEL=176\nACK_COMMIT={ACK}\n'
                  f'HERE={ROOT / "kernel"}\n' + BLOCK +
                  '\nexport KBUILD_BUILD_USER="$BUILD_USER" KBUILD_BUILD_HOST="$BUILD_HOST"'
                  '\nprintf "%s\\n%s\\n%s\\n%s\\n" "$LOCALVERSION" "$BUILD_USER" "$BUILD_HOST" "$CC_TEXT"'
                  '\nsh scripts/mkcompile_h arm64 "${CC_TEXT:-Neutron clang version 24.0.0git}" true')
        result = subprocess.run(["bash", "-c", script], cwd=tmp, capture_output=True, text=True,
                                env={"PATH": os.environ["PATH"]})
    if result.returncode:
        return {"error": result.stdout + result.stderr}
    lines = result.stdout.splitlines()
    return {"local": lines[0], "user": lines[1], "host": lines[2], "cc": lines[3], "compile_h": "\n".join(lines[4:])}


class DisguiseTest(unittest.TestCase):
    def test_off_keeps_the_cogan_identity(self):
        off = decide("false")
        self.assertRegex(off["local"], r"^-Cogan-Rothko-ACK-r16-[0-9a-f]{9}$")
        self.assertEqual((off["user"], off["host"], off["cc"]), ("cogan17", "github-actions", ""))
        self.assertIn('#define LINUX_COMPILE_BY\t"cogan17"', off["compile_h"])

    def test_on_shows_what_the_stock_kernel_shows(self):
        on = decide("true")
        self.assertEqual(on["local"], f"-android14-11-g{ACK[:12]}-ab{int(ACK[:7], 16) % 100000000:08d}")
        self.assertEqual((on["user"], on["host"], on["cc"]), ("build-user", "build-host", STOCK_CC))
        # The /proc/version parts exactly as in the stock banner, LLD included.
        self.assertIn('#define LINUX_COMPILE_BY\t"build-user"', on["compile_h"])
        self.assertIn('#define LINUX_COMPILE_HOST\t"build-host"', on["compile_h"])
        self.assertIn(f'#define LINUX_COMPILER\t\t"{STOCK_CC}, LLD 17.0.2"', on["compile_h"])

    def test_an_unexpected_mkcompile_h_stops_the_build(self):
        result = decide("true", mkcompile="#!/bin/sh\necho changed\n")
        self.assertIn("FAIL Disguise: unexpected scripts/mkcompile_h", result["error"])

    def test_compiler_string_is_overridden_only_when_disguising(self):
        # The make variable wins over the Kconfig default, so olddefconfig keeps it.
        self.assertIn('[ -z "$CC_TEXT" ] || MAKE+=(CC_VERSION_TEXT="$CC_TEXT")', BUILD)

    def test_build_env_records_the_disguise_state(self):
        self.assertIn('echo "DISGUISE=$([ "${DISGUISE:-false}" = "true" ] && echo on || echo off)"', BUILD)

    @unittest.skipUnless(yaml, "PyYAML")
    def test_form_box_is_off_by_default(self):
        wf = yaml.safe_load((ROOT / ".github/workflows/build-kernel.yml").read_text())
        box = wf[True]["workflow_dispatch"]["inputs"]["use_disguise"]
        self.assertIs(box["default"], False)
        self.assertEqual(box["type"], "boolean")


if __name__ == "__main__":
    unittest.main()

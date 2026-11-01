#!/usr/bin/env python3
"""Kernel identity disguise (owner 2026-11-01), off by default: when on, uname/proc-version use the
stock GKI format and a generic AOSP build identity instead of the Cogan name. Display only; the ZIP
name, build.env and the KMI gate keep the real identity."""
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


def decide(disguise):
    """Run the block in a throwaway git repo and return the chosen identity variables."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", tmp], check=True)
        Path(tmp, "build.config.common").write_text("KMI_GENERATION=11\n")
        Path(tmp, "x").write_text("x")
        for args in (["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
            subprocess.run(["git", "-C", tmp, *args], check=True)
        script = (f'set -euo pipefail\nDISGUISE={disguise}\nNAME=Cogan-Rothko-ACK\nREVISION=r16\n'
                  + BLOCK + '\nprintf "%s\\n%s\\n%s\\n%s\\n" "$LOCALVERSION" "$BUILD_USER" "$BUILD_HOST" "$CC_TEXT"')
        out = subprocess.run(["bash", "-c", script], cwd=tmp, capture_output=True, text=True, check=True).stdout
    local, user, host, cc = out.splitlines()[:4]
    return {"local": local, "user": user, "host": host, "cc": cc}


class DisguiseTest(unittest.TestCase):
    def test_off_keeps_the_cogan_identity(self):
        off = decide("false")
        self.assertRegex(off["local"], r"^-Cogan-Rothko-ACK-r16-[0-9a-f]{9}$")
        self.assertEqual((off["user"], off["host"], off["cc"]), ("cogan17", "github-actions", ""))

    def test_on_uses_the_stock_gki_format(self):
        on = decide("true")
        self.assertRegex(on["local"], r"^-android14-11-g[0-9a-f]{12}-ab[0-9]{8}$")
        self.assertNotIn("Cogan", on["local"])
        self.assertEqual((on["user"], on["host"]), ("android-build", "abfarm"))
        self.assertRegex(on["cc"], r"^Android \(.*\) clang version ")

    def test_compiler_string_is_overridden_only_when_disguising(self):
        # The make variable wins over the Kconfig default, so olddefconfig keeps it.
        self.assertIn('[ -z "$CC_TEXT" ] || MAKE+=(CC_VERSION_TEXT="$CC_TEXT")', BUILD)

    def test_build_env_records_the_disguise_state(self):
        self.assertIn('echo "DISGUISE=$([ "${DISGUISE:-false}" = "true" ] && echo on || echo off)"', BUILD)

    @unittest.skipUnless(yaml, "PyYAML")
    def test_form_box_is_off_by_default(self):
        wf = yaml.safe_load((ROOT / ".github/workflows/build-kernel.yml").read_text())
        box = (wf[True]["workflow_dispatch"]["inputs"]["use_disguise"])
        self.assertIs(box["default"], False)
        self.assertEqual(box["type"], "boolean")


if __name__ == "__main__":
    unittest.main()

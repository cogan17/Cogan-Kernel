#!/usr/bin/env python3
"""Builder box Force-load (audit r21 T1): off by default since r67 passed the phone test (owner 2026-11-19)."""
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
BUILD = (ROOT / "kernel/build.sh").read_text()
WORKFLOW = ROOT / ".github/workflows/build-kernel.yml"


class ForceLoadBoxTests(unittest.TestCase):
    @unittest.skipUnless(yaml, "PyYAML")
    def test_box_is_off_by_default_and_reaches_build_sh(self):
        wf = yaml.safe_load(WORKFLOW.read_text())
        box = wf[True]["workflow_dispatch"]["inputs"]["use_force_load"]
        self.assertIs(box["default"], False)
        self.assertEqual(box["type"], "boolean")
        self.assertIn("FORCE_LOAD: ${{ inputs.use_force_load }}", WORKFLOW.read_text())

    def test_patch_only_with_the_box_and_the_gate_checks_the_choice(self):
        block = BUILD.split('if [ "${FORCE_LOAD:-false}" = "true" ]; then', 1)[1].split("fi\n", 1)[0]
        self.assertIn('apply "$HERE/patches/force-load-modules.patch"', block)
        self.assertEqual(BUILD.count('apply "$HERE/patches/force-load-modules.patch"'), 1)
        self.assertIn('--force-load "$([ "${FORCE_LOAD:-false}" = "true" ] && echo on || echo off)"', BUILD)
        self.assertIn('echo "FORCE_LOAD=$([ "${FORCE_LOAD:-false}" = "true" ] && echo on || echo off)"', BUILD)
        # Protected exports go either way: our kernel does not trust Google's key.
        after = BUILD.split('if [ "${FORCE_LOAD:-false}" = "true" ]; then', 1)[1].split("fi\n", 1)[1]
        self.assertTrue(after.startswith('rm -f "$KSRC"/android/*protected_exports*'), after[:80])


if __name__ == "__main__":
    unittest.main()

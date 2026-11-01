#!/usr/bin/env python3
"""The SUSFS box of the Builder (owner 2026-11-02): ticked by default; unticked builds the plain root
manager without SUSFS and without sidex15's module, and such a build may be released."""
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from kernel import resolve as r
from kernel import telegram as tg

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
BUILD = (ROOT / "kernel/build.sh").read_text()
SNAP_FN = re.search(r"^snap\(\) \{.*?print\(d\)' \"\$SNAPSHOT\" \"\$1\"; \}$", BUILD, re.S | re.M)[0]
VARIANT_BLOCK = re.search(r'^ROOT="\$\(snap root\)"\n.*?^\[ "\$SUSFS_ON" = true \] && VARIANT="\$VARIANT\+SuSFS"$',
                          BUILD, re.S | re.M)[0]


def variant(snapshot):
    """VARIANT and SUSFS_ON that build.sh derives from a snapshot."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp, "snap.json")
        path.write_text(json.dumps(snapshot))
        script = (f'set -euo pipefail\nfail() {{ echo "FAIL $*"; exit 1; }}\nSNAPSHOT={path}\n{SNAP_FN}\n'
                  f'{VARIANT_BLOCK}\necho "$VARIANT $SUSFS_ON $ROOT_NAME"')
        return subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True).stdout.strip()


class SusfsBoxTest(unittest.TestCase):
    def test_build_names_the_variant_after_the_box(self):
        susfs = {"susfs": {"commit": "a" * 40}}
        self.assertEqual(variant({"root": "KSUN", **susfs}), "KernelSU-Next+SuSFS true KernelSU Next")
        self.assertEqual(variant({"root": "BSU", **susfs}), "BakaSU+SuSFS true BakaSU")
        self.assertEqual(variant({"root": "KSUN"}), "KernelSU-Next false KernelSU Next")
        self.assertEqual(variant({"root": "BSU"}), "BakaSU false BakaSU")

    def test_build_skips_susfs_and_records_it_when_unticked(self):
        self.assertIn('if [ "$SUSFS_ON" = true ]; then\ngroup "SUSFS', BUILD)
        self.assertIn('[ "$SUSFS_ON" = true ] && cat "$HERE/configs/susfs.config"', BUILD)
        self.assertIn('[ "$SUSFS_ON" = true ] && required+=(CONFIG_KSU_SUSFS=y CONFIG_KSU_SUSFS_SUS_MAP=y)', BUILD)
        self.assertIn('fail "SUSFS unticked but CONFIG_KSU_SUSFS=y"', BUILD)
        self.assertIn('echo "SUSFS_COMMIT=$([ "$SUSFS_ON" = true ] && snap susfs.commit || echo -)"', BUILD)

    def test_resolver_flag_turns_susfs_off(self):
        seen = {}

        def fake(root, sublevel, work, unicode=False, susfs_box=True):
            seen["susfs_box"] = susfs_box
            return {"root": root}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(r, "resolve", fake):
            r.main(["--root", "BSU", "--no-susfs", "--out", str(Path(tmp, "s.json"))])
            self.assertIs(seen["susfs_box"], False)
            r.main(["--root", "BSU", "--out", str(Path(tmp, "s.json"))])
            self.assertIs(seen["susfs_box"], True)

    def test_unticked_resolve_takes_bakasu_release_without_susfs(self):
        calls = []

        def ls_remote(url, *patterns):
            calls.append(url)
            if url == r.ACK:
                return {}
            if url == r.BAKASU:
                return {"refs/tags/v1.2.3": "b" * 40}
            if url == r.NOMOUNT:
                return {"refs/tags/v2.2.0": "c" * 40}
            if url == r.BBG:
                return {"refs/heads/main": "d" * 40}
            return {"HEAD": "e" * 40, "refs/heads/arm64-tools": "f" * 40}

        def api(path):
            if "Baka-SU" in path:
                return {"assets": [{"name": "BakaSU_v1.2.3-arm64.apk", "browser_download_url": "https://x/m.apk"}]}
            if "nomount" in path:
                return {"assets": [{"name": "nomount.zip", "browser_download_url": "https://x/n.zip"}]}
            return {"tag_name": "06092026"}
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.multiple(r, ls_remote=ls_remote, api=api, run=lambda *a, **k: "",
                                    ack_releases=lambda refs: [], pick_ack=lambda releases, wanted: [],
                                    bakasu_ready=mock.Mock(side_effect=AssertionError("no SUSFS check")),
                                    susfs_sidex=mock.Mock(side_effect=AssertionError("no sidex15 module"))):
            snap = r.resolve("BSU", "lts", tmp, susfs_box=False)
        self.assertNotIn("susfs", snap)
        self.assertNotIn("susfs_sidex", snap)
        self.assertEqual(snap["root_source"], {"repo": r.BAKASU, "tag": "v1.2.3", "commit": "b" * 40})
        self.assertNotIn(r.SUSFS, calls)

    def test_telegram_names_a_build_without_susfs(self):
        env = {"RELEASE": "v26.11.02-r18", "LINUX_VERSION": "6.1.176", "ROOT_NAME": "BakaSU",
               "SUSFS_VERSION": "-", "SUSFS_COMMIT": "-", "FEATURES": "NoMount"}
        self.assertIn("📦 v26.11.02-r18 · ACK 6.1.176 · BakaSU · tanpa SUSFS", tg.post(env, "id"))
        self.assertIn("· BakaSU · without SUSFS", tg.post(env, "en"))
        # A previous release with SUSFS: no "SUSFS updated" line, the feature list says it was dropped.
        prev = {"tag": "v26.10.31-r7", "susfs": ("v2.3.0", "ee155a1ad421"), "features": "SUSFS, NoMount"}
        self.assertEqual(tg.whats_new(env, prev, "id"), ["Fitur dilepas: SUSFS"])

    @unittest.skipUnless(yaml, "PyYAML")
    def test_form_box_is_ticked_by_default_and_wired(self):
        wf = yaml.safe_load((ROOT / ".github/workflows/build-kernel.yml").read_text())
        box = wf[True]["workflow_dispatch"]["inputs"]["use_susfs"]
        self.assertIs(box["default"], True)
        self.assertEqual(box["type"], "boolean")
        self.assertEqual(wf["jobs"]["susfs"]["if"], "${{ inputs.use_susfs }}")
        self.assertIn("needs.susfs.result == 'skipped' && !inputs.use_susfs", wf["jobs"]["release"]["if"])
        plan = next(s["run"] for s in wf["jobs"]["resolve"]["steps"] if s.get("id") == "plan")
        self.assertIn('[ "$USE_SUSFS" = "true" ] || extra+=(--no-susfs)', plan)


if __name__ == "__main__":
    unittest.main()

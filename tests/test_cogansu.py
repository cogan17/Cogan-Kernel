#!/usr/bin/env python3
"""CoganSU (owner 2026-11-04, cogan17/CoganSU, "dibuat khusus untuk cogan kernel"): KernelSU with Cogan's own
manager identity; kernel and manager from the same newest CoganSU release, SUSFS as for official KernelSU."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from kernel import build_history as bh
from kernel import release_from_run as rr
from kernel import resolve as r
from kernel import run_summary as rs
from kernel import sublevels as sl
from kernel import telegram as tg
from kernel import updates as u

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
BUILD = (ROOT / "kernel/build.sh").read_text()
WORKFLOW = ROOT / ".github/workflows/build-kernel.yml"
TAGS = {"refs/tags/v26.11.04-r3": "a" * 40, "refs/tags/v26.11.04-r10": "b" * 40, "refs/tags/v26.11.03-r20": "c" * 40}
APK = {"assets": [{"name": "CoganSU_v3.3.1_33000-release.apk", "browser_download_url": "https://x/c.apk",
                   "digest": "sha256:" + "1" * 64}]}


class ResolveTest(unittest.TestCase):
    def resolve(self, tags=TAGS, identity=True, fits=True, susfs_box=True):
        def ls_remote(url, *patterns):
            if url == r.COGANSU:
                return tags
            if url == r.NOMOUNT:
                return {"refs/tags/v2.2.0": "c" * 40}
            if url == r.SUSFS:
                return {f"refs/heads/{r.SUSFS_BRANCH}": "5" * 40}
            return {"HEAD": "e" * 40, "refs/heads/main": "d" * 40, "refs/heads/arm64-tools": "f" * 40}

        def api(path):
            if path == "repos/cogan17/CoganSU/releases/tags/v26.11.04-r10":
                return APK
            if "nomount" in path:
                return {"assets": [{"name": "nomount.zip", "browser_download_url": "https://x/n.zip"}]}
            return {"tag_name": "06092026"}
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.multiple(r, ls_remote=ls_remote, api=api, run=lambda *a, **k: "",
                                    ack_releases=lambda refs: [], pick_ack=lambda releases, wanted: [],
                                    cogansu_identity=mock.Mock(return_value=identity),
                                    patch_fits=mock.Mock(return_value=fits),
                                    susfs_sidex=lambda: {"commit": "6" * 40}):
            return r.resolve("CSU", "lts", tmp, susfs_box=susfs_box)

    def test_kernel_and_manager_from_the_same_newest_release(self):
        snap = self.resolve()
        self.assertEqual(snap["root_source"], {"repo": r.COGANSU, "tag": "v26.11.04-r10", "commit": "b" * 40})
        self.assertEqual(snap["manager"], {"kind": "release", "tag": "v26.11.04-r10",
                                           "name": "CoganSU_v3.3.1_33000-release.apk", "url": "https://x/c.apk",
                                           "digest": "sha256:" + "1" * 64})

    def test_no_release_yet_waits(self):
        with self.assertRaises(r.Wait) as caught:
            self.resolve(tags={})
        self.assertIn("Tunggu rilis CoganSU pertama", caught.exception.id_text)

    def test_a_release_without_the_manager_certificate_waits(self):
        with self.assertRaises(r.Wait) as caught:
            self.resolve(identity=False)
        self.assertIn("kernel/cogansu.mk di rilis v26.11.04-r10", caught.exception.id_text)

    def test_susfs_patch_must_fit_unless_unticked(self):
        with self.assertRaises(r.Wait) as caught:
            self.resolve(fits=False)
        self.assertIn("Tunggu simonpunk menyesuaikan SUSFS", caught.exception.id_text)
        self.assertNotIn("susfs", self.resolve(fits=False, susfs_box=False))

    def test_identity_is_read_from_cogansu_mk(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = ["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t"]
            subprocess.run(["git", "init", "-q", tmp], check=True)
            Path(tmp, "kernel").mkdir()
            mk = Path(tmp, "kernel/cogansu.mk")
            mk.write_text("COGANSU_PACKAGE_NAME := com.cogan.su\nCOGANSU_EXPECTED_SIZE :=\nCOGANSU_EXPECTED_HASH :=\n")
            subprocess.run([*git, "add", "-A"], check=True)
            subprocess.run([*git, "commit", "-qm", "empty"], check=True)
            self.assertFalse(r.cogansu_identity(tmp, "HEAD"))
            mk.write_text("COGANSU_PACKAGE_NAME := com.cogan.su\nCOGANSU_EXPECTED_SIZE := 0x033b\n"
                          "COGANSU_EXPECTED_HASH := " + "c" * 64 + "\n")
            subprocess.run([*git, "commit", "-qam", "filled"], check=True)
            self.assertTrue(r.cogansu_identity(tmp, "HEAD"))

    def test_release_tags_order_by_date_then_revision(self):
        self.assertEqual(r.cogansu_release(TAGS), ("v26.11.04-r10", "b" * 40))
        self.assertIsNone(r.cogansu_release({"refs/tags/v3.3.1": "d" * 40}))


class BuildTest(unittest.TestCase):
    def test_build_sets_up_cogansu_and_the_kernelsu_susfs_patch(self):
        self.assertIn('CSU) VARIANT="CoganSU"; ROOT_NAME="CoganSU" ;;', BUILD)
        self.assertIn('curl -fsSL "https://raw.githubusercontent.com/cogan17/CoganSU/$ROOT_COMMIT/kernel/setup.sh"', BUILD)
        self.assertIn('[ "$(git -C KernelSU rev-parse HEAD)" = "$ROOT_COMMIT" ] || fail "CoganSU checkout is not $ROOT_COMMIT"', BUILD)
        self.assertIn('if [ "$ROOT" = "KSU" ] || [ "$ROOT" = "CSU" ]; then', BUILD)
        self.assertIn('"$OUT/2-MANAGER_CoganSU_$(snap manager.tag).apk"', BUILD)


@unittest.skipUnless(yaml, "PyYAML")
class WorkflowTest(unittest.TestCase):
    def test_form_offers_cogansu_on_its_own(self):
        wf = yaml.safe_load(WORKFLOW.read_text())
        options = wf[True]["workflow_dispatch"]["inputs"]["root_flavor"]["options"]
        self.assertIn("CoganSU", options)
        self.assertFalse([o for o in options if "&" in o and "CoganSU" in o])
        plan = next(s["run"] for s in wf["jobs"]["resolve"]["steps"] if s.get("id") == "plan")
        self.assertIn('"CoganSU") roots=(CSU) ;;', plan)
        self.assertIn('"CSU": "CoganSU"', plan)


class ReportsTest(unittest.TestCase):
    def test_every_report_knows_cogansu(self):
        for roots in (bh.ROOTS, rs.ROOTS, sl.ROOTS, u.ROOT_NAMES):
            self.assertEqual(roots["CSU"], "CoganSU")
        self.assertEqual(rr.ROOTS["CoganSU"], "CoganSU")
        self.assertIn("CSU", u.ROOT_KEYS)
        self.assertEqual(tg.root_name("CoganSU v26.11.04-r10"), "CoganSU")

    def test_sublevel_record_knows_cogansu(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp, "build-info-CSU-176")
            folder.mkdir()
            (folder / "build.env").write_text(f"ACK_TAG=android14-6.1-2026-09_r5\nZIP_SHA256={'a' * 64}\n")
            self.assertEqual(sl.record_run({}, Path(tmp), "70"), [("176", "CoganSU", "ok")])


if __name__ == "__main__":
    unittest.main()

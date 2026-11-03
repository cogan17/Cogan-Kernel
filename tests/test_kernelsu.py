#!/usr/bin/env python3
"""Official KernelSU (tiann) as a third root manager (owner 2026-11-02: "integrasi dengan ksu (induk segala
induk)"): kernel and manager from the newest main commit the official CI built a manager for, SUSFS through
simonpunk's own patch for KernelSU, strict."""
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from kernel import resolve as r
from kernel import sublevels as sl
from kernel import telegram as tg

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
BUILD = (ROOT / "kernel/build.sh").read_text()
WORKFLOW = ROOT / ".github/workflows/build-kernel.yml"
MAIN = "28db74f6f4692e97006ce9ebd8b19b9cc614b5b7"


class PatchFitsTest(unittest.TestCase):
    def test_checks_on_a_scratch_index_without_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = ["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t"]
            subprocess.run(["git", "init", "-q", tmp], check=True)
            Path(tmp, "kernel").mkdir()
            Path(tmp, "kernel/Kbuild").write_text("obj-y += a.o\n")
            subprocess.run([*git, "add", "-A"], check=True)
            subprocess.run([*git, "commit", "-qm", "base"], check=True)
            fits = "--- a/kernel/Kbuild\n+++ b/kernel/Kbuild\n@@ -1 +1,2 @@\n obj-y += a.o\n+obj-y += susfs.o\n"
            stale = fits.replace(" obj-y += a.o", " obj-y += b.o")
            self.assertTrue(r.patch_fits(tmp, "HEAD", fits))
            self.assertFalse(r.patch_fits(tmp, "HEAD", stale))
            self.assertEqual(Path(tmp, "kernel/Kbuild").read_text(), "obj-y += a.o\n")  # tree untouched


class ResolveTest(unittest.TestCase):
    def resolve(self, fits=True, susfs_box=True, main=None):
        def ls_remote(url, *patterns):
            if url == r.NOMOUNT:
                return {"refs/tags/v2.2.0": "c" * 40}
            if url == r.SUSFS:
                return {f"refs/heads/{r.SUSFS_BRANCH}": "5" * 40}
            return {"HEAD": "e" * 40, "refs/heads/main": "d" * 40, "refs/heads/arm64-tools": "f" * 40}

        def api(path):
            if "nomount" in path:
                return {"assets": [{"name": "nomount.zip", "browser_download_url": "https://x/n.zip"}]}
            return {"tag_name": "06092026"}
        manager = {"repo": "tiann/KernelSU", "run": 88, "url": "https://ksu/run/88", "manager": 3}
        main = main or (lambda: (MAIN, manager))
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.multiple(r, ls_remote=ls_remote, api=api, run=lambda *a, **k: "", ksu_main=main,
                                    ack_releases=lambda refs: [], pick_ack=lambda releases, wanted: [],
                                    patch_fits=mock.Mock(return_value=fits),
                                    susfs_sidex=lambda: {"commit": "6" * 40}):
            return r.resolve("KSU", "lts", tmp, susfs_box=susfs_box)

    def test_kernel_and_manager_from_the_same_main_commit(self):
        snap = self.resolve()
        self.assertEqual(snap["root_source"], {"repo": r.KSU, "branch": "main", "commit": MAIN})
        self.assertEqual(snap["manager"], {"kind": "ci", "repo": "tiann/KernelSU", "run": 88,
                                           "url": "https://ksu/run/88", "manager": 3})
        self.assertIn("susfs", snap)

    def test_a_susfs_patch_that_does_not_fit_waits_for_simonpunk(self):
        with self.assertRaises(r.Wait) as caught:
            self.resolve(fits=False)
        self.assertIn("Tunggu simonpunk", caught.exception.id_text)
        self.assertIn("KernelSU main terbaru `28db74f6f469`", caught.exception.id_text)

    def test_without_susfs_no_patch_check(self):
        snap = self.resolve(fits=False, susfs_box=False)
        self.assertNotIn("susfs", snap)
        self.assertEqual(snap["root_source"]["commit"], MAIN)

    def test_no_official_manager_build_waits(self):
        def missing():
            raise r.Wait("Tunggu build CI resmi manager KernelSU", "Wait for the official KernelSU CI")
        with self.assertRaises(r.Wait):
            self.resolve(main=missing)

    def test_newest_main_ci_run_with_a_manager(self):
        runs = {"workflow_runs": [{"id": 2, "head_sha": "b" * 40, "html_url": "u2"},
                                  {"id": 1, "head_sha": MAIN, "html_url": "u1"}]}
        artifacts = {2: {"artifacts": [{"name": "manager", "id": 7, "expired": True}]},
                     1: {"artifacts": [{"name": "manager", "id": 8, "expired": False}]}}

        def api(path):
            if "/runs?" in path:
                self.assertIn("tiann/KernelSU/actions/workflows/build-manager.yml/runs?branch=main&event=push", path)
                return runs
            return artifacts[int(re.search(r"runs/(\d+)/artifacts", path)[1])]
        commit, manager = r.ksu_main(api)
        self.assertEqual((commit, manager["manager"]), (MAIN, 8))   # the newest with an unexpired manager

    def test_cli_accepts_ksu(self):
        seen = {}

        def fake(root, sublevel, work, unicode=False, susfs_box=True):
            seen["root"] = root
            return {"root": root}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(r, "resolve", fake):
            r.main(["--root", "KSU", "--out", str(Path(tmp, "s.json"))])
        self.assertEqual(seen["root"], "KSU")


class BuildTest(unittest.TestCase):
    def test_build_sets_up_official_kernelsu_and_its_susfs_patch(self):
        self.assertIn('KSU) VARIANT="KernelSU"; ROOT_NAME="KernelSU" ;;', BUILD)
        self.assertIn('curl -fsSL "https://raw.githubusercontent.com/tiann/KernelSU/$ROOT_COMMIT/kernel/setup.sh"', BUILD)
        self.assertIn('[ "$(git -C KernelSU rev-parse HEAD)" = "$ROOT_COMMIT" ] || fail "KernelSU checkout is not $ROOT_COMMIT"', BUILD)
        self.assertIn('git -C KernelSU apply --whitespace=nowarn "$WORK/susfs/kernel_patches/KernelSU/10_enable_susfs_for_ksu.patch"', BUILD)
        self.assertIn('|| wait_for "Tunggu simonpunk menyesuaikan SUSFS dengan KernelSU main', BUILD)
        self.assertIn('mv "$WORK/$kind.apk" "$OUT/${prefix}_KernelSU_main-$(echo "$ROOT_COMMIT" | cut -c1-8).apk"', BUILD)


@unittest.skipUnless(yaml, "PyYAML")
class WorkflowTest(unittest.TestCase):
    def test_form_offers_kernelsu_and_maps_names_exactly(self):
        wf = yaml.safe_load(WORKFLOW.read_text())
        box = wf[True]["workflow_dispatch"]["inputs"]["root_flavor"]
        self.assertEqual(box["default"], "KernelSU Next")
        self.assertEqual(box["options"], ["KernelSU Next", "KernelSU Next & BakaSU", "BakaSU", "KernelSU",
                                          "KernelSU Next & KernelSU", "SukiSU", "KernelSU Next & SukiSU", "Semua / All"])
        plan = next(s["run"] for s in wf["jobs"]["resolve"]["steps"] if s.get("id") == "plan")
        case = re.search(r'case "\$ROOT_FLAVOR" in\n(.*?)esac', plan, re.S)[1]
        for flavor, roots in (("KernelSU Next", "roots=(KSUN)"), ("BakaSU", "roots=(BSU)"), ("KernelSU", "roots=(KSU)"),
                              ("KernelSU Next & KernelSU", "roots=(KSUN KSU)"), ("SukiSU", "roots=(SUKI)"),
                              ("KernelSU Next & SukiSU", "roots=(KSUN SUKI)"), ("Semua / All", "roots=(KSUN BSU KSU SUKI)")):
            self.assertIn(f'"{flavor}") {roots} ;;', case)
        self.assertNotIn('== *"KernelSU', plan)   # "KernelSU" must not match "KernelSU Next"

    def test_a_release_needs_one_root(self):
        wf = WORKFLOW.read_text()
        self.assertIn('[[ "$ROOT_FLAVOR" != *"&"* && "$ROOT_FLAVOR" != Semua* && -n "${SUBLEVEL// /}"', wf)


class ReportsTest(unittest.TestCase):
    def test_root_name_is_exact(self):
        self.assertEqual(tg.root_name("KernelSU Next dev-susfs"), "KernelSU Next")
        self.assertEqual(tg.root_name("KernelSU main"), "KernelSU")
        self.assertEqual(tg.root_name("BakaSU main"), "BakaSU")
        self.assertIsNone(tg.root_name("KernelSUX main"))

    def test_kernelsu_never_takes_kernelsu_next_as_its_previous_release(self):
        body = ("## KernelSU Next · 6.1.176\n- Root: KernelSU Next dev-susfs `aaaaaaaaaaaa` (33453) + SUSFS v2.3.0 `bbbbbbb`\n"
                "## KernelSU · 6.1.176\n- Root: KernelSU main `cccccccccccc` + SUSFS v2.3.0 `bbbbbbb`\n")
        releases = [{"tag_name": "v26.11.03-r9", "body": body, "target_commitish": "d" * 40}]
        self.assertEqual(tg.previous(releases, {"ROOT_NAME": "KernelSU"})["root"][1], "cccccccccccc")
        self.assertEqual(tg.previous(releases, {"ROOT_NAME": "KernelSU Next"})["root"][1], "aaaaaaaaaaaa")
        only_next = [{"tag_name": "v26.11.03-r9", "body": body.split("## KernelSU ·")[0], "target_commitish": "d" * 40}]
        self.assertIsNone(tg.previous(only_next, {"ROOT_NAME": "KernelSU"}))

    def test_sublevel_record_and_table_know_kernelsu(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp, "build-info-KSU-176")
            folder.mkdir()
            (folder / "build.env").write_text(f"ACK_TAG=android14-6.1-2026-09_r5\nZIP_SHA256={'a' * 64}\n")
            record = {}
            changed = sl.record_run(record, Path(tmp), "50")
        self.assertEqual(changed, [("176", "KernelSU", "ok")])
        self.assertIn("✅ KernelSU: [build + gate KMI]", sl.table(record, "id"))


if __name__ == "__main__":
    unittest.main()

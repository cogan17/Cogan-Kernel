#!/usr/bin/env python3
"""SukiSU Ultra as a fourth root manager (owner 2026-11-02): with SUSFS the kernel-only `builtin` branch
(SUSFS built into the root driver), without SUSFS the newest release's own commit; the manager is always the
newest release's APK; KPM stays off."""
import re
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
RELEASE, BUILTIN = "e67b14e6bbbbd3e67f24df658a01d3e73a64159c", "1cfa57340590971cba7521ed536da8ebbedc5f0a"
APKS = [{"name": "SukiSU_Ultra_v4.3.0_40571-release-spoofed.apk", "browser_download_url": "https://x/spoofed.apk"},
        {"name": "SukiSU_Ultra_v4.3.0_40571-arm64-v8a-release.apk", "browser_download_url": "https://x/arm64.apk"},
        {"name": "SukiSU_Ultra_v4.3.0_40571-release.apk", "browser_download_url": "https://x/universal.apk",
         "digest": "sha256:" + "1" * 64}]


class ResolveTest(unittest.TestCase):
    def resolve(self, susfs_box=True, builtin_susfs=True, assets=None, problem=None):
        def ls_remote(url, *patterns):
            if url == r.SUKISU:
                return {"refs/tags/v4.3.0": RELEASE, "refs/tags/v4.2.1": "0" * 40, "refs/tags/v4.2.1-r2": "9" * 40,
                        f"refs/heads/{r.SUKISU_BUILTIN}": BUILTIN}
            if url == r.NOMOUNT:
                return {"refs/tags/v2.2.0": "c" * 40}
            if url == r.SUSFS:
                return {f"refs/heads/{r.SUSFS_BRANCH}": "5" * 40}
            return {"HEAD": "e" * 40, "refs/heads/main": "d" * 40, "refs/heads/arm64-tools": "f" * 40}

        def api(path):
            if path == "repos/SukiSU-Ultra/SukiSU-Ultra/releases/tags/v4.3.0":
                return {"assets": APKS if assets is None else assets}
            if "nomount" in path:
                return {"assets": [{"name": "nomount.zip", "browser_download_url": "https://x/n.zip"}]}
            return {"tag_name": "06092026"}
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.multiple(r, ls_remote=ls_remote, api=api, run=lambda *a, **k: "",
                                    ack_releases=lambda refs: [], pick_ack=lambda releases, wanted: [],
                                    has_builtin_susfs=mock.Mock(return_value=builtin_susfs),
                                    sukisu_ready=mock.Mock(return_value=problem),
                                    susfs_sidex=lambda: {"commit": "6" * 40}):
            return r.resolve("SUKI", "lts", tmp, susfs_box=susfs_box)

    def test_with_susfs_the_builtin_branch_and_the_release_manager(self):
        snap = self.resolve()
        self.assertEqual(snap["root_source"], {"repo": r.SUKISU, "branch": "builtin", "commit": BUILTIN,
                                               "manager_tag": "v4.3.0"})
        self.assertEqual(snap["manager"], {"kind": "release", "tag": "v4.3.0", "name": APKS[2]["name"],
                                           "url": "https://x/universal.apk", "digest": "sha256:" + "1" * 64})
        self.assertIn("susfs", snap)

    def test_without_susfs_the_release_commit_itself(self):
        snap = self.resolve(susfs_box=False, builtin_susfs=False)
        self.assertEqual(snap["root_source"], {"repo": r.SUKISU, "tag": "v4.3.0", "commit": RELEASE})
        self.assertEqual(snap["manager"]["tag"], "v4.3.0")
        self.assertNotIn("susfs", snap)

    def test_a_builtin_branch_without_susfs_waits(self):
        with self.assertRaises(r.Wait) as caught:
            self.resolve(builtin_susfs=False)
        self.assertIn("Tunggu pengembang SukiSU", caught.exception.id_text)
        self.assertIn("no longer carries SUSFS", caught.exception.en_text)

    def test_a_builtin_branch_behind_the_newest_susfs_waits_for_sukisu(self):
        with self.assertRaises(r.Wait) as caught:
            self.resolve(problem="CONFIG_KSU_SUSFS_PRIORITY_UID_FILTER")
        self.assertIn("Tunggu pengembang SukiSU menyesuaikan cabang builtin", caught.exception.id_text)
        self.assertIn("CONFIG_KSU_SUSFS_PRIORITY_UID_FILTER", caught.exception.en_text)
        self.assertIn("lepas centang SUSFS", caught.exception.id_text)
        # Without SUSFS nothing of SUSFS is checked.
        self.assertEqual(self.resolve(susfs_box=False, problem="x")["root_source"]["commit"], RELEASE)

    def test_never_the_spoofed_apk_and_arm64_when_there_is_no_universal_one(self):
        self.assertEqual(self.resolve(assets=APKS[:2])["manager"]["url"], "https://x/arm64.apk")
        with self.assertRaises(r.Wait) as caught:
            self.resolve(assets=APKS[:1])
        self.assertIn("APK manager untuk v4.3.0", caught.exception.id_text)

    def test_builtin_susfs_is_read_from_the_kconfig(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = ["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t"]
            subprocess.run(["git", "init", "-q", tmp], check=True)
            Path(tmp, "kernel").mkdir()
            Path(tmp, "kernel/Kconfig").write_text('menu "KernelSU"\nconfig KSU\n\ttristate "x"\n')
            subprocess.run([*git, "add", "-A"], check=True)
            subprocess.run([*git, "commit", "-qm", "main"], check=True)
            self.assertFalse(r.has_builtin_susfs(tmp, "HEAD"))
            Path(tmp, "kernel/Kconfig").write_text('menu "KernelSU"\nconfig KSU_SUSFS\n\tbool "KernelSU addon - SUSFS"\n')
            subprocess.run([*git, "commit", "-qam", "builtin"], check=True)
            self.assertTrue(r.has_builtin_susfs(tmp, "HEAD"))

    def test_readiness_finds_an_unguarded_call_to_a_feature_sukisu_does_not_know(self):
        header = ("/* sus_map */\n#ifdef CONFIG_KSU_SUSFS_SUS_MAP\nvoid susfs_add_sus_map(void __user **user_info);\n"
                  "#endif // #ifdef CONFIG_KSU_SUSFS_SUS_MAP\n#ifdef CONFIG_KSU_SUSFS_PRIORITY_UID_FILTER\n"
                  "void susfs_set_priority_uid_filter(void __user **user_info);\nvoid susfs_parse_priority_app_strings(void);\n"
                  "#endif\nvoid susfs_set_avc_log_spoofing(void __user **user_info);\n")
        self.assertEqual(r.guarded_functions(header), {"susfs_add_sus_map": "KSU_SUSFS_SUS_MAP",
                                                       "susfs_set_priority_uid_filter": "KSU_SUSFS_PRIORITY_UID_FILTER",
                                                       "susfs_parse_priority_app_strings": "KSU_SUSFS_PRIORITY_UID_FILTER"})
        with tempfile.TemporaryDirectory() as tmp:
            git = ["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t"]
            subprocess.run(["git", "init", "-q", tmp], check=True)
            Path(tmp, "kernel_patches/include/linux").mkdir(parents=True)
            Path(tmp, r.SUSFS_HEADER).write_text(header)
            Path(tmp, "kernel").mkdir()
            Path(tmp, "kernel/Kconfig").write_text("config KSU_SUSFS\n\tbool\nconfig KSU_SUSFS_SUS_MAP\n\tbool\n")
            Path(tmp, "kernel/a.c").write_text("void f(void)\n{\n    susfs_add_sus_map(0);\n    susfs_parse_priority_app_strings();\n}\n")
            subprocess.run([*git, "add", "-A"], check=True)
            subprocess.run([*git, "commit", "-qm", "behind"], check=True)
            self.assertEqual(r.sukisu_ready(tmp, "HEAD", "HEAD"), "CONFIG_KSU_SUSFS_PRIORITY_UID_FILTER")
            # Guarded by the symbol: dead code without it, so it still compiles.
            Path(tmp, "kernel/a.c").write_text("#ifdef CONFIG_KSU_SUSFS_PRIORITY_UID_FILTER\n"
                                               "void g(void) { susfs_parse_priority_app_strings(); }\n#endif\n")
            subprocess.run([*git, "commit", "-qam", "guarded"], check=True)
            self.assertIsNone(r.sukisu_ready(tmp, "HEAD", "HEAD"))
            # SukiSU defines the symbol itself.
            Path(tmp, "kernel/a.c").write_text("void g(void) { susfs_parse_priority_app_strings(); }\n")
            Path(tmp, "kernel/Kconfig").write_text("config KSU_SUSFS\n\tbool\nconfig KSU_SUSFS_PRIORITY_UID_FILTER\n\tbool\n")
            subprocess.run([*git, "commit", "-qam", "adapted"], check=True)
            self.assertIsNone(r.sukisu_ready(tmp, "HEAD", "HEAD"))

    def test_cli_accepts_suki(self):
        seen = {}

        def fake(root, sublevel, work, unicode=False, susfs_box=True):
            seen["root"] = root
            return {"root": root}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(r, "resolve", fake):
            r.main(["--root", "SUKI", "--out", str(Path(tmp, "s.json"))])
        self.assertEqual(seen["root"], "SUKI")


class BuildTest(unittest.TestCase):
    def test_build_sets_up_sukisu_strictly_without_kpm(self):
        self.assertIn('SUKI) VARIANT="SukiSU"; ROOT_NAME="SukiSU" ;;', BUILD)
        self.assertIn('curl -fsSL "https://raw.githubusercontent.com/SukiSU-Ultra/SukiSU-Ultra/$ROOT_COMMIT/kernel/setup.sh"', BUILD)
        # Its setup.sh falls back to the default branch silently when the checkout fails.
        self.assertIn('[ "$(git -C KernelSU rev-parse HEAD)" = "$ROOT_COMMIT" ] || fail "SukiSU checkout is not $ROOT_COMMIT"', BUILD)
        self.assertIn('[ "$ROOT" = "SUKI" ] && echo "# CONFIG_KPM is not set"', BUILD)
        self.assertIn("! grep -qx 'CONFIG_KPM=y' \"$KOUT/.config\" || fail", BUILD)

    def test_sukisu_needs_no_root_driver_patch_for_susfs(self):
        susfs = BUILD[BUILD.index('group "SUSFS'):BUILD.index('SUSFS_VERSION="$(sed')]
        self.assertNotIn("SUKI", susfs)   # built in: only simonpunk's kernel patch, as for every root

    def test_manager_from_the_release(self):
        self.assertIn('download_digest "$(snap manager.url)" "$OUT/2-MANAGER_SukiSU_$(snap manager.tag).apk" "$(snap manager.digest)"', BUILD)
        self.assertLess(BUILD.index('if [ "$ROOT" = "SUKI" ]; then\n  # The newest SukiSU release'),
                        BUILD.index('elif [ "$(snap manager.kind)" = "release" ]; then'))


@unittest.skipUnless(yaml, "PyYAML")
class WorkflowTest(unittest.TestCase):
    def test_plan_names_sukisu(self):
        plan = next(s["run"] for s in yaml.safe_load(WORKFLOW.read_text())["jobs"]["resolve"]["steps"] if s.get("id") == "plan")
        self.assertIn('"SUKI": "SukiSU"', plan)
        self.assertIn('version += f" · manager {src[\'manager_tag\']}"', plan)


class ReportsTest(unittest.TestCase):
    def test_every_report_knows_sukisu(self):
        for roots in (bh.ROOTS, rs.ROOTS, sl.ROOTS, u.ROOT_NAMES):
            self.assertEqual(roots["SUKI"], "SukiSU")
        self.assertEqual(rr.ROOTS["SukiSU"], "SukiSU")
        self.assertIn("SUKI", u.ROOT_KEYS)
        self.assertEqual(tg.root_name("SukiSU builtin"), "SukiSU")

    def test_sublevel_record_knows_sukisu(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp, "build-info-SUKI-176")
            folder.mkdir()
            (folder / "build.env").write_text(f"ACK_TAG=android14-6.1-2026-09_r5\nZIP_SHA256={'a' * 64}\n")
            changed = sl.record_run({}, Path(tmp), "60")
        self.assertEqual(changed, [("176", "SukiSU", "ok")])


class CheckTest(unittest.TestCase):
    class Net:
        def __init__(self, builtin=BUILTIN, problem=None):
            self.builtin, self.problem = builtin, problem

        def sukisu_ready(self, builtin, susfs):
            return self.problem

        def ls_remote(self, url, *patterns):
            return {"refs/tags/v4.3.0": RELEASE, f"refs/heads/{r.SUKISU_BUILTIN}": self.builtin}

        def api(self, path):
            if path.endswith("releases/tags/v4.3.0"):
                return {"tag_name": "v4.3.0", "published_at": "2026-10-29T07:28:09Z", "html_url": "https://suki", "body": "notes"}
            if "/compare/" in path:
                return {"commits": [{"sha": self.builtin, "commit": {"committer": {"date": "2026-11-02T00:00:00Z"},
                                                                     "message": "kernel: Fix mount_hide crash"}}]}
            sha = re.search(r"commits/(\w+)$", path)[1]
            return {"sha": sha, "commit": {"committer": {"date": "2026-11-01T15:59:33Z"}, "message": "kernel: sync"}}

    def check(self, base, builtin=BUILTIN, problem=None):
        builds = {"SUKI": {"snap": {"root_source": base}}} if base else {}
        return u.check_sukisu(self.Net(builtin, problem), builds, "5" * 40)

    def test_never_built_is_not_used(self):
        self.assertEqual(self.check(None)["status"], "off")

    def test_same_builtin_and_manager_release(self):
        found = self.check({"branch": "builtin", "commit": BUILTIN, "manager_tag": "v4.3.0"})
        self.assertEqual(found["status"], "same")
        self.assertEqual(found["ci"]["label"], "builtin `1cfa57340590`")

    def test_a_newer_builtin_commit_is_new(self):
        found = self.check({"branch": "builtin", "commit": BUILTIN, "manager_tag": "v4.3.0"}, builtin="2" * 40)
        self.assertEqual(found["status"], "new")
        self.assertEqual(found["changes"][0]["title"], "kernel: Fix mount_hide crash")

    def test_a_builtin_branch_behind_susfs_waits_for_sukisu(self):
        found = self.check(None, problem="CONFIG_KSU_SUSFS_PRIORITY_UID_FILTER")
        self.assertEqual(found["status"], "wait")
        self.assertIn("Tunggu pengembang SukiSU", found["wait"]["id"])
        self.assertIn("belum cocok (CONFIG_KSU_SUSFS_PRIORITY_UID_FILTER)", found["lines"][-1]["id"])

    def test_a_build_without_susfs_is_compared_with_the_release(self):
        self.assertEqual(self.check({"tag": "v4.3.0", "commit": RELEASE})["status"], "same")


if __name__ == "__main__":
    unittest.main()

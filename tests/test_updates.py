#!/usr/bin/env python3
"""Offline tests for kernel/updates.py (Cek pembaruan): newest versions against the last build, two languages."""
import base64
import json
import unittest
import zipfile

from kernel import resolve as r
from kernel import updates as u

REPO = "cogan17/Cogan-Kernel"
A, D, M = "a" * 40, "d" * 40, "m" * 40
SUSFS_OLD, SUSFS_NEW = "c27ebe93c68e953c248b11bb747ef220ea648373", "27e0a0e42745991ba09d6f96a97bf4b83f41a012"
BAKA_REL, BAKA_MAIN = "b" * 40, "e" * 40
SNAP = {"root": "KSUN", "ack": [{"tag": "android14-6.1-2025-09_r36", "commit": "4" * 40, "sublevel": 145},
                                {"tag": "android14-6.1-2026-09_r4", "commit": "1" * 40, "sublevel": 176}],
        "susfs": {"repo": r.SUSFS, "branch": r.SUSFS_BRANCH, "commit": SUSFS_OLD},
        "root_source": {"repo": r.KSUN_FORK, "branch": "dev-susfs", "commit": A, "base": M, "ksu_version": 33405},
        "nomount": {"tag": "v2.2.0"}, "bbg": {"commit": "f" * 40}, "anykernel": {"commit": "9" * 40, "arm64_tools": "8" * 40},
        "neutron": {"tag": "24102026"}}


def commit(sha, date, title):
    return {"sha": sha, "commit": {"committer": {"date": date}, "message": title + "\n\nbody"}}


class FakeNet:
    def __init__(self, *, runs=True, ack="android14-6.1-2026-10_r2", susfs=SUSFS_NEW, nomount="v2.3.0",
                 bakasu=("SUSFS diblokir di BakaSU / SUSFS blocked in BakaSU", None), manager=True):
        self.runs, self.ack, self.susfs, self.nomount, self.bakasu, self.manager = runs, ack, susfs, nomount, bakasu, manager
        self.apis = {
            f"repos/{REPO}/actions/workflows/build-kernel.yml/runs?branch=main&status=completed&per_page=30":
                {"workflow_runs": [{"id": 11, "run_number": 6, "html_url": "https://run/11", "created_at": "2026-10-24T01:00:00Z"}]
                 if runs else []},
            f"repos/{REPO}/actions/runs/11/artifacts?per_page=100": {"artifacts": [
                {"id": 5, "name": "snapshots-6", "expired": False},
                {"id": 6, "name": "1-KERNEL_Cogan-Rothko-ACK-6.1.176_KernelSU-Next+SuSFS_v26.10.24-r6.zip", "expired": False}]},
            f"repos/pershoot/KernelSU-Next/commits/{A}": commit(A, "2026-10-25T02:00:00Z", "kernel: sync"),
            "repos/KernelSU-Next/KernelSU-Next/releases/latest":
                {"tag_name": "v3.4.2", "published_at": "2026-10-01T00:00:00Z", "html_url": "https://ksun/v3.4.2",
                 "body": "## Changes\n![shot](x.png)\n- fix boot\n"},
            "repos/Baka-SU/BakaSU/releases/tags/v1.2.0": {"tag_name": "v1.2.0", "published_at": "2026-10-20T00:00:00Z",
                                                         "html_url": "https://baka/v1.2.0", "body": "BakaSU v1.2.0"},
            "repos/Baka-SU/BakaSU/actions/workflows/build-manager.yml/runs?branch=main&event=push&per_page=5":
                {"workflow_runs": [{"id": 77, "head_sha": BAKA_MAIN, "html_url": "https://baka/run/77"}]},
            "repos/Baka-SU/BakaSU/actions/runs/77/artifacts?per_page=100":
                {"artifacts": [{"name": "Manager-release", "id": 1, "expired": False}]},
            f"repos/Baka-SU/BakaSU/commits/{BAKA_MAIN}": commit(BAKA_MAIN, "2026-10-24T10:00:00Z", "susfs: hooks"),
            f"repos/maxsteeel/nomount/releases/tags/{nomount}": {"tag_name": nomount, "published_at": "2026-10-23T00:00:00Z",
                                                               "html_url": "https://nomount", "body": "NoMount notes"},
            "repos/maxsteeel/nomount/commits/" + "h" * 40: commit("h" * 40, "2026-10-25T00:00:00Z", "wip"),
            f"repos/maxsteeel/nomount/compare/{nomount}..." + "h" * 40: {"commits": [commit("h" * 40, "2026-10-25T00:00:00Z", "wip")]},
            "repos/maxsteeel/nomount/compare/v2.2.0...v2.3.0": {"commits": [
                commit("1" * 40, "2026-10-22T00:00:00Z", "Fix mount leak on reboot"),
                commit("2" * 40, "2026-10-23T00:00:00Z", "Add overlay support")]},
            "repos/vc-teahouse/Baseband-guard/commits/" + "f" * 40: commit("f" * 40, "2026-10-01T00:00:00Z", "bbg"),
            "repos/osm0sis/AnyKernel3/commits/" + "9" * 40: commit("9" * 40, "2026-09-01T00:00:00Z", "ak3"),
            "repos/Neutron-Toolchains/clang-build-catalogue/releases/latest":
                {"tag_name": "24102026", "published_at": "2026-10-24T00:00:00Z", "html_url": "https://neutron"},
            "repos/WildKernels/kernel_patches/commits?path=common/unicode_bypass_fix_6.1%2B.patch&per_page=5":
                [commit("u" * 40, "2026-10-10T00:00:00Z", "unicode fix")],
        }

    def api(self, path):
        if path not in self.apis:
            raise OSError(f"no fake for {path}")
        return self.apis[path]

    def gitlab(self, path):
        return {f"/repository/commits/{self.susfs}": {"created_at": "2026-10-24T19:44:31.000+08:00"},
                f"/repository/compare?from={SUSFS_OLD}&to={self.susfs}": {"commits": [
                    {"id": "3" * 40, "created_at": "2026-10-20T10:00:00+08:00", "title": "kernel: Fix crash in sus_path"},
                    {"id": self.susfs, "created_at": "2026-10-24T19:44:31+08:00", "title": "kernel & KernelSU: Sync with upstream"}]},
                }[path]

    def http(self, url):
        if url.endswith("/Makefile?format=TEXT"):
            return base64.b64encode(b"VERSION = 6\nPATCHLEVEL = 1\nSUBLEVEL = 180\n")
        if url.endswith("?format=JSON"):
            return b")]}'\n" + json.dumps({"committer": {"time": "Thu Oct 22 05:25:51 2026 +0000"}}).encode()
        if "susfs.h" in url:
            return b'#define SUSFS_VERSION "v2.3.1"\n'
        raise OSError(url)

    def ls_remote(self, url, *patterns):
        table = {
            r.ACK: {f"refs/tags/{self.ack}": "7" * 40, "refs/tags/android14-6.1-2026-09_r4": "1" * 40},
            r.SUSFS: {f"refs/heads/{r.SUSFS_BRANCH}": self.susfs},
            r.KSUN_FORK: {"refs/heads/dev-susfs": A, "refs/heads/dev": D},
            r.BAKASU: {"refs/tags/v1.2.0": BAKA_REL, "refs/tags/v1.1.0": "0" * 40},
            r.NOMOUNT: {f"refs/tags/{self.nomount}": "n" * 40, "refs/tags/v2.2.0": "o" * 40, "HEAD": "h" * 40},
            r.BBG: {"refs/heads/main": "f" * 40},
            r.ANYKERNEL: {"HEAD": "9" * 40, "refs/heads/arm64-tools": "8" * 40},
        }[url]
        return {k: v for k, v in table.items() if k in patterns or any(p.endswith("*") and k.startswith(p[:-1]) for p in patterns)}

    def download(self, repo, artifact, dest):
        with zipfile.ZipFile(dest, "w") as archive:
            archive.writestr("KSUN.json", json.dumps(SNAP))
            archive.writestr("BSU.json", json.dumps({"root": "BSU", "wait": {"id": "tunggu", "en": "wait"}}))

    def ksun_manager(self, base):
        if not self.manager:
            raise r.Wait("Tunggu build CI resmi manager KernelSU Next.", "Wait for the official KernelSU Next CI manager build.")
        return {"run": 1}

    def ksu_version(self, head, dev):
        return M, 33410

    def bakasu_ready(self, release, main, susfs):
        return self.bakasu


class UpdatesTest(unittest.TestCase):
    def run_check(self, **kwargs):
        builds, found = u.gather(FakeNet(**kwargs), REPO)
        return builds, {e["key"]: e for e in found}, u.summary(builds, found)

    def test_newer_components_ask_for_a_build(self):
        builds, found, text = self.run_check()
        self.assertEqual(builds["KSUN"]["run"], 6)
        self.assertNotIn("BSU", builds)                                    # its snapshot only waited
        statuses = {k: e["status"] for k, e in found.items()}
        self.assertEqual(statuses, {"ack": "new", "susfs": "new", "ksun": "same", "bakasu": "unknown", "nomount": "new",
                                    "bbg": "same", "anykernel": "same", "neutron": "same", "unicode": "off"})
        self.assertIn("🆕 **Ada pembaruan: ACK android14-6.1, SUSFS (simonpunk), NoMount.** Silakan jalankan **Cogan Kernel Builder**", text)
        self.assertIn("🆕 **Updates: ACK android14-6.1, SUSFS (simonpunk), NoMount.** Run **Cogan Kernel Builder**", text)
        self.assertIn("Rilis ACK baru: `android14-6.1-2026-10_r2`", text)
        self.assertIn("| `android14-6.1-2026-09_r4` | Stabil: `android14-6.1-2026-10_r2` (6.1.180, 22 Okt 2026 12.25 WIB) |", text)
        self.assertIn("CI: v2.3.1 `27e0a0e42745` (24 Okt 2026 18.44 WIB)", text)   # +08:00 → WIB
        self.assertIn("CI: dev-susfs `aaaaaaaaaaaa` (33410, 25 Okt 2026 09.00 WIB)", text)
        # What is new and what was fixed, newest first, in their developers' words.
        susfs = text[text.index("**SUSFS (simonpunk)**"):text.index("**KernelSU Next**")]
        self.assertLess(susfs.index("🔧 Perbaikan"), susfs.index("Fix crash in sus_path"))
        self.assertLess(susfs.index("✨ Baru"), susfs.index("Sync with upstream"))
        self.assertIn("Fix mount leak on reboot", text)
        self.assertIn("1 commit di main sesudah v2.3.0 (belum dirilis; Builder memakai rilis)", text)
        self.assertIn("CI lebih baru dari rilis stabil", text)               # KernelSU Next dev-susfs after v3.4.2
        self.assertIn("Manager CI resmi untuk commit ini: ada", text)
        # BakaSU: the release is blocked, main is ready, as resolve.py decides.
        self.assertIn("Rilis v1.2.0: SUSFS diblokir di BakaSU / SUSFS blocked in BakaSU", text)
        self.assertIn(f"main `{BAKA_MAIN[:8]}`: siap untuk SUSFS terbaru", text)
        self.assertIn(f"Builder akan memakai: main `{BAKA_MAIN[:8]}` (CI)", text)
        self.assertIn("Build terakhir: KernelSU Next [run #6](https://run/11) (24 Okt 2026 08.00 WIB).", text)
        self.assertIn("Build terakhir tanpa Unicode fix.", text)
        self.assertLess(text.index("🇮🇩"), text.index("🇬🇧"))
        self.assertNotIn("![shot]", text)                                     # release notes without images

    def test_all_the_same_and_bakasu_blocked(self):
        _, found, text = self.run_check(ack="android14-6.1-2026-09_r4", susfs=SUSFS_OLD, nomount="v2.2.0",
                                        bakasu=("SUSFS diblokir di BakaSU / SUSFS blocked in BakaSU", "`my_setprocattr` missing"))
        self.assertIn("✅ **Semua komponen sama dengan build terakhir.** Belum perlu build.", text)
        self.assertIn("✅ **Every component equals the last build.** No build needed yet.", text)
        self.assertEqual(found["bakasu"]["status"], "wait")
        self.assertIn("⏳ **Belum bisa dibangun:**", text)
        self.assertIn("- BakaSU: Tunggu pengembang BakaSU: rilis v1.2.0 dan main belum siap untuk SUSFS terbaru", text)
        self.assertIn("- BakaSU: Wait for the BakaSU developer: release v1.2.0 and main are not ready", text)

    def test_a_missing_ci_manager_is_a_wait(self):
        _, found, text = self.run_check(manager=False)
        self.assertEqual(found["ksun"]["status"], "wait")
        self.assertIn("- KernelSU Next: Tunggu build CI resmi manager KernelSU Next.", text)

    def test_without_a_last_build_the_newest_versions_still_show(self):
        builds, found, text = self.run_check(runs=False)
        self.assertEqual(builds, {})
        self.assertIn("Belum ada run Builder dengan kernel dalam 90 hari terakhir.", text)
        self.assertNotIn("Ada pembaruan", text)
        self.assertEqual(found["susfs"]["status"], "unknown")

    def test_one_source_down_does_not_hide_the_others(self):
        net = FakeNet()
        del net.apis["repos/Neutron-Toolchains/clang-build-catalogue/releases/latest"]
        builds, found = u.gather(net, REPO)
        entries = {e["key"]: e for e in found}
        self.assertEqual(entries["neutron"]["status"], "error")
        self.assertEqual(entries["susfs"]["status"], "new")
        self.assertIn("⚠️ tidak bisa dicek: no fake for", u.summary(builds, found))

    def test_dates_and_helpers(self):
        self.assertEqual(u.when("2026-10-25T17:05:00Z", "id"), "26 Okt 2026 00.05 WIB")
        self.assertEqual(u.when("2026-08-25T17:05:00Z", "en"), "26 Aug 2026 00:05 WIB")
        self.assertEqual(u.gitiles_time("Thu Oct 22 05:25:51 2026 +0000"), "2026-10-22T05:25:51+00:00")
        fixes, news = u.split_changes([{"title": "Fix leak"}, {"title": "fix(susfs): x"}, {"title": "Add prefix"},
                                       {"title": "Revert hooks"}, {"title": "Prefix fixture"}])
        self.assertEqual([c["title"] for c in fixes], ["Fix leak", "fix(susfs): x", "Revert hooks"])
        self.assertEqual([c["title"] for c in news], ["Add prefix", "Prefix fixture"])


if __name__ == "__main__":
    unittest.main()

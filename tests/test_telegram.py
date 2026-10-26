#!/usr/bin/env python3
"""Offline tests for kernel/telegram.py: a measured What's new, fix commits, both languages."""
import tempfile
import unittest
from pathlib import Path

from kernel import release_notes as rn
from kernel import telegram as tg

R1 = {"RELEASE": "v26.10.23-r1", "RELEASE_NAME": "Cogan-Rothko-ACK v26.10.23-r1", "LINUX_VERSION": "6.1.176",
      "ACK_TAG": "android14-6.1-2026-09_r4", "ROOT_NAME": "KernelSU Next", "ROOT_TAG": "dev-susfs",
      "ROOT_COMMIT": "d21e0a66c887ae4bc75b7c9f83e41761819ec09a", "KSU_VERSION": "33405", "SUSFS_VERSION": "v2.3.0",
      "SUSFS_COMMIT": "c27ebe93c68e953c248b11bb747ef220ea648373", "NOMOUNT": "v2.2.0", "NEUTRON": "06092026",
      "FEATURES": "SUSFS, BBRv3 (default, also bbr3), BBG, NoMount, Cogan Bridge, Full LTO",
      "KMI_COMPAT": "KMI Xiaomi 14T Pro (rothko): OK; CRC differs 0"}
R2 = {**R1, "RELEASE": "v26.10.24-r2", "UNICODE_FIX": "fa76c90e2cb284e6ce22b0b008ad4dd19820dbb1",
      "FEATURES": "SUSFS, BBRv3 (default, also bbr3), BBG, NoMount, Unicode fix, Cogan Bridge, Full LTO"}
RELEASES = [  # newest first, as the API lists them
    {"tag_name": "cogan-smart-v2.8.2", "body": "module", "target_commitish": "a" * 40},
    {"tag_name": "v26.10.23-r1", "target_commitish": "e" * 40,
     "body": rn.notes(R1, ["1-KERNEL_x.zip"], "https://run", "cogan17/Cogan-Kernel", tested=True)},
    {"tag_name": "arsip-v26.10.23-r8", "body": "- Root: BakaSU `5b76b884c75f` + SUSFS v2.3.0 `2474336`"},
]


class TelegramTest(unittest.TestCase):
    def test_previous_release_of_the_same_root_is_read_from_its_notes(self):
        prev = tg.previous(RELEASES, R2)
        self.assertEqual(prev["tag"], "v26.10.23-r1")
        self.assertEqual(prev["kernel"], "6.1.176")
        self.assertEqual(prev["root"][1], "d21e0a66c887")
        self.assertEqual(prev["susfs"], ("v2.3.0", "c27ebe93c68e"))
        self.assertIsNone(tg.previous(RELEASES, {**R2, "ROOT_NAME": "BakaSU"}))  # archives and modules never count

    def test_whats_new_is_measured_against_the_previous_release(self):
        prev = tg.previous(RELEASES, R2)
        self.assertEqual(tg.whats_new(R2, prev, "id"), ["Fitur baru: Unicode fix"])
        self.assertEqual(tg.whats_new(R2, prev, "en"), ["New features: Unicode fix"])
        newer = {**R2, "LINUX_VERSION": "6.1.180", "SUSFS_COMMIT": "1" * 40, "NOMOUNT": "v2.3.0"}
        self.assertEqual(tg.whats_new(newer, prev, "id")[:3], ["Kernel ACK 6.1.176 → 6.1.180",
                                                               "SUSFS v2.3.0 `c27ebe93c68e` → v2.3.0 `111111111111`",
                                                               "NoMount v2.2.0 → v2.3.0"])
        self.assertEqual(tg.whats_new(R1, prev, "en"), ["Same components as v26.10.23-r1"])
        self.assertEqual(tg.whats_new(R1, None, "id"), ["Rilis pertama varian ini"])

    def test_previous_combined_release_uses_each_roots_own_components(self):
        bakasu = {**R1, "ROOT_NAME": "BakaSU", "ROOT_TAG": "main", "ROOT_COMMIT": "b" * 40,
                  "SUSFS_COMMIT": "c" * 40}
        body = "# Combined release\n\n" + "\n".join(rn.notes(env, [], "https://run", "cogan17/Cogan-Kernel")
                                                        for env in (R1, bakasu))
        compact = rn.compact_notes([(env, [], tg.changelog_section(env, "r/r", source_sha="d" * 40))
                                    for env in ({**R1, "ZIP": "1-KERNEL_KSUN.zip"}, {**bakasu, "ZIP": "1-KERNEL_BSU.zip"})],
                                   "https://run", "r/r")
        for layout, text in (("old", body), ("compact", compact)):
            with self.subTest(layout=layout):
                releases = [{"tag_name": R1["RELEASE"], "target_commitish": "e" * 40, "body": text}]
                for env in (R1, bakasu):
                    previous = tg.previous(releases, {**env, "RELEASE": R2["RELEASE"]})
                    self.assertEqual(previous["root"][1], env["ROOT_COMMIT"][:12])
                    self.assertEqual(previous["susfs"][1], env["SUSFS_COMMIT"][:12])
                    if layout == "compact":
                        self.assertEqual(previous["sha"], "d" * 40)

    def test_only_kernel_fixes_become_fixes(self):
        self.assertEqual(tg.fixes(["fix(kernel): alat AnyKernel3 arm64 untuk rothko (#5)\n\nbody",
                                   "fix(builder): semua tidak lagi kena HTTP 429 (#21)",
                                   "docs: README", "feat(kernel): centang Unicode fix (#11)"]),
                         ["alat AnyKernel3 arm64 untuk rothko"])

    def test_post_in_both_languages_with_status_and_link(self):
        prev = tg.previous(RELEASES, R2)
        text = tg.post(R2, "id", prev, ["alat AnyKernel3 arm64"], "https://x/r2", tested=True, note="baris 1\\nbaris 2")
        self.assertIn("📦 v26.10.24-r2 · ACK 6.1.176 · KernelSU Next + SUSFS v2.3.0", text)
        self.assertIn("✨ Baru\n• Fitur baru: Unicode fix", text)
        self.assertIn("🔧 Perbaikan\n• alat AnyKernel3 arm64", text)
        self.assertIn("📝 Catatan\nbaris 1\nbaris 2", text)
        self.assertIn("✅ Diuji di HP\n⬇️ Unduh: https://x/r2", text)
        english = tg.post(R2, "en", prev, link="https://x/run")
        self.assertIn("✨ New\n• New features: Unicode fix", english)
        self.assertIn("⚠️ Not tested on the phone yet", english)
        self.assertIn("🔧 Fixes\n• No additional kernel fix commits recorded in this range", english)

    def test_cli_writes_both_posts_and_survives_without_the_api(self):
        with tempfile.TemporaryDirectory() as temp:
            env = Path(temp) / "build.env"
            env.write_text("".join(f"{k}={v}\n" for k, v in R2.items()))
            out = Path(temp) / "tg"
            asked = []

            def api(path):
                asked.append(path)
                if path.startswith("repos/r/r/releases"):
                    return RELEASES
                return {"commits": [{"commit": {"message": "fix(kernel): perbaikan contoh (#9)"}}]}
            tg.main([str(env), "--repo", "r/r", "--sha", "f" * 40, "--link", "https://x", "--out", str(out)], api=api)
            self.assertIn("• perbaikan contoh", (out / "id.txt").read_text())
            self.assertIn(f"repos/r/r/compare/{'e' * 40}...{'f' * 40}", asked)
            tg.main([str(env), "--repo", "r/r", "--out", str(out)], api=lambda path: None)
            text = (out / "id.txt").read_text()
            self.assertIn("Riwayat rilis belum dapat dibaca", text)
            self.assertIn("Daftar commit perbaikan belum dapat dibaca", text)
            self.assertNotIn("Rilis pertama varian ini", text)

    def test_ack_revision_and_unicode_patch_updates_are_visible(self):
        previous = tg.previous([{"tag_name": R2["RELEASE"], "target_commitish": "e" * 40,
                                 "body": rn.notes(R2, [], "https://run", "r/r")}],
                               {**R2, "RELEASE": "v26.10.26-r4"})
        current = {**R2, "ACK_TAG": "android14-6.1-2026-09_r5", "UNICODE_FIX": "f" * 40, "NEUTRON": "24102026"}
        text = "\n".join(tg.whats_new(current, previous, "id"))
        self.assertIn("Rilis ACK android14-6.1-2026-09_r4 → android14-6.1-2026-09_r5", text)
        self.assertIn("Unicode fix WildKernel `fa76c90e2cb2` → `ffffffffffff`", text)
        self.assertIn("Neutron clang 06092026 → 24102026", text)

    def test_old_preview_ignores_its_own_and_newer_releases(self):
        releases = [{"tag_name": tag, "body": rn.notes(R1, [], "https://run", "r/r"), "target_commitish": "e" * 40}
                    for tag in ("v26.10.26-r10", R2["RELEASE"], R1["RELEASE"])]
        self.assertEqual(tg.previous(releases, R2)["tag"], R1["RELEASE"])

    def test_release_notes_and_post_share_measured_changes_and_fix_status(self):
        def api(path):
            return RELEASES if "/releases?" in path else {"commits": [{"commit": {"message": "fix(kernel): ARM64 flasher"}}]}
        measured = tg.changes(R2, "r/r", "f" * 40, api)
        release = tg.changelog_section(R2, "r/r", **measured)
        for lang in ("id", "en"):
            text = tg.post(R2, lang, **measured)
            self.assertIn("ARM64 flasher", text)
            self.assertIn(tg.WORDS[lang]["new"], release)
            self.assertIn(tg.WORDS[lang]["fixes"], release)
        self.assertIn("### What's New & Fixes", release)
        self.assertIn("[v26.10.23-r1](https://github.com/r/r/releases/tag/v26.10.23-r1)", release)
        self.assertEqual(tg.parse_release(release)["sha"], "f" * 40)

    def test_failed_compare_does_not_claim_there_were_no_fixes(self):
        measured = tg.changes(R2, "r/r", "f" * 40, lambda path: RELEASES if "/releases?" in path else None)
        text = tg.post(R2, "en", **measured)
        self.assertIn("The fix commit list could not be read", text)
        self.assertNotIn("No additional kernel fix commits", text)

    def test_fix_comparison_uses_the_recorded_build_commit_instead_of_the_tag_target(self):
        body = rn.notes(R1, [], "https://run", "r/r") + f"\n<!-- cogan-build-sha: {'d' * 40} -->\n"
        releases = [{"tag_name": R1["RELEASE"], "target_commitish": "e" * 40, "body": body}]
        asked = []

        def api(path):
            asked.append(path)
            return releases if "/releases?" in path else {"commits": []}
        tg.changes(R2, "r/r", "f" * 40, api)
        self.assertIn(f"repos/r/r/compare/{'d' * 40}...{'f' * 40}", asked)

    def test_first_release_is_only_reported_after_reading_the_history(self):
        measured = tg.changes(R1, "r/r", api=lambda path: [])
        text = tg.post(R1, "id", **measured)
        self.assertIn("Rilis pertama varian ini", text)
        self.assertIn("Belum ada rilis pembanding", text)

    def test_summary_section_puts_each_language_in_a_code_block(self):
        text = tg.summary_section({"id": "teks\n", "en": "text\n"})
        self.assertIn("<details open><summary>🇮🇩 Bahasa Indonesia</summary>", text)
        self.assertIn("**📣 Teks Telegram** (salin lewat tombol di pojok kanan atas kotak)\n\n```text\nteks\n```", text)
        self.assertIn("<details><summary>🇬🇧 English</summary>", text)
        self.assertIn("```text\ntext\n```", text)


if __name__ == "__main__":
    unittest.main()

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
        self.assertNotIn("🔧", english)

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
            self.assertIn("Rilis pertama varian ini", (out / "id.txt").read_text())

    def test_summary_section_puts_each_language_in_a_code_block(self):
        text = tg.summary_section({"id": "teks\n", "en": "text\n"})
        self.assertIn("<details open><summary>🇮🇩 Bahasa Indonesia</summary>", text)
        self.assertIn("**📣 Teks Telegram** (salin lewat tombol di pojok kanan atas kotak)\n\n```text\nteks\n```", text)
        self.assertIn("<details><summary>🇬🇧 English</summary>", text)
        self.assertIn("```text\ntext\n```", text)


if __name__ == "__main__":
    unittest.main()

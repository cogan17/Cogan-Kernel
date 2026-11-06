#!/usr/bin/env python3
"""Offline tests for kernel/tidy_release_notes.py: consolidate a published release body's What's New."""
import unittest

from kernel.tidy_release_notes import tidy

VARIANT = """#### CoganSU · {ver}

**🇮🇩 Bahasa Indonesia**

Dibandingkan dengan [v26.10.31-r7](https://x/r7)

**✨ Baru**
- Kernel ACK 6.1.176 → {ver}
- CoganSU diperbarui
- Fitur baru: Disguise

**🔧 Perbaikan**
- perbaiki crash kernel lewat futex (CVE-2026-53163)

**🇬🇧 English**

Compared with [v26.10.31-r7](https://x/r7)

**✨ New**
- ACK kernel 6.1.176 → {ver}
- CoganSU updated
- New features: Disguise

**🔧 Fixes**
- Fix a kernel crash through futex (CVE-2026-53163)

<!-- cogan-build-sha: {sha} -->
"""

BODY = ('<h2 align="center">Cogan v26.11.05-r12</h2>\n\n'
        "<details>\n<summary>✨ <b>What's New & Fixes</b></summary>\n\n"
        + VARIANT.format(ver="6.1.138", sha="a" * 40) + "\n"
        + VARIANT.format(ver="6.1.145", sha="b" * 40) + "\n"
        + VARIANT.format(ver="6.1.176", sha="c" * 40)
        + "\n</details>\n\n<details>\n<summary>📦 <b>Modul pendukung / Modules</b></summary>\n\n- NoMount\n</details>\n")


class TidyTest(unittest.TestCase):
    def setUp(self):
        self.out = tidy(BODY)

    def test_no_per_sublevel_repetition(self):
        whats_new = self.out.split("What's New & Fixes</b></summary>", 1)[1].split("</details>", 1)[0]
        self.assertNotIn("#### ", whats_new)                       # no per-variant headers
        self.assertEqual(whats_new.count("CoganSU diperbarui"), 1)  # each change once
        self.assertEqual(whats_new.count("CoganSU updated"), 1)
        self.assertEqual(whats_new.count("Fix a kernel crash through futex (CVE-2026-53163)"), 1)

    def test_versions_named_once_and_ack_lines_dropped(self):
        self.assertIn("🐧 3 pilihan kernel: 6.1.138, 6.1.145, 6.1.176 (6.1.176 = terbaru)", self.out)
        self.assertIn("🐧 3 kernel choices: 6.1.138, 6.1.145, 6.1.176 (6.1.176 = newest)", self.out)
        self.assertNotIn("Kernel ACK", self.out)                   # version lines are implied by the choices line
        self.assertNotIn("ACK kernel", self.out)
        self.assertEqual(self.out.count("Dibandingkan dengan [v26.10.31-r7](https://x/r7)"), 1)  # baseline once

    def test_other_sections_are_preserved(self):
        self.assertIn("<summary>📦 <b>Modul pendukung / Modules</b></summary>", self.out)
        self.assertIn("- NoMount", self.out)
        self.assertEqual(self.out.count("<details>"), self.out.count("</details>"))

    def test_a_body_without_the_section_is_unchanged(self):
        plain = "## Cogan v26.10.23-r1\n\n- Kernel: `6.1.176`\n\nSHA256: `checksums.txt`.\n"
        self.assertEqual(tidy(plain), plain)


if __name__ == "__main__":
    unittest.main()

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


def _cmp_variant(root, ver, ack, mtk):
    return (f"## {root} · {ver}\n\n"
            f"- Kernel: `{ver}` (ACK `{ack}`)\n"
            f"- Root: {root} main `abc123abc123` + SUSFS v2.3.0 `def456def456`\n"
            "- NoMount: v2.2.0 · Neutron clang 06092026\n"
            "- Fitur / features: SUSFS, BBG, NoMount\n"
            "- Unicode fix: WildKernel `ee68218dc83b`\n"
            f"- KMI Xiaomi 14T Pro (rothko): OK; generation 11; exported GKI 2/2, mtk {mtk}/{mtk}, "
            "xiaomi 455/455 (3 via GKI modules); CRC differs 0 (force-load on)\n\n"
            "<!-- cogan-build-sha: " + "d" * 40 + " -->\n")


COMP_BODY = ("<details>\n<summary>🧩 <b>Komponen & fitur / Components & features</b></summary>\n\n"
             + "\n".join(_cmp_variant(root, ver, ack, mtk)
                         for root in ("KernelSU", "KernelSU Next")
                         for ver, ack, mtk in (("6.1.138", "a-2025-06_r17", "3596"),
                                               ("6.1.176", "a-2026-09_r6", "3705")))
             + "\n</details>\n\n<details>\n<summary>🔏 <b>SHA256</b></summary>\n\n- x\n</details>\n")


class TidyComponentsTest(unittest.TestCase):
    def setUp(self):
        self.out = tidy(COMP_BODY)
        self.sec = self.out.split("Components & features</b></summary>", 1)[1].split("\n</details>", 1)[0]

    def test_one_section_per_root_not_per_sublevel(self):
        self.assertEqual(self.sec.count("## KernelSU\n"), 1)       # KernelSU once, not twice
        self.assertEqual(self.sec.count("## KernelSU Next\n"), 1)
        self.assertEqual(self.sec.count("- Root: "), 2)            # shared line once per root, not per sublevel
        self.assertEqual(self.sec.count("- Kernel: "), 4)          # every sublevel kept
        self.assertIn("· mtk 3596/3596, xiaomi 455/455", self.sec)  # per-sublevel KMI counts on the kernel line
        self.assertEqual(self.sec.count("exported GKI 2/2 (3 via GKI modules)"), 2)  # common KMI once per root

    def test_previous_still_reads_each_root(self):
        import sys
        sys.path.insert(0, "kernel")
        from telegram import parse_release, root_name
        import re
        found = {root_name(parse_release(s)["root"][0]): parse_release(s)
                 for s in re.split(r"(?=^## )", self.out, flags=re.M) if parse_release(s).get("root")}
        self.assertEqual(set(found), {"KernelSU", "KernelSU Next"})
        for p in found.values():
            self.assertEqual(p["kernel"], "6.1.138")              # first sublevel, as the old layout gave
            self.assertEqual(p["susfs"][1], "def456def456")
            self.assertEqual(p["sha"], "d" * 40)

    def test_idempotent(self):
        self.assertEqual(tidy(self.out), self.out)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline tests for kernel/release_notes.py: two languages, phone-test label only when tested."""
import unittest

from kernel import release_notes as rn

ENV = {"RELEASE_NAME": "Cogan-Rothko-ACK v26.10.24-r10", "LINUX_VERSION": "6.1.176",
       "ACK_TAG": "android14-6.1-2026-09_r4", "ROOT_NAME": "KernelSU Next", "ROOT_TAG": "dev-susfs",
       "ROOT_COMMIT": "d21e0a66c887ae4bc75b7c9f83e41761819ec09a", "KSU_VERSION": "33405",
       "SUSFS_VERSION": "v2.3.0", "SUSFS_COMMIT": "c27ebe93c68e953c248b11bb747ef220ea648373",
       "NOMOUNT": "v2.2.0", "NEUTRON": "24102026", "FEATURES": "SUSFS, BBRv3, BBG, NoMount",
       "KMI_COMPAT": "KMI Xiaomi 14T Pro (rothko): OK; CRC differs 0; BSP: generation 11"}
FILES = ["4-NOMOUNT-MODULE_v2.2.0.zip", "1-KERNEL_x.zip", "2-MANAGER_KernelSU-Next_v3.4.2_33405.apk"]


class ReleaseNotesTest(unittest.TestCase):
    def test_untested_build_says_so_in_both_languages(self):
        text = rn.notes(ENV, FILES, "https://run", "cogan17/Cogan-Kernel")
        self.assertIn("**belum diuji di HP**", text)
        self.assertIn("**not tested on the phone yet**", text)
        self.assertNotIn("Diuji owner", text)
        self.assertIn("KernelSU Next dev-susfs `d21e0a66c887` (33405) + SUSFS v2.3.0 `c27ebe93c68e`", text)
        self.assertIn("- KMI Xiaomi 14T Pro (rothko): OK; CRC differs 0\n", text)
        self.assertLess(text.index("1-KERNEL_x.zip"), text.index("4-NOMOUNT"))
        text = rn.notes(ENV, FILES + ["5-SUSFS-MODULE-SIMONPUNK_v2.3.0_27e0a0e4.zip", "6-SUSFS-MODULE-SIDEX15_v1.5.2-CI-89b04b9.zip"],
                        "https://run", "cogan17/Cogan-Kernel")
        self.assertIn("| `5-SUSFS-MODULE-SIMONPUNK_v2.3.0_27e0a0e4.zip` | Modul SUSFS simonpunk (alat `ksu_susfs`, commit SUSFS "
                      "yang sama dengan kernel). Pasang **salah satu**: 5 atau 6 |", text)
        self.assertIn("| `6-SUSFS-MODULE-SIDEX15_v1.5.2-CI-89b04b9.zip` | Modul SUSFS sidex15 dengan WebUI", text)

    def test_tested_label_and_note(self):
        text = rn.notes(ENV, FILES, "https://run", "cogan17/Cogan-Kernel", tested=True, note="baris 1\\nline 2")
        self.assertIn("**Diuji owner di Xiaomi 14T Pro.**", text)
        self.assertIn("> baris 1\n> line 2", text)

    def test_unicode_fix_line_only_when_built_with_it(self):
        line = "- Unicode fix: WildKernel `fa76c90e2cb2`"
        self.assertNotIn("Unicode fix", rn.notes(ENV, FILES, "https://run", "cogan17/Cogan-Kernel"))
        self.assertNotIn("Unicode fix", rn.notes({**ENV, "UNICODE_FIX": "-"}, FILES, "https://run", "cogan17/Cogan-Kernel"))
        text = rn.notes({**ENV, "UNICODE_FIX": "fa76c90e2cb284e6ce22b0b008ad4dd19820dbb1"}, FILES, "https://run",
                        "cogan17/Cogan-Kernel")
        self.assertIn(line, text)


if __name__ == "__main__":
    unittest.main()

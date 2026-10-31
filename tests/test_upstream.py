#!/usr/bin/env python3
"""Offline tests for kernel/upstream.py: upstream commits in plain words, never hashes (owner 2026-10-31)."""
import unittest

from kernel import upstream as up

# The real ranges of r7 (v26.10.29-r6 → v26.10.31-r7), as new titles after a force-push of the fork.
KSUN_R7 = [
    "fix(kernel): align SELinux hide policy parsing (https://github.com/tiann/KernelSU/pull/3936)",
    "kernel: Balance file references when reopening wrapped files (https://github.com/tiann/KernelSU/pull/3958)",
    "kernel: Remove noisy logs from critical and frequent paths (https://github.com/tiann/KernelSU/pull/3960)",
    "kernel: remove useless code (https://github.com/tiann/KernelSU/pull/3945)",
    "kernel: selinux_hide: Even out attr/current timing",
    "kernel: susfs (LKM): sus_mount: cover the mounts a magic-mount store marks",
    "kernel: susfs (LKM): or_entry: do not putname twice on 5.10",
    "userspace: Update waitsys to fix crash",
]


class UpstreamTest(unittest.TestCase):
    def test_r7_in_plain_indonesian_and_english(self):
        self.assertEqual(up.describe("SUSFS", ["KernelSU: Fix compiler error"], "id", head="SUSFS v2.3.0 diperbarui"),
                         ("SUSFS v2.3.0 diperbarui", "SUSFS: memperbaiki error saat compile"))
        self.assertEqual(up.describe("BakaSU", ["ksud, ksuinit: block vklp_smaps_rollup"], "id"),
                         ("BakaSU diperbarui: meningkatkan anti deteksi lewat peta memori", None))
        self.assertEqual(up.describe("KernelSU Next", KSUN_R7, "id", kernel_only=True),
                         ("KernelSU Next diperbarui: meningkatkan penyembunyian SELinux, mengurangi log yang tidak perlu "
                          "dan 1 perubahan lain", "KernelSU Next: memperbaiki penyembunyian SELinux"))
        self.assertEqual(up.describe("KernelSU Next", KSUN_R7, "en", kernel_only=True),
                         ("KernelSU Next updated: improves SELinux hiding, reduces unnecessary logs and 1 other change",
                          "KernelSU Next: fixes SELinux hiding"))

    def test_what_never_reaches_this_kernel_is_left_out(self):
        self.assertEqual(up.relevant(KSUN_R7, kernel_only=True), [
            "fix(kernel): align SELinux hide policy parsing",
            "kernel: Balance file references when reopening wrapped files",
            "kernel: Remove noisy logs from critical and frequent paths",
            "kernel: selinux_hide: Even out attr/current timing"])
        noise = ["manager: update translations from Weblate (#636)", "deps: Update Rust crate libc to v0.2.191 (#627)",
                 "Update README.md", "kernel: compat: samsung_kdp: Fix build on kernels >= 6.12"]
        self.assertEqual(up.relevant(noise), [])
        self.assertEqual(up.relevant(["kernel: Rebase susfs patches onto android14-6.1.176"]),
                         ["kernel: Rebase susfs patches onto android14-6.1.176"])

    def test_unreadable_or_minor_ranges_still_say_what_was_updated(self):
        self.assertEqual(up.describe("BakaSU", None, "id"), ("BakaSU diperbarui ke versi terbaru dari pengembang", None))
        self.assertEqual(up.describe("BakaSU", ["Update README.md"], "en"), ("BakaSU updated (minor changes)", None))
        self.assertEqual(up.describe("BakaSU", ["kernel: limit code generators on CONFIG_KSU (#639)",
                                                "kernel: something else"], "en"), ("BakaSU updated (2 technical changes)", None))
        self.assertEqual(up.describe("SUSFS", None, "en", head="SUSFS v2.2.0 → v2.3.0"), ("SUSFS v2.2.0 → v2.3.0", None))

    def test_long_ranges_stay_short(self):
        titles = ["kernel: Fix another selinux leak", "kernel: SUS_MOUNT: Fix race condition in clone_mnt()",
                  "kernel: SUS_KSTAT: fix f_flags left zeroed", "kernel: Fix compiling issues", "susfs: Add uname spoof",
                  "kernel: optimize fast path", "KernelSU: Sync with the official KernelSU main repo",
                  "manager: new theme", "kernel: add module preinit"]
        line, fixes = up.describe("SUSFS", titles, "id")
        self.assertEqual(line, "SUSFS diperbarui: meningkatkan penyamaran info sistem, meningkatkan performa, "
                               "meningkatkan dukungan modul dan 3 perubahan lain")
        self.assertEqual(fixes, "SUSFS: memperbaiki penyembunyian SELinux, penyembunyian mount dan penyamaran info file")


if __name__ == "__main__":
    unittest.main()

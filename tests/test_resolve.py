#!/usr/bin/env python3
"""Offline tests for kernel/resolve.py: newest ACK release per sublevel, tags, hooks, KSUN manager."""
import unittest

from kernel import resolve as r

REFS = {
    "refs/tags/android14-6.1-2025-05_r9": "a" * 40,  # before the phone's own release: never picked
    "refs/tags/android14-6.1-2025-06_r11": "b" * 40,
    "refs/tags/android14-6.1-2025-09_r36": "c" * 40,
    "refs/tags/android14-6.1-2026-09_r4": "d" * 40,
    "refs/tags/android14-6.1-2026-09_r2": "e" * 40,
    "refs/tags/android14-6.1-lts-x": "f" * 40,
}
SUBLEVELS = {"android14-6.1-2025-06_r11": 138, "android14-6.1-2025-09_r36": 145,
             "android14-6.1-2026-09_r4": 176, "android14-6.1-2026-09_r2": 176}


class AckTest(unittest.TestCase):
    def setUp(self):
        self.releases = r.ack_releases(REFS)
        self.asked = []

    def sublevel(self, tag):
        self.asked.append(tag)
        return SUBLEVELS[tag]

    def test_releases_since_the_phone_newest_first(self):
        self.assertEqual([tag for tag, _ in self.releases],
                         ["android14-6.1-2026-09_r4", "android14-6.1-2026-09_r2",
                          "android14-6.1-2025-09_r36", "android14-6.1-2025-06_r11"])

    def test_lts_is_the_newest_release(self):
        self.assertEqual(r.pick_ack(self.releases, "lts", self.sublevel), [("android14-6.1-2026-09_r4", "d" * 40, 176)])
        self.assertEqual(self.asked, ["android14-6.1-2026-09_r4"])

    def test_a_number_is_the_newest_release_of_that_sublevel(self):
        self.assertEqual(r.pick_ack(self.releases, "176", self.sublevel), [("android14-6.1-2026-09_r4", "d" * 40, 176)])
        self.assertEqual(r.pick_ack(self.releases, "138, 145", self.sublevel),
                         [("android14-6.1-2025-06_r11", "b" * 40, 138), ("android14-6.1-2025-09_r36", "c" * 40, 145)])

    def test_semua_is_every_sublevel_once(self):
        self.assertEqual([sub for _, _, sub in r.pick_ack(self.releases, "semua", self.sublevel)], [138, 145, 176])

    def test_unknown_sublevel_or_format_is_refused(self):
        with self.assertRaisesRegex(ValueError, "6.1.150"):
            r.pick_ack(self.releases, "150", self.sublevel)
        with self.assertRaisesRegex(ValueError, "lts, a number"):
            r.pick_ack(self.releases, "6.1.176", self.sublevel)


class TagsAndHooksTest(unittest.TestCase):
    def test_newest_release_puts_the_final_after_its_candidates(self):
        refs = {"refs/tags/v4.2.0-rc3": "a", "refs/tags/v4.1.0": "b", "refs/tags/v4.2.0": "c", "refs/tags/x": "d"}
        self.assertEqual(r.newest_tag(refs), ("v4.2.0", "c"))
        del refs["refs/tags/v4.2.0"]
        self.assertEqual(r.newest_tag(refs), ("v4.2.0-rc3", "a"))
        self.assertEqual(r.newest_tag(refs, r.STABLE), ("v4.1.0", "b"))

    def test_hooks_the_susfs_patch_calls(self):
        patch = "+\tmy_setprocattr(a);\n context my_write_access(b);\n+ksu_setup_preinit_file();\n"
        self.assertEqual(r.needed_hooks(patch), ["my_setprocattr", "ksu_setup_preinit_file"])

    def test_hook_state_reads_definitions_only(self):
        self.assertEqual(r.hook_state("static int my_write_context(void)\n\tmy_write_context();\n"), "static")
        self.assertEqual(r.hook_state("int my_write_context(void)\nstatic int my_write_context(void);\n"), "global")
        self.assertEqual(r.hook_state("\tmy_write_context();\n"), "missing")


class KsunManagerTest(unittest.TestCase):
    def api(self, runs, artifacts):
        def call(path):
            return {"workflow_runs": runs} if "/runs?" in path else {"artifacts": artifacts}
        return call

    def test_the_ci_run_of_the_base_commit(self):
        artifacts = [{"name": "manager", "id": 1, "expired": False}, {"name": "manager-spoofed", "id": 2, "expired": False}]
        found = r.ksun_manager("b" * 40, self.api([{"id": 9, "html_url": "u"}], artifacts))
        self.assertEqual(found, {"run": 9, "url": "u", "manager": 1, "spoofed": 2})

    def test_no_or_expired_build_means_wait(self):
        expired = [{"name": "manager", "id": 1, "expired": True}]
        for runs in ([], [{"id": 9, "html_url": "u"}]):
            with self.assertRaises(r.Wait) as caught:
                r.ksun_manager("b" * 40, self.api(runs, expired))
            self.assertIn("bbbbbbbbbbbb", caught.exception.id_text)


class UnicodeFixTest(unittest.TestCase):
    def test_newest_wildkernel_patch(self):
        asked = []

        def ls_remote(url, *patterns):
            asked.append((url, patterns))
            return {"refs/heads/main": "9" * 40}
        self.assertEqual(r.unicode_fix(ls_remote), {"repo": "https://github.com/WildKernels/kernel_patches",
                                                    "commit": "9" * 40, "path": "common/unicode_bypass_fix_6.1+.patch"})
        self.assertEqual(asked, [("https://github.com/WildKernels/kernel_patches", ("refs/heads/main",))])

    def test_the_box_is_off_unless_asked(self):
        import inspect
        self.assertFalse(inspect.signature(r.resolve).parameters["unicode"].default)


if __name__ == "__main__":
    unittest.main()

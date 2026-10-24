#!/usr/bin/env python3
"""Offline tests for kernel/resolve.py: newest ACK release per sublevel, tags, hooks, KSUN manager."""
import subprocess
import tempfile
import unittest
from pathlib import Path

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
        # One Makefile per month: 2026-09_r2 shares the sublevel of 2026-09_r4 and is not asked.
        self.assertEqual(self.asked, ["android14-6.1-2026-09_r4", "android14-6.1-2025-09_r36",
                                      "android14-6.1-2025-06_r11"])

    def test_http_waits_and_retries_on_too_many_requests(self):
        import io
        import urllib.error
        from unittest import mock
        calls, slept = [], []

        def urlopen(request, timeout):
            calls.append(request.full_url)
            if len(calls) < 3:
                raise urllib.error.HTTPError(request.full_url, 429, "Too Many Requests",
                                             {"Retry-After": "2"} if len(calls) == 1 else {}, io.BytesIO())
            return io.BytesIO(b"ok")
        with mock.patch.object(r.urllib.request, "urlopen", urlopen):
            self.assertEqual(r.http("https://example.invalid/x", sleep=slept.append), b"ok")
        self.assertEqual((len(calls), slept), (3, [2, 30]))
        with mock.patch.object(r.urllib.request, "urlopen", urlopen):
            calls.clear()
            with self.assertRaises(urllib.error.HTTPError):
                r.http("https://example.invalid/x", attempts=1, sleep=slept.append)

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

    def test_bakasu_ready_follows_a_macro_name(self):
        # BakaSU main, 24 Oct 2026: the hook SUSFS calls is the macro name of a global function.
        with tempfile.TemporaryDirectory() as tmp:
            git = lambda *args: subprocess.run(["git", "-C", tmp, *args], check=True, capture_output=True, text=True)
            git("init", "-q")
            git("config", "user.name", "t"); git("config", "user.email", "t@t"); git("config", "commit.gpgsign", "false")
            patch = Path(tmp, r.SUSFS_PATCH)
            patch.parent.mkdir(parents=True)
            patch.write_text("+extern int my_setprocattr(const char *name, void *value, size_t size);\n"
                             "+\t\treturn my_setprocattr(name, value, size);\n")
            git("add", "-A"); git("commit", "-qm", "susfs"); git("branch", "susfs")
            git("rm", "-rq", "kernel_patches")
            hide = Path(tmp, "kernel/feature/selinux_hide.c")
            hide.parent.mkdir(parents=True)
            hide.write_text("#ifdef KSU_COMPAT_HAS_SUSFS_FEATURE_SELINUX_HIDE\n"
                            "    #define ksu_handle_selinux_setprocattr my_setprocattr\n#endif\n"
                            "int __nocfi ksu_handle_selinux_setprocattr(const char *name, void *value, size_t size)\n{\n}\n")
            git("add", "-A"); git("commit", "-qm", "bakasu"); git("branch", "bakasu")
            self.assertIsNone(r.bakasu_ready(tmp, "bakasu", "susfs"))
            hide.write_text(hide.read_text().replace("int __nocfi", "static int __nocfi"))
            git("commit", "-qam", "static"); git("branch", "static")
            self.assertEqual(r.bakasu_ready(tmp, "static", "susfs"), "`my_setprocattr` static")
            hide.write_text("int ksu_handle_selinux_setprocattr(void)\n{\n}\n")
            git("commit", "-qam", "no macro"); git("branch", "plain")
            self.assertEqual(r.bakasu_ready(tmp, "plain", "susfs"), "`my_setprocattr` missing")


class KsunManagerTest(unittest.TestCase):
    def api(self, runs, artifacts):
        def call(path):
            return {"workflow_runs": runs} if "/runs?" in path else {"artifacts": artifacts}
        return call

    def test_the_ci_run_of_the_base_commit(self):
        artifacts = [{"name": "manager", "id": 1, "expired": False}, {"name": "manager-spoofed", "id": 2, "expired": False}]
        found = r.ksun_manager("b" * 40, self.api([{"id": 9, "html_url": "u"}], artifacts))
        self.assertEqual(found, {"repo": "KernelSU-Next/KernelSU-Next", "run": 9, "url": "u", "manager": 1, "spoofed": 2})

    def test_no_or_expired_build_means_wait(self):
        expired = [{"name": "manager", "id": 1, "expired": True}]
        for runs in ([], [{"id": 9, "html_url": "u"}]):
            with self.assertRaises(r.Wait) as caught:
                r.ksun_manager("b" * 40, self.api(runs, expired))
            self.assertIn("bbbbbbbbbbbb", caught.exception.id_text)


class BakasuMainTest(unittest.TestCase):
    # Owner 2026-10-24 (Baka-SU/BakaSU#214): BakaSU main before its next release.
    def test_newest_successful_main_build_and_its_manager(self):
        asked = []

        def api(path):
            asked.append(path)
            if "/runs?" in path:
                return {"workflow_runs": [{"id": 7, "html_url": "u", "head_sha": "c" * 40}]}
            return {"artifacts": [{"name": "Manager-release", "id": 3, "expired": False},
                                  {"name": "Spoofed-Manager-release", "id": 4, "expired": False},
                                  {"name": "Manager-debug", "id": 5, "expired": False}]}
        commit, manager = r.bakasu_main(api)
        self.assertEqual(commit, "c" * 40)
        self.assertEqual(manager, {"repo": "Baka-SU/BakaSU", "run": 7, "url": "u", "manager": 3, "spoofed": 4})
        self.assertIn("build-manager.yml/runs?branch=main&event=push&per_page=5", asked[0])

    def test_a_run_still_building_its_manager_is_skipped(self):
        # The newest run has no manager yet; the one before it has (its Telegram job may still run).
        runs = [{"id": 8, "html_url": "u8", "head_sha": "d" * 40, "status": "in_progress"},
                {"id": 7, "html_url": "u7", "head_sha": "c" * 40, "status": "in_progress"}]

        def api(path):
            if "/runs?" in path:
                return {"workflow_runs": runs}
            return {"artifacts": [] if "/runs/8/" in path else [{"name": "Manager-release", "id": 3, "expired": False}]}
        self.assertEqual(r.bakasu_main(api), ("c" * 40, {"repo": "Baka-SU/BakaSU", "run": 7, "url": "u7", "manager": 3}))

    def test_no_main_build_means_wait(self):
        for runs, artifacts in (([], []), ([{"id": 7, "html_url": "u", "head_sha": "c" * 40}],
                                           [{"name": "Manager-release", "id": 3, "expired": True}])):
            api = lambda path: {"workflow_runs": runs} if "/runs?" in path else {"artifacts": artifacts}
            with self.assertRaises(r.Wait) as caught:
                r.bakasu_main(api)
            self.assertIn("BakaSU di main", caught.exception.id_text)


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

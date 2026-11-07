#!/usr/bin/env python3
"""kernel/cogansu_auto.py (owner 2026-11-07: "buat jadi satu langkah pakai PAT"): the Builder runs Build CoganSU
on cogan17/CoganSU when CoganSU lags KernelSU, waits for it, and resolves CoganSU again."""
import datetime
import json
import tempfile
import unittest
from pathlib import Path

from kernel import cogansu_auto as a

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/build-kernel.yml").read_text()
T0 = datetime.datetime(2026, 11, 7, 1, 0, tzinfo=datetime.timezone.utc)


class FakeApi:
    def __init__(self, dispatch=204, conclusion="success", polls=2, listed=True):
        self.calls, self.dispatch, self.conclusion, self.polls, self.listed = [], dispatch, conclusion, polls, listed

    def __call__(self, method, path, token, body=None):
        self.calls.append((method, path, body))
        if method == "POST":
            return self.dispatch, None
        if "/runs?" in path:
            runs = [{"id": 1, "created_at": "2026-11-06T23:00:00Z", "status": "completed", "html_url": "https://old"}]
            if self.listed:
                runs.append({"id": 7, "created_at": "2026-11-07T01:00:05Z", "status": "queued", "html_url": "https://run/7"})
            return 200, {"workflow_runs": runs}
        self.polls -= 1
        done = self.polls <= 0
        return 200, {"id": 7, "status": "completed" if done else "in_progress",
                     "conclusion": self.conclusion if done else None, "html_url": "https://run/7"}


class NeedTest(unittest.TestCase):
    def test_build_first_wait_needs_a_build(self):
        snap = {"root": "CSU", "wait": {"id": "Jalankan Build CoganSU …", "en": "Run Build CoganSU …", "kind": "build-first"}}
        self.assertEqual(a.need(snap), ("Jalankan Build CoganSU …", "Run Build CoganSU …"))

    def test_a_real_wait_does_not(self):
        self.assertIsNone(a.need({"root": "CSU", "wait": {"id": "Tunggu simonpunk", "en": "Wait for simonpunk"}}))

    def test_a_release_behind_kernelsu_main_needs_a_build(self):
        snap = {"root_source": {"tag": "v26.11.07-r6", "kernelsu_main": "d" * 40, "kernelsu_in_release": False}}
        self.assertIn("belum memuat KernelSU main `dddddddddddd`", a.need(snap)[0])
        snap["root_source"]["kernelsu_in_release"] = True
        self.assertIsNone(a.need(snap))

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "CSU.json")
            path.write_text(json.dumps({"root_source": {"kernelsu_main": "d" * 40, "kernelsu_in_release": True}}))
            self.assertEqual(a.main(["need", str(path)]), 1)
            path.write_text(json.dumps({"root_source": {"kernelsu_main": "d" * 40, "kernelsu_in_release": False}}))
            self.assertEqual(a.main(["need", str(path)]), 0)


class BuildTest(unittest.TestCase):
    def build(self, api, **kwargs):
        return a.build("tok", "Release", api=api, sleep=lambda s: None, now=lambda: T0, **kwargs)

    def test_dispatches_on_main_and_waits_for_its_own_run(self):
        api = FakeApi()
        run = self.build(api)
        self.assertEqual(run["id"], 7)
        method, path, body = api.calls[0]
        self.assertEqual((method, path), ("POST", "repos/cogan17/CoganSU/actions/workflows/build-cogansu.yml/dispatches"))
        self.assertEqual(body, {"ref": "main", "inputs": {"release_type": "Release", "build_revision": ""}})
        self.assertTrue(any(p == "repos/cogan17/CoganSU/actions/runs/7" for _, p, _ in api.calls))

    def test_a_failed_build_stops_with_its_link(self):
        with self.assertRaises(a.Stop) as caught:
            self.build(FakeApi(conclusion="failure"))
        self.assertIn("Build CoganSU gagal (failure): https://run/7", caught.exception.id_text)

    def test_a_refused_token_names_the_permission(self):
        with self.assertRaises(a.Stop) as caught:
            self.build(FakeApi(dispatch=403))
        self.assertIn("Actions: Read and write", caught.exception.id_text)
        self.assertNotIn("Tunggu", caught.exception.id_text)

    def test_a_run_that_never_shows_up_stops(self):
        with self.assertRaises(a.Stop):
            self.build(FakeApi(listed=False))

    def test_a_run_that_does_not_finish_stops(self):
        with self.assertRaises(a.Stop) as caught:
            self.build(FakeApi(polls=10**6), timeout=90, every=30)
        self.assertIn("belum selesai setelah 1 menit", caught.exception.id_text)

    def test_without_token_the_summary_says_how(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = Path(tmp, "summary.md")
            env = dict(a.os.environ)
            a.os.environ.pop("COGANSU_TOKEN", None)
            try:
                self.assertEqual(a.main(["build", "--release-type", "CI", "--summary", str(summary)]), 1)
            finally:
                a.os.environ.clear()
                a.os.environ.update(env)
            self.assertIn("Secret COGANSU_TOKEN belum ada", summary.read_text())
            self.assertIn("docs/cogansu-token.md", summary.read_text())

    def test_kernel_release_types_map_to_cogansu_releases(self):
        self.assertEqual(a.RELEASE_TYPES, {"CI": "Pre-Release", "Pre-Release": "Pre-Release", "Release": "Release"})


class WorkflowTest(unittest.TestCase):
    def test_builder_runs_build_cogansu_then_resolves_again(self):
        self.assertIn("COGANSU_TOKEN: ${{ secrets.COGANSU_TOKEN }}", WORKFLOW)
        self.assertIn('python3 kernel/cogansu_auto.py need "snapshots/CSU.json"', WORKFLOW)
        self.assertIn('python3 kernel/cogansu_auto.py build --release-type "$RELEASE_TYPE"', WORKFLOW)
        self.assertIn("python3 kernel/resolve.py --root CSU", WORKFLOW)
        self.assertTrue((ROOT / "docs/cogansu-token.md").is_file())
        self.assertTrue((ROOT / "docs/cogansu-token.en.md").is_file())


if __name__ == "__main__":
    unittest.main()

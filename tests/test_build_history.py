"""Permanent Markdown records survive Actions deletion and select proven results per root."""
import base64
import copy
import json
import tempfile
import unittest
from pathlib import Path

from kernel import build_history as h

REPO = "cogan17/Cogan-Kernel"
SOURCE = "a" * 40
ACK = {"tag": "android14-6.1-2026-09_r5", "sublevel": 176, "commit": "b" * 40}
SNAP = {"root": "KSUN", "ack": [ACK], "root_source": {"commit": SOURCE}, "susfs": {"commit": "c" * 40},
        "nomount": {"tag": "v2.2.0"}, "bbg": {"commit": "d" * 40}, "unicode": {"commit": "e" * 40}}


def record(run_id=11, root="KSUN", status="ok", attempt=1, branch="main"):
    return {"schema": 1, "id": run_id, "attempt": attempt, "number": run_id, "date": "2026-10-26T07:16:00Z",
            "url": f"https://github.com/{REPO}/actions/runs/{run_id}", "branch": branch, "sha": "f" * 40,
            "builds": [{"root": root, "sublevel": 176, "status": status, "snap": {**copy.deepcopy(SNAP), "root": root}, "env": {}}]}


class HistoryTest(unittest.TestCase):
    def test_markdown_is_readable_and_preserves_metadata(self):
        value = record()
        text = h.markdown(value)
        self.assertIn("2026-10-26 14:16 WIB", text)
        self.assertIn("| KernelSU Next | 6.1.176 | ✅ Build + KMI", text)
        self.assertEqual(h.parse(text), value)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / h.filename(value)).write_text(text)
            (folder / "README.md").write_text("Guide; not a Builder record")
            self.assertEqual(h.load(folder), [value])

    def test_latest_per_root_ignores_failed_waiting_and_other_branches(self):
        values = [record(), record(12, "BSU"), record(13, status="failed"), record(14, "BSU", "wait"),
                  record(15, branch="fix/test")]
        latest = h.latest(values, REPO)
        self.assertEqual({key: v["run_id"] for key, v in latest.items()}, {"KSUN": 11, "BSU": 12})
        self.assertIn("/kernel/history/run-11-1.md", latest["KSUN"]["record_url"])

    def test_reruns_are_kept_separate_and_a_failure_cannot_erase_a_success(self):
        values = [record(), record(attempt=2, status="failed")]
        self.assertTrue(h.latest(values, REPO)["KSUN"]["record_url"].endswith("run-11-1.md"))
        values.append(record(attempt=3))
        self.assertTrue(h.latest(values, REPO)["KSUN"]["record_url"].endswith("run-11-3.md"))

    def test_only_successful_sublevels_enter_the_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            info, snapshots = work / "info", work / "snapshots"
            snapshots.mkdir()
            older = {"tag": "android14-6.1-2025-09_r36", "sublevel": 145}
            snap = {**SNAP, "ack": [older, ACK]}
            (snapshots / "KSUN.json").write_text(json.dumps(snap))
            folder = info / "build-info-KSUN-176"
            folder.mkdir(parents=True)
            env = {"ZIP_SHA256": "1" * 64, "ROOT_COMMIT": SOURCE, "ACK_TAG": ACK["tag"], "NOMOUNT": "-", "BBG_COMMIT": "-", "UNICODE_FIX": "-"}
            (folder / "build.env").write_text("\n".join(f"{k}={v}" for k, v in env.items()))
            run = {"id": 11, "run_number": 1, "created_at": "2026-10-26T07:16:00Z", "head_sha": "f" * 40,
                   "html_url": "https://run/11", "head_branch": "main", "path": ".github/workflows/build-kernel.yml"}
            value = h.collect(run, info, snapshots)
            self.assertEqual([b["status"] for b in value["builds"]], ["failed", "ok"])
            latest = h.latest([value], REPO)["KSUN"]["snap"]
            self.assertEqual(latest["ack"], [ACK])
            for disabled in ("nomount", "bbg", "unicode"):
                self.assertNotIn(disabled, latest)
            env["ROOT_COMMIT"] = "0" * 40
            (folder / "build.env").write_text("\n".join(f"{k}={v}" for k, v in env.items()))
            with self.assertRaisesRegex(ValueError, "Snapshot and build info differ"):
                h.collect(run, info, snapshots)

    def test_merge_retains_success_and_other_results(self):
        old = record()
        old["builds"] += record(root="BSU")["builds"]
        result = h.merge(old, record(status="failed"))
        self.assertEqual({b["root"]: b["status"] for b in result["builds"]}, {"KSUN": "ok", "BSU": "ok"})
        with self.assertRaises(ValueError):
            h.merge(old, record(12))

    def test_persist_one_file_with_owner_identity_and_no_duplicate_commit(self):
        files, writes = {}, []

        def api(path, payload=None):
            if payload is None:
                key = path.split("?")[0]
                if key not in files:
                    raise RuntimeError("gh: Not Found (HTTP 404)")
                return files[key]
            writes.append(payload)
            files[path] = {"content": payload["content"], "sha": "s" * 40}
            return {}

        self.assertTrue(h.persist(REPO, record(), api))
        self.assertFalse(h.persist(REPO, record(), api))
        self.assertEqual(len(writes), 1)
        payload = writes[0]
        self.assertEqual(payload["author"], h.IDENTITY)
        self.assertEqual(payload["committer"], h.IDENTITY)
        self.assertEqual(payload["branch"], "main")
        self.assertTrue(next(iter(files)).endswith("kernel/history/run-11-1.md"))
        self.assertEqual(h.parse(base64.b64decode(payload["content"]).decode()), record())

    def test_conflict_rereads_and_merges_other_root(self):
        remote = record()
        writes = []

        def api(path, payload=None):
            if payload is None:
                return {"content": base64.b64encode(h.markdown(remote).encode()).decode(), "sha": str(len(writes))}
            writes.append(payload)
            if len(writes) == 1:
                remote["builds"] += record(root="BSU")["builds"]
                raise RuntimeError("gh: conflict (HTTP 409)")
            return {}

        new = record(status="failed")
        new["note"] = "Additional retained evidence"
        self.assertTrue(h.persist(REPO, new, api))
        self.assertEqual(len(writes), 2)
        self.assertEqual(writes[1]["sha"], "1")
        saved = h.parse(base64.b64decode(writes[1]["content"]).decode())
        self.assertEqual({b["root"]: b["status"] for b in saved["builds"]}, {"KSUN": "ok", "BSU": "ok"})

    def test_permission_failure_is_reported_without_retrying(self):
        calls = []

        def api(path, payload=None):
            calls.append(path)
            raise RuntimeError("gh: Forbidden (HTTP 403)")

        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            h.persist(REPO, record(), api)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()

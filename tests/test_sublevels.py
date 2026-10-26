#!/usr/bin/env python3
"""Offline tests for kernel/sublevels.py: check for a new release, record of Builder runs, README table."""
import json
import tempfile
import unittest
from pathlib import Path

from kernel import sublevels as sl

TAG = "android14-6.1-2026-09_r4"


class SublevelsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def left(self, root, sublevel, status, tag=TAG):
        folder = self.base / "info" / f"build-info-{root}-{sublevel}"
        folder.mkdir(parents=True)
        if status == "ok":
            (folder / "build.env").write_text(f"ACK_TAG={tag}\nZIP_SHA256={'a' * 64}\n")
        elif status == "tunggu":
            (folder / "wait.json").write_text('{"id": "Tunggu simonpunk.", "en": "Wait for simonpunk."}')
        else:
            (folder / "stage.txt").write_text("KMI gate\n")

    def test_record_a_builder_run(self):
        record = {"176": {"tag": TAG, "note": {"id": "r1 diuji di HP", "en": "r1 tested"}},
                  "172": {"tag": "android14-6.1-2026-06_r14", "pendahulu": True},
                  "141": {}}
        self.left("KSUN", 176, "ok")
        self.left("KSUN", 172, "ok", "android14-6.1-2026-06_r14")
        self.left("KSUN", 141, "gagal")
        self.left("BSU", 176, "tunggu")
        snapshots = self.base / "snapshots"
        snapshots.mkdir()
        (snapshots / "KSUN.json").write_text(json.dumps({"ack": [{"tag": "android14-6.1-2025-07_r13", "sublevel": 141}]}))
        changed = sl.record_run(record, self.base / "info", "42", sl.snapshot_tags(snapshots))
        self.assertIn(("141", "KernelSU Next", "gagal"), changed)
        self.assertEqual(record["176"]["KSUN"], {"status": "ok", "run": 42})
        self.assertEqual(record["176"]["BSU"], {"status": "tunggu", "run": 42,
                                                "wait": {"id": "Tunggu simonpunk.", "en": "Wait for simonpunk."}})
        self.assertEqual(record["176"]["note"]["id"], "r1 diuji di HP")
        self.assertNotIn("pendahulu", record["172"])  # proven here now
        self.assertEqual(record["141"], {"tag": "android14-6.1-2025-07_r13", "KSUN": {"status": "gagal", "run": 42}})

    def test_newer_release_of_a_sublevel_replaces_old_results(self):
        record = {"176": {"tag": "old", "KSUN": {"status": "ok", "run": 1}, "note": {"id": "n", "en": "n"}}}
        self.left("KSUN", 176, "gagal")
        sl.record_run(record, self.base / "info", "7", {"176": TAG})
        self.assertEqual(record["176"], {"tag": TAG, "note": {"id": "n", "en": "n"}, "KSUN": {"status": "gagal", "run": 7}})

    def test_readme_table_lists_supported_sublevels_only(self):
        record = {"176": {"tag": TAG, "KSUN": {"status": "ok", "run": 9}, "note": {"id": "r1 diuji di HP", "en": "r1 tested"}},
                  "141": {"tag": "android14-6.1-2025-07_r13", "KSUN": {"status": "gagal", "run": 9}},
                  "180": {"tag": "android14-6.1-2026-12_r1", "dicoba": "2026-12-01"},
                  "162": {"tag": "android14-6.1-2026-03_r24", "pendahulu": True, "KSUN": {"status": "gagal", "run": 9}},
                  "145": {"tag": "android14-6.1-2025-09_r36", "pendahulu": True,
                          "KSUN": {"status": "tunggu", "run": 9, "wait": {"id": "Tunggu simonpunk.", "en": "Wait."}}},
                  "138": {"tag": "android14-6.1-2025-06_r11", "pendahulu": True}}
        text = sl.table(record, "id")
        self.assertIn("| **176** (`lts`) | `2026-09_r4` | ✅ KernelSU Next: [build + gate KMI]"
                      "(https://github.com/cogan17/Cogan-Kernel/actions/runs/9) · r1 diuji di HP |", text)
        self.assertIn("| 138 | `2025-06_r11` | 🧪 lolos build + gate KMI di repo pendahulu |", text)
        # The newest result here decides: waiting for upstream is listed, a failure here is not.
        self.assertIn("| 145 | `2025-09_r36` | ⏳ KernelSU Next: [Tunggu simonpunk]"
                      "(https://github.com/cogan17/Cogan-Kernel/actions/runs/9) |", text)
        self.assertNotIn("162", text)
        self.assertNotIn("141", text)
        self.assertNotIn("180", text)
        self.assertIn("| 138 | `2025-06_r11` | 🧪 passed build + KMI gate in the predecessor repository |",
                      sl.table(record, "en"))

    def test_readmes_are_rewritten_between_the_markers(self):
        readme = self.base / "README.md"
        readme.write_text(f"intro\n{sl.START}\nold table\n{sl.END}\nafter\n")
        record = {"176": {"tag": TAG, "KSUN": {"status": "ok", "run": 9}}}
        self.assertEqual(sl.write_readmes(record, {"id": readme}), ["README.md"])
        text = readme.read_text()
        self.assertTrue(text.startswith(f"intro\n{sl.START}\n| Sublevel | Rilis ACK | Status |"))
        self.assertTrue(text.endswith(f"{sl.END}\nafter\n"))
        self.assertNotIn("old table", text)
        self.assertEqual(sl.write_readmes(record, {"id": readme}), [])  # nothing to change

    def test_repository_record_matches_the_readme(self):
        record = sl.load()
        for lang, path in sl.READMES.items():
            text = path.read_text()
            self.assertIn(sl.table(record, lang), text)


if __name__ == "__main__":
    unittest.main()

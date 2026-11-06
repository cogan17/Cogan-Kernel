#!/usr/bin/env python3
"""Pilih sumber (owner 2026-11-06): Stabil (terakhir berhasil) takes every component exactly from the last good
build of a root manager in kernel/history/, so it builds again where the newest versions still wait."""
import io
import json
import re
import tempfile
import unittest
import urllib.error
from pathlib import Path

from kernel import build_history as bh
from kernel import last_good as lg
from kernel import release_notes as rn
from kernel import telegram as tg

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/build-kernel.yml"
BUILD = (ROOT / "kernel/build.sh").read_text()


def snap(root, sublevel, commit, susfs=True, **features):
    found = {"root": root, "susfs_box": susfs, "ack": [{"tag": f"android14-6.1-x_r{sublevel}", "commit": "a" * 40, "sublevel": sublevel}],
             "root_source": {"repo": "r", "branch": "main", "commit": commit},
             "manager": {"kind": "ci", "repo": "tiann/KernelSU", "run": 1, "url": "u", "manager": 11},
             "susfs_sidex": {"repo": "sidex15/susfs4ksu-module", "artifact": 22},
             "nomount": {"tag": "v2.2.0"}, "bbg": {"commit": "b" * 40}, "anykernel": {"commit": "c" * 40},
             "neutron": {"tag": "n"}}
    if susfs:
        found["susfs"] = {"commit": "5" * 40}
    if features.get("unicode", True):
        found["unicode"] = {"commit": "6" * 40}
    if not features.get("nomount", True):
        found.pop("nomount")
    return found


def run(run_id, number, builds, branch="main"):
    return {"schema": 1, "id": run_id, "attempt": 1, "number": number, "url": f"https://run/{run_id}", "date": "2026-11-05T02:25:07Z",
            "sha": "s", "branch": branch, "builds": builds}


def ok(root, sublevel, commit, **kw):
    return {"root": root, "sublevel": sublevel, "status": "ok", "snap": snap(root, sublevel, commit, **kw), "env": {}}


RECORDS = [
    run(41, 41, [ok("KSU", 172, "old"), ok("KSU", 176, "old"), ok("KSUN", 176, "n41")]),
    run(42, 42, [{"root": "KSU", "status": "wait", "wait": {"id": "Tunggu simonpunk", "en": "Wait"}}, ok("KSUN", 176, "n42")]),
    run(43, 43, [ok("KSU", 176, "dev")], branch="feature"),
]


class PickTest(unittest.TestCase):
    def test_the_newest_good_build_on_main_even_after_a_wait(self):
        found = lg.pick(RECORDS, "KSU", "lts")
        self.assertEqual(found["root_source"]["commit"], "old")    # run 42 waits, run 43 is another branch
        self.assertEqual([a["sublevel"] for a in found["ack"]], [176])
        self.assertEqual(found["source"], {"kind": "stable", "run": 41, "run_id": 41, "url": "https://run/41",
                                           "date": "2026-11-05T02:25:07Z", "record": "run-41-1.md"})
        self.assertEqual(lg.pick(RECORDS, "KSUN")["root_source"]["commit"], "n42")

    def test_sublevels_come_from_those_that_passed(self):
        self.assertEqual([a["sublevel"] for a in lg.pick(RECORDS, "KSU", "semua")["ack"]], [172, 176])
        self.assertEqual([a["sublevel"] for a in lg.pick(RECORDS, "KSU", "172")["ack"]], [172])
        with self.assertRaises(lg.NotFound) as caught:
            lg.pick(RECORDS, "KSU", "162,176")
        self.assertIn("6.1.162 tidak ada di build terakhir yang berhasil (ada: 6.1.172, 6.1.176)", caught.exception.id_text)

    def test_the_form_boxes_decide_which_good_build_fits(self):
        records = [run(50, 50, [ok("KSU", 176, "nomount-off", nomount=False)]), run(49, 49, [ok("KSU", 176, "plain", susfs=False)]),
                   *RECORDS]
        self.assertEqual(lg.pick(records, "KSU")["root_source"]["commit"], "old")      # NoMount ticked: run 50 lacks it
        self.assertEqual(lg.pick(records, "KSU", nomount=False)["root_source"]["commit"], "nomount-off")
        self.assertNotIn("nomount", lg.pick(records, "KSU", nomount=False))
        self.assertEqual(lg.pick(records, "KSU", susfs_box=False)["root_source"]["commit"], "plain")
        self.assertNotIn("unicode", lg.pick(records, "KSU", unicode=False))
        self.assertIn("unicode", lg.pick(records, "KSU", unicode=True))

    def test_no_good_build_says_so_in_both_languages(self):
        with self.assertRaises(lg.NotFound) as caught:
            lg.pick(RECORDS, "SUKI")
        self.assertIn("Stabil: belum ada build SukiSU dengan SUSFS yang berhasil di main", caught.exception.id_text)
        self.assertIn("Use Always newest (CI)", caught.exception.en_text)

    def test_the_real_history_has_a_good_kernelsu_build(self):
        found = lg.pick(bh.load(), "KSU", "lts", unicode=True)
        self.assertEqual(found["source"]["kind"], "stable")
        self.assertIn("susfs", found)


class ArtifactTest(unittest.TestCase):
    def test_an_expired_ci_artifact_stops_early(self):
        found = lg.pick(RECORDS, "KSU")
        self.assertEqual(lg.artifacts(found), [("manager manager", "tiann/KernelSU", 11),
                                               ("sidex15 SUSFS module", "sidex15/susfs4ksu-module", 22)])
        lg.check_artifacts(found, api=lambda path: {"expired": False})
        with self.assertRaises(lg.NotFound) as caught:
            lg.check_artifacts(found, api=lambda path: {"expired": "/11" in path})
        self.assertIn("manager manager dari build terakhir yang berhasil (run #41) sudah kedaluwarsa", caught.exception.id_text)

        def gone(path):
            raise urllib.error.HTTPError(path, 404, "Not Found", {}, io.BytesIO())
        with self.assertRaises(lg.NotFound):
            lg.check_artifacts(found, api=gone)

    def test_a_release_manager_needs_no_check(self):
        found = lg.pick(RECORDS, "KSU")
        found["manager"] = {"kind": "release", "url": "https://x/m.apk"}
        found.pop("susfs_sidex")
        self.assertEqual(lg.artifacts(found), [])


class CliTest(unittest.TestCase):
    def test_writes_the_snapshot_or_what_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            history = Path(tmp, "history")
            history.mkdir()
            for record in RECORDS:
                Path(history, bh.filename(record)).write_text(bh.markdown(record))
            out = Path(tmp, "s.json")
            self.assertEqual(lg.main(["--root", "KSU", "--history", str(history), "--unicode", "--no-artifact-check",
                                      "--out", str(out)]), 0)
            self.assertEqual(json.loads(out.read_text())["root_source"]["commit"], "old")
            self.assertEqual(lg.main(["--root", "SUKI", "--history", str(history), "--no-artifact-check", "--out", str(out)]), 2)
            self.assertIn("wait", json.loads(out.read_text()))


class WiringTest(unittest.TestCase):
    @unittest.skipIf(yaml is None, "PyYAML not installed")
    def test_the_form_asks_the_source_first(self):
        inputs = yaml.safe_load(WORKFLOW.read_text())[True]["workflow_dispatch"]["inputs"]
        self.assertEqual(list(inputs)[:2], ["source", "release_type"])   # right below "Use workflow from"
        self.assertEqual(inputs["source"]["description"], "Pilih sumber / Source")
        self.assertEqual(inputs["source"]["options"], ["Selalu terbaru (CI) / Always newest (CI)",
                                                       "Stabil (terakhir berhasil) / Stable (last good build)"])
        self.assertEqual(inputs["source"]["default"], "Selalu terbaru (CI) / Always newest (CI)")

    def test_the_plan_picks_the_finder_by_source(self):
        text = WORKFLOW.read_text()
        self.assertIn('if [[ "$SOURCE" == Stabil* ]]; then\n            finder=(kernel/last_good.py)', text)
        self.assertIn('python3 "${finder[@]}" --root "$root"', text)
        self.assertIn("Sumber / source", text)

    def test_build_env_and_reports_name_the_source(self):
        self.assertIn('echo "SOURCE=$(snap source.kind 2>/dev/null || echo newest)"', BUILD)
        self.assertIn('echo "SOURCE_RUN=$(snap source.run 2>/dev/null || echo -)"', BUILD)
        env = {"SOURCE": "stable", "SOURCE_RUN": "41", "LINUX_VERSION": "6.1.176", "ACK_TAG": "t", "ROOT_NAME": "KernelSU",
               "ROOT_COMMIT": "a" * 40, "SUSFS_COMMIT": "-", "NOMOUNT": "v2.2.0", "NEUTRON": "n", "FEATURES": "BBR",
               "KMI_COMPAT": "KMI OK; BSP: x"}
        self.assertIn("- Sumber / source: Stabil, build terakhir yang berhasil #41 / Stable, last good build #41",
                      rn.component_lines(env))
        self.assertNotIn("Sumber", "\n".join(rn.component_lines({**env, "SOURCE": "newest"})))
        self.assertIn("🧊 Sumber: Stabil, build terakhir yang berhasil (#41)", tg.post(env, "id"))
        self.assertIn("🧊 Source: Stable, last good build (#41)", tg.post(env, "en"))
        self.assertNotIn("🧊", tg.post({**env, "SOURCE": "newest"}, "id"))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Workflows that read build-info-* per build get one folder per build, also from a run with one build;
the Builder uploads the shared NoMount module once per NoMount version."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # Validate installs PyYAML for its YAML step; locally it may be missing
    yaml = None

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github/workflows"


def steps():
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for name, job in yaml.safe_load(path.read_text())["jobs"].items():
            for step in job.get("steps", []):
                yield f"{path.name}:{name}", job, step


@unittest.skipUnless(yaml, "PyYAML")
class BuildInfoTest(unittest.TestCase):
    def test_download_artifact_merges_or_is_not_used(self):
        # download-artifact puts a lone pattern match straight into its path (Builder run 10): a reader of
        # info/build-info-*/ would see no build. Only the release job, which wants the files merged, uses it.
        for where, _, step in steps():
            with_ = step.get("with") or {}
            if str(step.get("uses", "")).startswith("actions/download-artifact") and "build-info" in str(with_.get("pattern")):
                self.assertIs(with_.get("merge-multiple"), True, where)

    def test_per_build_readers_use_gh_with_a_pattern(self):
        # gh puts every pattern match in a folder of its own (cli/cli isolateArtifacts), even a lone one.
        readers = [(where, job) for where, job, step in steps()
                   if re.search(r"^gh run download .*--pattern 'build-info-\*' --dir info$", str(step.get("run", "")).strip())]
        self.assertEqual(sorted(where for where, _ in readers), ["build-kernel.yml:summary", "catat-sublevel.yml:catat"])
        for where, job in readers:
            self.assertEqual((job.get("permissions") or {}).get("actions"), "read", where)


@unittest.skipUnless(yaml, "PyYAML")
class NoMountOnceTest(unittest.TestCase):
    def plan(self, snapshots):
        # The resolve job's plan script, run as written in the workflow, on fake snapshots.
        job = yaml.safe_load((WORKFLOWS / "build-kernel.yml").read_text())["jobs"]["resolve"]
        run = next(step["run"] for step in job["steps"] if "print(\"matrix=\"" in str(step.get("run")))
        script = run[run.index("<<'PY'\n") + 7:run.rindex("\nPY")]
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "snapshots").mkdir()
            for snap in snapshots:
                (Path(tmp) / "snapshots" / f"{snap['root']}.json").write_text(json.dumps(snap))
            env = dict(os.environ, RELEASE_TYPE="CI", GITHUB_STEP_SUMMARY=str(Path(tmp) / "summary"))
            out = subprocess.run([sys.executable, "-c", script], cwd=tmp, env=env, capture_output=True, text=True, check=True).stdout
        return json.loads(out.split("matrix=", 1)[1])["include"]

    @staticmethod
    def snap(root, nomount, *sublevels):
        return {"root": root, "ack": [{"sublevel": s, "tag": f"t{s}", "commit": "c" * 12} for s in sublevels],
                "root_source": {"tag": "v1", "commit": "a" * 12}, "susfs": {"commit": "b" * 12}, "nomount": {"tag": nomount},
                "bbg": {"commit": "d" * 12}, "anykernel": {"commit": "e" * 12}, "neutron": {"tag": "n1"}}

    def test_the_first_build_of_each_nomount_version_uploads_it(self):
        builds = self.plan([self.snap("BSU", "v2.2.0", 176), self.snap("KSUN", "v2.2.0", 172, 176)])
        self.assertEqual([b["nomount"] for b in builds], ["1", "", ""])
        builds = self.plan([self.snap("BSU", "v2.2.0", 176), self.snap("KSUN", "v2.3.0", 176)])
        self.assertEqual([b["nomount"] for b in builds], ["1", "1"])   # two versions: each one is needed

    def test_the_upload_step_follows_the_plan(self):
        step = next(step for where, _, step in steps() if step.get("name") == "Upload 4 - NoMount module")
        self.assertIn("matrix.nomount == '1'", step["if"])


if __name__ == "__main__":
    unittest.main()

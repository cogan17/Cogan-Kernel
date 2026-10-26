#!/usr/bin/env python3
"""Workflows that read build-info-* per build get one folder per build, also from a run with one build."""
import re
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


if __name__ == "__main__":
    unittest.main()

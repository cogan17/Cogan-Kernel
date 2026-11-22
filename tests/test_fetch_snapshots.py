#!/usr/bin/env python3
"""kernel/scripts/fetch_snapshots.sh retries while a just-uploaded snapshots artifact is not visible yet
(Builder run 71: 8 jobs got "Artifact not found" from actions/download-artifact a few seconds after upload)."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # Validate installs PyYAML for its YAML step; locally it may be missing
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "kernel/scripts/fetch_snapshots.sh"
# Fake gh: fails until the call count reaches $FAIL_UNTIL, then writes the artifact like gh run download.
FAKE_GH = """#!/usr/bin/env bash
n=$(( $(cat "$CALLS" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$CALLS"
echo "$*" >> "$ARGS"
[ "$n" -ge "$FAIL_UNTIL" ] || { echo "no valid artifacts found to download" >&2; exit 1; }
while [ $# -gt 0 ]; do [ "$1" = --dir ] && dir=$2; shift; done
mkdir -p "$dir" && echo '{"root": "KSU"}' > "$dir/KSU.json"
"""


class FetchSnapshotsTest(unittest.TestCase):
    def run_script(self, fail_until, tries=4):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "bin").mkdir()
        gh = tmp / "bin/gh"
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        env = dict(os.environ, PATH=f"{tmp / 'bin'}:{os.environ['PATH']}", CALLS=str(tmp / "calls"),
                   ARGS=str(tmp / "args"), FAIL_UNTIL=str(fail_until), SNAPSHOT_TRIES=str(tries), SNAPSHOT_WAIT="0",
                   GITHUB_RUN_NUMBER="71", GITHUB_RUN_ID="44981877723", GITHUB_REPOSITORY="cogan17/Cogan-Kernel")
        result = subprocess.run(["bash", str(SCRIPT)], cwd=tmp, env=env, capture_output=True, text=True)
        return tmp, result

    def test_retries_until_the_artifact_is_visible(self):
        tmp, result = self.run_script(fail_until=3)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((tmp / "calls").read_text().strip(), "3")
        self.assertTrue((tmp / "snapshots/KSU.json").is_file())
        self.assertIn("run download 44981877723 --repo cogan17/Cogan-Kernel --name snapshots-71 --dir snapshots",
                      (tmp / "args").read_text())

    def test_gives_up_after_the_last_try(self):
        tmp, result = self.run_script(fail_until=99, tries=3)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((tmp / "calls").read_text().strip(), "3")
        self.assertIn("::error::snapshots-71", result.stdout)

    @unittest.skipUnless(yaml, "PyYAML")
    def test_jobs_that_need_the_snapshots_fetch_them_with_retries(self):
        jobs = yaml.safe_load((ROOT / ".github/workflows/build-kernel.yml").read_text())["jobs"]
        for name in ("susfs", "build"):
            job = jobs[name]
            steps = job["steps"]
            self.assertFalse([s for s in steps if "download-artifact" in str(s.get("uses"))
                              and "snapshots" in str((s.get("with") or {}).get("name"))], name)
            self.assertTrue([s for s in steps if s.get("run") == "bash kernel/scripts/fetch_snapshots.sh"], name)
            self.assertEqual(job["permissions"].get("actions"), "read", name)
        sparse = jobs["susfs"]["steps"][0]["with"]["sparse-checkout"]
        self.assertIn("kernel/scripts/fetch_snapshots.sh", sparse)


if __name__ == "__main__":
    unittest.main()

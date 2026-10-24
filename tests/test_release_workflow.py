"""Execute the release workflow's shell blocks offline with a fake GitHub CLI."""
import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/release-from-run.yml"
SOURCE_SHA = "4730fee1297fa5ef1a779a4223136ab1912b09e2"


def script(name):
    step = WORKFLOW.read_text().split(f"      - name: {name}\n", 1)[1]
    return textwrap.dedent(step.split("        run: |\n", 1)[1].split("\n      - ", 1)[0])


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ("bin", "info", "files", "kernel"):
            (self.root / name).mkdir()
        (self.root / "run.json").write_text(json.dumps({"head_sha": SOURCE_SHA}))
        (self.root / "info/build.env").write_text("RELEASE=v26.10.24-r2\nRELEASE_NAME=Cogan r2\n")
        (self.root / "files/1-KERNEL_fixture.zip").write_text("kernel fixture")
        for name in ("release_notes.py", "telegram.py"):
            (self.root / "kernel" / name).write_text('print("notes fixture")\n')
        gh = self.root / "bin/gh"
        gh.write_text('''#!/bin/bash
if [[ "$1 $2" == "release view" ]]; then
  [[ "$CASE" == exists ]] && exit 0
  exit 1
elif [[ "$1 $2" == "release create" ]]; then
  printf '%s\\n' "$@" > called.txt
  case "$CASE" in
    denied) echo 'HTTP 403: Resource not accessible by integration' >&2; exit 1;;
    server-error) echo 'HTTP 500: server error' >&2; exit 1;;
  esac
  echo 'https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/v26.10.24-r2'
else
  echo 'Unexpected API request: the App has no Actions permission' >&2
  exit 2
fi
''')
        gh.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.root / 'bin'}:{os.environ['PATH']}",
                        CASE="success", GITHUB_REPOSITORY="cogan17/Xiomi_14T_Pro",
                        GITHUB_SERVER_URL="https://github.com", SOURCE_RUN="40046361218",
                        GITHUB_STEP_SUMMARY=str(self.root / "summary.md"),
                        RELEASE_TYPE="Pre-Release", TESTED="true", NOTE="Tested on my device.")

    def run_step(self, name, **env):
        return subprocess.run(["bash", "-euo", "pipefail", "-c", script(name)], cwd=self.root,
                              env={**self.env, **env}, capture_output=True, text=True, timeout=10)

    def summary(self):
        path = self.root / "summary.md"
        return path.read_text() if path.exists() else ""

    def test_incomplete_app_setup_stops_with_bilingual_instructions(self):
        for client, key in (("", "false"), ("Iv1.example", "false"), ("", "true")):
            with self.subTest(client=client, key=key):
                result = self.run_step("Periksa pengaturan App / check App setup",
                                       RELEASE_APP_CLIENT_ID=client, HAS_RELEASE_APP_PRIVATE_KEY=key)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("RELEASE_APP_CLIENT_ID", self.summary())
                self.assertIn("RELEASE_APP_PRIVATE_KEY", self.summary())
                self.assertIn("🇮🇩", self.summary())
                self.assertIn("🇬🇧", self.summary())
                self.assertFalse((self.root / "called.txt").exists())

    def test_complete_app_configuration_passes_without_api_calls(self):
        result = self.run_step("Periksa pengaturan App / check App setup",
                               RELEASE_APP_CLIENT_ID="Iv1.example", HAS_RELEASE_APP_PRIVATE_KEY="true")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_publish_uses_validated_source_without_actions_permission(self):
        result = self.run_step("Terbitkan / publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "called.txt").read_text().splitlines()
        self.assertEqual(args[args.index("--target") + 1], SOURCE_SHA)
        self.assertIn("--prerelease", args)
        self.assertNotIn("--latest", args)
        self.assertIn("Terbit:", self.summary())
        self.assertIn("Published:", self.summary())
        self.assertTrue((self.root / "files/checksums.txt").exists())

    def test_release_choice_marks_latest(self):
        result = self.run_step("Terbitkan / publish", RELEASE_TYPE="Release", TESTED="false", NOTE="")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "called.txt").read_text().splitlines()
        self.assertIn("--latest", args)
        self.assertNotIn("--prerelease", args)
        self.assertNotIn("tested on the phone", self.summary())

    def test_existing_release_is_not_overwritten(self):
        result = self.run_step("Terbitkan / publish", CASE="exists")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / "called.txt").exists())

    def test_permissions_failure_points_to_app_setup(self):
        result = self.run_step("Terbitkan / publish", CASE="denied")
        self.assertEqual(result.returncode, 1)
        self.assertIn("RELEASE_APP_PRIVATE_KEY", self.summary())
        self.assertIn("Contents dan Workflows", self.summary())
        self.assertIn("Contents and Workflows", self.summary())
        self.assertNotIn("Terbit:", self.summary())

    def test_server_failure_is_not_reported_as_permissions_failure(self):
        result = self.run_step("Terbitkan / publish", CASE="server-error")
        self.assertEqual(result.returncode, 1)
        self.assertIn("HTTP 500", result.stderr)
        self.assertNotIn("RELEASE_APP_PRIVATE_KEY", self.summary())


if __name__ == "__main__":
    unittest.main()

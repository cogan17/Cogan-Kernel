#!/usr/bin/env python3
"""CVE-2026-53163 in every build (owner 2026-11-01): applied only where the CVE-2026-43499 fix brought the
remove_waiter() regression (ACK 6.1.175-176), skipped where it is absent or already fixed, strict otherwise."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "kernel/patches/cve-2026-53163-rtmutex.patch"
BLOCK = re.search(r"^# CVE-2026-53163.*?^echo \"::endgroup::\"$", (ROOT / "kernel/build.sh").read_text(), re.S | re.M)[0]


def preimage(patch):
    """{path: text} with the lines each hunk expects before the patch (context and removed lines)."""
    files, path = {}, None
    for line in patch.splitlines():
        if line.startswith("--- a/"):
            path = line[6:]
            files[path] = []
        elif path and line.startswith("@@"):
            files[path].append("")
        elif path and line[:1] in (" ", "-") and not line.startswith("---"):
            files[path].append(line[1:])
    texts = {path: "\n".join(lines) + "\n" for path, lines in files.items()}
    # The CVE-2026-43499 fix this one follows (Linux 6.1.175), a few lines above the hunk.
    texts["kernel/locking/rtmutex.c"] = "\tstruct task_struct *waiter_task = waiter->task;\n" + texts["kernel/locking/rtmutex.c"]
    return texts


class CveRtmutexTest(unittest.TestCase):
    def run_block(self, files, box="true"):
        with tempfile.TemporaryDirectory() as tmp:
            for path, text in files.items():
                Path(tmp, path).parent.mkdir(parents=True, exist_ok=True)
                Path(tmp, path).write_text(text)
            subprocess.run(["git", "init", "-q", tmp], check=True)
            script = ('set -euo pipefail; log() { echo "[+] $*"; }; group() { :; }; fail() { echo "FAIL $*"; exit 1; }\n'
                      'apply() { git -C "$KSRC" apply --whitespace=nowarn "$1"; }\n' + BLOCK + '\necho "STATE=$CVE_2026_53163"')
            result = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                                    env={"KSRC": tmp, "HERE": str(ROOT / "kernel"), "ACK_TAG": "t", "SUBLEVEL": "176", "CVE": box,
                                         "PATH": "/usr/bin:/bin"})
            texts = {path: Path(tmp, path).read_text() for path in files}
        return result, texts

    def test_suspended_by_default(self):
        # Owner 2 Nov 2026 (myBCA on r8): "Test tanpa cve ... coba di tangguhkan".
        files = preimage(PATCH.read_text())
        result, texts = self.run_block(files, box="false")
        self.assertIn("STATE=off", result.stdout, result.stdout + result.stderr)
        self.assertEqual(texts, files)
        import yaml
        box = yaml.safe_load((ROOT / ".github/workflows/build-kernel.yml").read_text())[True]["workflow_dispatch"]["inputs"]["use_cve"]
        self.assertIs(box["default"], False)
        self.assertIn("CVE: ${{ inputs.use_cve }}", (ROOT / ".github/workflows/build-kernel.yml").read_text())

    def test_the_patch_is_the_upstream_stable_commit(self):
        text = PATCH.read_text()
        self.assertIn("[ Upstream commit 40a25d59e85b3c8709ac2424d44f65610467871e ]", text)
        self.assertEqual(sorted(preimage(text)), ["kernel/locking/rtmutex.c", "kernel/locking/rtmutex_api.c"])

    def test_applied_on_the_cve_2026_43499_tree(self):
        result, texts = self.run_block(preimage(PATCH.read_text()))
        self.assertIn("STATE=applied", result.stdout, result.stdout + result.stderr)
        self.assertIn("if (!waiter_task) /* never enqueued */", texts["kernel/locking/rtmutex.c"])
        self.assertIn("if (unlikely(ret < 0))", texts["kernel/locking/rtmutex_api.c"])

    def test_skipped_when_already_fixed_or_not_needed(self):
        fixed = preimage(PATCH.read_text())
        fixed["kernel/locking/rtmutex.c"] += "\tif (!waiter_task) /* never enqueued */\n"
        self.assertIn("STATE=present", self.run_block(fixed)[0].stdout)
        old = {"kernel/locking/rtmutex.c": "\traw_spin_lock(&current->pi_lock);\n"}
        self.assertIn("STATE=not-needed", self.run_block(old)[0].stdout)

    def test_a_tree_the_patch_does_not_fit_stops_the_build(self):
        broken = {"kernel/locking/rtmutex.c": "\tstruct task_struct *waiter_task = waiter->task;\n",
                  "kernel/locking/rtmutex_api.c": "\n"}
        result = self.run_block(broken)[0]
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL CVE-2026-53163 fix does not fit ACK 6.1.176", result.stdout)


if __name__ == "__main__":
    unittest.main()

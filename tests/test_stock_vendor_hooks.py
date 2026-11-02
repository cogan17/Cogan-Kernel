#!/usr/bin/env python3
"""Stock scheduler vendor hooks (Issue #105): ACK 2025-07 (6.1.141) lacks two ACK commits the phone's stock
kernel and the vendor modules have; applied as they are when missing, skipped when present, strict otherwise."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "kernel/patches/stock-vendor-hooks-sched.patch"
BUILD = (ROOT / "kernel/build.sh").read_text()
BLOCK = re.search(r'^group "Stock vendor hooks.*?^echo "::endgroup::"$', BUILD, re.S | re.M)[0]


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
    return {path: "\n".join(lines) + "\n" for path, lines in files.items()}


class StockVendorHooksTest(unittest.TestCase):
    def run_block(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            for path, text in files.items():
                Path(tmp, path).parent.mkdir(parents=True, exist_ok=True)
                Path(tmp, path).write_text(text)
            subprocess.run(["git", "init", "-q", tmp], check=True)
            script = ('set -euo pipefail; log() { echo "[+] $*"; }; group() { :; }; fail() { echo "FAIL $*"; exit 1; }\n'
                      'apply() { git -C "$KSRC" apply --whitespace=nowarn "$1"; }\n' + BLOCK +
                      '\necho "STATE=$STOCK_VENDOR_HOOKS"')
            result = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                                    env={"KSRC": tmp, "HERE": str(ROOT / "kernel"), "ACK_TAG": "t", "SUBLEVEL": "141",
                                         "PATH": "/usr/bin:/bin"})
            texts = {path: Path(tmp, path).read_text() for path in files}
        return result, texts

    def test_the_patch_is_the_two_ack_commits(self):
        text = PATCH.read_text()
        for commit in ("8148058f689d", "9667c70358a5"):
            self.assertIn(commit, text)
        self.assertEqual(sorted(preimage(text)), ["include/trace/hooks/sched.h", "kernel/sched/core.c",
                                                  "kernel/sched/fair.c", "kernel/sched/vendor_hooks.c"])
        for hook in ("android_vh_sched_move_task", "android_vh_reweight_entity"):
            self.assertIn(f"+EXPORT_TRACEPOINT_SYMBOL_GPL({hook});", text)

    def test_applied_where_missing(self):
        result, texts = self.run_block(preimage(PATCH.read_text()))
        self.assertIn("STATE=applied", result.stdout, result.stdout + result.stderr)
        self.assertIn("trace_android_vh_reweight_entity(se);", texts["kernel/sched/fair.c"])
        self.assertIn("trace_android_vh_sched_move_task(tsk);", texts["kernel/sched/core.c"])

    def test_skipped_when_present(self):
        files = preimage(PATCH.read_text())
        files["include/trace/hooks/sched.h"] += "DECLARE_HOOK(android_vh_sched_move_task,\nDECLARE_HOOK(android_vh_reweight_entity,\n"
        result, texts = self.run_block(files)
        self.assertIn("STATE=present", result.stdout, result.stdout + result.stderr)
        self.assertEqual(texts, files)

    def test_part_of_the_hooks_stops_the_build(self):
        files = preimage(PATCH.read_text())
        files["include/trace/hooks/sched.h"] += "DECLARE_HOOK(android_vh_sched_move_task,\n"
        result, _ = self.run_block(files)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL ACK t has only part of the stock scheduler vendor hooks", result.stdout)

    def test_a_patch_that_does_not_fit_stops_the_build(self):
        files = {path: "something else\n" for path in preimage(PATCH.read_text())}
        result, _ = self.run_block(files)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL Stock vendor hooks do not fit ACK 6.1.141", result.stdout)

    def test_build_env_records_it(self):
        self.assertIn('echo "STOCK_VENDOR_HOOKS=$STOCK_VENDOR_HOOKS"', BUILD)


if __name__ == "__main__":
    unittest.main()

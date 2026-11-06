#!/usr/bin/env python3
"""HyperOS OS3.0.302 vendor hooks and exports for older ACK releases (owner 2026-11-06): the official ACK
commits are cherry-picked per sublevel; applied as they are when all are missing, skipped when present,
strict otherwise."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from kernel.scripts import kmi_compat as kc

ROOT = Path(__file__).resolve().parents[1]
PATCHES = ROOT / "kernel/patches/hyperos302"
BUILD = (ROOT / "kernel/build.sh").read_text()
BLOCK = re.search(r'^group "HyperOS 302.*?^echo "::endgroup::"$', BUILD, re.S | re.M)[0]
MARKERS = {"include/trace/hooks/mm.h": "DECLARE_HOOK(android_vh_mm_direct_reclaim_start,\n",
           "init/init_task.c": "u64 vendor_data_pad[1];\n",
           "mm/filemap.c": "EXPORT_SYMBOL(__filemap_remove_folio);\n"}


def preimage(patch):
    """{path: text} with the lines each hunk expects before the patch (context and removed lines)."""
    files, path = {}, None
    for line in patch.splitlines():
        if line.startswith("--- a/"):
            path = line[6:]
            files[path] = []
        elif line.startswith("--- /dev/null"):
            path = None
        elif path and line.startswith("@@"):
            files[path].append("")
        elif path and line[:1] in (" ", "-") and not line.startswith("---"):
            files[path].append(line[1:])
    return {path: "\n".join(lines) + "\n" for path, lines in files.items()}


class HyperOS302Test(unittest.TestCase):
    def run_block(self, files, sublevel="162"):
        with tempfile.TemporaryDirectory() as tmp:
            for path, text in files.items():
                Path(tmp, path).parent.mkdir(parents=True, exist_ok=True)
                Path(tmp, path).write_text(text)
            subprocess.run(["git", "init", "-q", tmp], check=True)
            script = ('set -euo pipefail; log() { echo "[+] $*"; }; group() { :; }; fail() { echo "FAIL $*"; exit 1; }\n'
                      'apply() { git -C "$KSRC" apply --whitespace=nowarn "$1"; }\n' + BLOCK +
                      '\necho "STATE=$HYPEROS302"')
            result = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                                    env={"KSRC": tmp, "HERE": str(ROOT / "kernel"), "ACK_TAG": "t",
                                         "SUBLEVEL": sublevel, "PATH": "/usr/bin:/bin"})
            texts = {path: Path(tmp, path).read_text() for path in files}
        return result, texts

    def test_a_patch_for_every_sublevel_the_stock_302_kernel_needs(self):
        # 157, 172 and 176 have the hooks (CI run 42164313002); 138, 141, 145 and 162 do not.
        self.assertEqual(sorted(p.name for p in PATCHES.glob("*.patch")),
                         ["6.1.138.patch", "6.1.141.patch", "6.1.145.patch", "6.1.162.patch"])
        for patch in PATCHES.glob("*.patch"):
            text = patch.read_text()
            commits = re.findall(r"^  ([0-9a-f]{12}) ANDROID: ", text, re.M)
            self.assertTrue(commits, patch.name)
            # the dynamic task_struct size of the stock kernel, and the exports its vendor modules use
            for commit in ("93f1f1150300", "94c4c3f92d03", "9d2e77d7fce3", "40bc26814c22"):
                self.assertIn(commit, commits, patch.name)
            for line in ("+EXPORT_SYMBOL(__filemap_remove_folio);", "+EXPORT_SYMBOL_GPL(vendor_data_pad);",
                         "+EXPORT_TRACEPOINT_SYMBOL_GPL(android_vh_mm_direct_reclaim_start);",
                         'early_param("android_arch_task_struct_size", task_struct_vendor_size_setup);'):
                self.assertIn(line, text, patch.name)

    def test_the_patches_hold_the_hooks_the_stock_302_vendor_modules_use(self):
        stock = next(s for s in kc.DEVICES["rothko"]["stocks"] if s["version"] == "6.1.157")
        self.assertEqual(stock["commit"], "0baf70f2581d2bef029fb08cb61255e420858d10")
        for patch in PATCHES.glob("*.patch"):
            text = patch.read_text()
            for hook in ("android_vh_alloc_pages_slowpath_start", "android_vh_cma_alloc_bypass",
                         "android_vh_fuse_request_fetch", "android_vh_mmap_lock_init", "android_vh_rcu_boost_start"):
                self.assertIn(f"+EXPORT_TRACEPOINT_SYMBOL_GPL({hook});", text, patch.name)

    def test_applied_where_missing(self):
        text = (PATCHES / "6.1.162.patch").read_text()
        result, texts = self.run_block(preimage(text))
        self.assertIn("STATE=applied", result.stdout, result.stdout + result.stderr)
        self.assertIn("23 ACK commits", result.stdout)
        self.assertIn("vendor_data_pad", texts["init/init_task.c"])

    def test_skipped_when_present(self):
        result, texts = self.run_block(dict(MARKERS), sublevel="176")
        self.assertIn("STATE=present", result.stdout, result.stdout + result.stderr)
        self.assertEqual(texts, MARKERS)

    def test_part_of_it_stops_the_build(self):
        files = {path: "" for path in MARKERS}
        files["mm/filemap.c"] = MARKERS["mm/filemap.c"]
        result, _ = self.run_block(files)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL ACK t has only part of the HyperOS 302 vendor hooks and exports", result.stdout)

    def test_a_sublevel_without_a_patch_stops_the_build(self):
        result, _ = self.run_block({path: "" for path in MARKERS}, sublevel="150")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL No HyperOS 302 patch for 6.1.150", result.stdout)

    def test_a_patch_that_does_not_fit_stops_the_build(self):
        result, _ = self.run_block({path: "something else\n" for path in MARKERS})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL HyperOS 302 patch does not fit ACK t", result.stdout)

    def test_build_env_records_it(self):
        self.assertIn('echo "HYPEROS302=$HYPEROS302"', BUILD)
        # after the scheduler hooks: the 6.1.141 patch is made on top of stock-vendor-hooks-sched.patch
        self.assertLess(BUILD.index('group "Stock vendor hooks'), BUILD.index('group "HyperOS 302'))


if __name__ == "__main__":
    unittest.main()

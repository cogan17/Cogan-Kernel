#!/usr/bin/env python3
"""Offline tests for susfs_context.py: the SUSFS patch fits older ACK releases by context only."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from kernel.scripts import susfs_context as sc

BLK = "#include <trace/hooks/blk.h>"
# fs/namespace.c includes of ACK 6.1.157 and newer, and of 6.1.138/145 (no blk.h hook include).
NEW = ["#include <linux/shmem_fs.h>", "#include <linux/mnt_idmapping.h>", "", '#include "pnode.h"',
       '#include "internal.h"', BLK, "", "/* Maximum number of mounts in a mount namespace */",
       "static unsigned int sysctl_mount_max __read_mostly = 100000;"]
OLD = [line for line in NEW if line != BLK]
# The shape of SUSFS's hunk: additions on both sides of the blk.h context line.
PATCH = f"""diff --git a/fs/namespace.c b/fs/namespace.c
index 4d910be7c..572d3c20f 100644
--- a/fs/namespace.c
+++ b/fs/namespace.c
@@ -1,9 +1,13 @@
 #include <linux/shmem_fs.h>
 #include <linux/mnt_idmapping.h>
+#ifdef CONFIG_KSU_SUSFS
+#include <linux/susfs_def.h>
+#endif
 
 #include "pnode.h"
 #include "internal.h"
 {BLK}
 
+/* SUSFS */
 /* Maximum number of mounts in a mount namespace */
 static unsigned int sysctl_mount_max __read_mostly = 100000;
diff --git a/fs/stat.c b/fs/stat.c
--- a/fs/stat.c
+++ b/fs/stat.c
@@ -1,2 +1,3 @@
 {BLK}
+/* SUSFS stat */
 int x;
"""


class SusfsContextTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.src = Path(self.temp.name)
        (self.src / "fs").mkdir()
        (self.src / "fs/stat.c").write_text(f"{BLK}\nint x;\n")

    def namespace(self, lines):
        (self.src / "fs/namespace.c").write_text("\n".join(lines) + "\n")

    def test_older_ack_drops_the_context_line_only(self):
        self.namespace(OLD)
        text, dropped = sc.adapt(PATCH, self.src)
        self.assertEqual(dropped, [f"fs/namespace.c: {BLK}"])
        self.assertIn("@@ -1,8 +1,12 @@", text)
        self.assertNotIn(f" {BLK}\n \n+/* SUSFS */", text)
        self.assertIn("+#include <linux/susfs_def.h>", text)  # what SUSFS adds stays
        self.assertIn(f"@@ -1,2 +1,3 @@\n {BLK}\n+/* SUSFS stat */", text)  # other files untouched
        if shutil.which("patch"):
            result = subprocess.run(["patch", "-p1", "--fuzz=3", "--no-backup-if-mismatch"], input=text,
                                    cwd=self.src, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            patched = (self.src / "fs/namespace.c").read_text()
            self.assertIn("#include <linux/susfs_def.h>", patched)
            self.assertIn("/* SUSFS */", patched)
            self.assertNotIn(BLK, patched)

    def test_newer_ack_keeps_the_patch_as_it_is(self):
        self.namespace(NEW)
        self.assertEqual(sc.adapt(PATCH, self.src), (PATCH, []))

    def test_added_lines_are_never_touched(self):
        self.namespace(OLD)
        patch = PATCH.replace(f" {BLK}\n \n+/* SUSFS */", f"+{BLK}\n \n+/* SUSFS */")
        patch = patch.replace("-1,9 +1,13", "-1,8 +1,13")
        self.assertEqual(sc.adapt(patch, self.src), (patch, []))

    def test_other_mismatches_still_stop_the_patch(self):
        self.namespace([line.replace("pnode.h", "pnode2.h") for line in OLD])
        text, _ = sc.adapt(PATCH, self.src)
        if shutil.which("patch"):
            result = subprocess.run(["patch", "-p1", "--fuzz=3", "--dry-run"], input=text, cwd=self.src,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()

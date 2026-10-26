#!/usr/bin/env python3
"""Offline tests for kernel/susfs_module.sh: simonpunk's SUSFS module from one SUSFS commit, with a fake NDK."""
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "kernel/susfs_module.sh"
FILES = {
    "ksu_susfs/jni/Android.mk": "LOCAL_MODULE := ksu_susfs\n",
    "ksu_susfs/jni/main.c": "int main(void) { return 0; }\n",
    "ksu_module_susfs/module.prop": "id=susfs4ksu\nname=SUSFS-FOR-KERNELSU\nversion=v2.3.0\nversionCode=202000\n",
    "ksu_module_susfs/customize.sh": "cp tools/ksu_susfs_arm64 /data/adb/ksu/bin/ksu_susfs\n",
    "ksu_module_susfs/META-INF/com/google/android/update-binary": "#!/sbin/sh\n",
    "ksu_module_susfs/tools/ksu_susfs_arm64": "old prebuilt tool\n",
    "ksu_module_susfs/.susfs_no_auto_add_try_umount": "",
    "ksu_module_susfs/susfs_no_auto_add_try_umount": "",
}
# ELF64, little endian, e_machine at byte 18: 183 = AArch64, 62 = x86-64.
NDK = """#!/bin/sh
mkdir -p libs/arm64-v8a
python3 -c 'import sys; open("libs/arm64-v8a/ksu_susfs", "wb").write(b"\\x7fELF\\x02\\x01" + bytes(12) + int(sys.argv[1]).to_bytes(2, "little") + b"compiled")' {machine}
"""


class SusfsModuleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.src = self.base / "susfs"
        for name, text in FILES.items():
            path = self.src / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        git = ["git", "-C", str(self.src), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(["git", "init", "-q", str(self.src)], check=True)
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-qm", "susfs"], check=True)
        self.commit = subprocess.run(git + ["rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, machine=183):
        ndk = self.base / "ndk-build"
        ndk.write_text(NDK.format(machine=machine))
        ndk.chmod(0o755)
        return subprocess.run(["bash", str(SCRIPT), str(self.src), str(self.base / "out")], capture_output=True, text=True,
                              env={"PATH": "/usr/bin:/bin", "NDK_BUILD": str(ndk)})

    def test_module_from_the_commit_with_the_compiled_tool(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        name = f"5-SUSFS-MODULE-SIMONPUNK_v2.3.0_{self.commit[:8]}.zip"
        with zipfile.ZipFile(self.base / "out" / name) as archive:
            names = set(archive.namelist())
            self.assertTrue({"module.prop", "customize.sh", "META-INF/com/google/android/update-binary",
                             "tools/ksu_susfs_arm64", "susfs_no_auto_add_try_umount"} <= names)
            self.assertNotIn(".susfs_no_auto_add_try_umount", names)        # "zip -r9 ... *" as simonpunk's script
            self.assertTrue(archive.read("tools/ksu_susfs_arm64").endswith(b"compiled"))   # not the old prebuilt
        env = dict(line.split("=", 1) for line in (self.base / "out" / f"susfs-{self.commit[:8]}.env").read_text().splitlines())
        self.assertEqual((env["SUSFS_MODULE"], env["SUSFS_MODULE_VERSION"], env["SUSFS_MODULE_COMMIT"]),
                         (name, "v2.3.0", self.commit))
        self.assertEqual(len(env["SUSFS_MODULE_SHA256"]), 64)

    def test_a_tool_that_is_not_64_bit_arm_stops(self):
        result = self.build(machine=62)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a 64-bit ARM program", result.stdout + result.stderr)
        self.assertFalse(list((self.base / "out").glob("5-*")))


if __name__ == "__main__":
    unittest.main()

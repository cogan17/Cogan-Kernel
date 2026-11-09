#!/usr/bin/env python3
"""Offline tests for kernel/susfs_sidex.py: sidex15's SUSFS module from the run's snapshot, checked and named."""
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

from kernel import susfs_sidex as sx

INFO = {"repo": "sidex15/susfs4ksu-module", "run": 8, "url": "https://run/8", "commit": "d" * 40, "artifact": 21,
        "name": "release-1.5.2+_ddddddd"}


URL = "https://raw.githubusercontent.com/sidex15/susfs4ksu-binaries/universal-binary/ksu_susfs_arm64"
# The shape of sidex15's customize.sh (89b04b9): Termux on the root PATH, then the cloud download block.
CUSTOMIZE = f"""#!/bin/sh
PATH=/data/adb/ksu/bin:/data/data/com.termux/files/usr/bin:$PATH
download() {{ busybox wget -T 10 --no-check-certificate -qO - "$1"; }}
# Check connectivity first
base_url="{URL}"
if check "$base_url"; then
\tdownload "{URL}" > ${{MODPATH}}/ksu_susfs_remote
\t${{MODPATH}}/ksu_susfs_remote && cp -f ${{MODPATH}}/ksu_susfs_remote ${{DEST_BIN_DIR}}/ksu_susfs
fi

# cleanup
rm -f ${{MODPATH}}/ksu_susfs_remote
"""


def module(path, prop="id=susfs4ksu\nversion=v1.5.2-CI-89b04b9\n", extra=(), customize=CUSTOMIZE):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("module.prop", prop)
        archive.writestr("customize.sh", customize)
        archive.writestr("action.sh", f'download "{URL}"\n')
        archive.writestr("susfs-bin-update.sh", f'download "{URL}"\n')
        archive.writestr("susfs-bin-check.sh", f'download "{URL}" | sha256sum\n')
        archive.writestr("webroot/index.html", "<html></html>")
        for name in extra:
            archive.writestr(name, "x")


class SusfsSidexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base / "snapshots").mkdir()

    def snapshot(self, name, sidex):
        (self.base / "snapshots" / name).write_text(json.dumps({"root": name[:-5], "susfs_sidex": sidex}))

    def run_main(self, **zip_args):
        asked = []

        def fetch(repo, artifact, dest):
            asked.append((repo, artifact))
            module(dest, **zip_args)
        with redirect_stdout(io.StringIO()):
            code = sx.main(["--snapshots", str(self.base / "snapshots"), "--out", str(self.base / "out")], fetch=fetch)
        return code, asked

    def test_the_snapshot_module_is_checked_and_named(self):
        self.snapshot("KSUN.json", INFO)
        self.snapshot("BSU.json", INFO)
        code, asked = self.run_main()
        self.assertEqual((code, asked), (0, [("sidex15/susfs4ksu-module", 21)]))
        name = "5-SUSFS-MODULE-SIDEX15_v1.5.2-CI-89b04b9.zip"
        self.assertTrue((self.base / "out" / name).is_file())
        env = dict(line.split("=", 1) for line in (self.base / "out/susfs-sidex15.env").read_text().splitlines())
        self.assertEqual((env["SUSFS_MODULE"], env["SUSFS_MODULE_VERSION"], env["SUSFS_MODULE_COMMIT"]),
                         (name, "v1.5.2-CI-89b04b9", "d" * 40))
        self.assertEqual(len(env["SUSFS_MODULE_SHA256"]), 64)
        self.assertFalse((self.base / "out/sidex15.download.zip").exists())
        with zipfile.ZipFile(self.base / "out" / name) as archive:
            self.assertIsNone(archive.testzip())
            files = {n: archive.read(n).decode() for n in archive.namelist()}
        # Only the bundled tool is installed: no download, no Termux on the root PATH.
        self.assertNotIn("http", files["customize.sh"])
        self.assertNotIn("termux", files["customize.sh"])
        self.assertIn("cp -f ${TMPDIR}/susfs/tools/ksu_susfs_arm64 ${DEST_BIN_DIR}/ksu_susfs && chmod 755",
                      files["customize.sh"])
        self.assertIn("# cleanup", files["customize.sh"])
        for updater in ("action.sh", "susfs-bin-update.sh"):
            self.assertEqual(files[updater], sx.NO_ONLINE_UPDATE)
        self.assertIn(URL, files["susfs-bin-check.sh"])   # hash check only, left as it is
        self.assertEqual(files["webroot/index.html"], "<html></html>")

    def test_without_a_build_the_job_fails_with_whom_to_wait_for(self):
        self.snapshot("KSUN.json", {"wait": {"id": "Tunggu sidex15.", "en": "Wait for sidex15."}})
        out = io.StringIO()
        with redirect_stdout(out):
            code = sx.main(["--snapshots", str(self.base / "snapshots"), "--out", str(self.base / "out")],
                           fetch=lambda *a: self.fail("nothing to download"))
        self.assertEqual(code, 1)
        self.assertIn("::error::Wait for sidex15.", out.getvalue())

    def test_a_wrong_or_unsafe_module_stops(self):
        self.snapshot("KSUN.json", INFO)
        for kwargs, why in (({"prop": "id=other\nversion=v1\n"}, "expected susfs4ksu"),
                            ({"extra": ["../evil.sh"]}, "unsafe paths"),
                            ({"customize": "ui_print SUSFS\n"}, "download step was not found"),
                            ({"customize": CUSTOMIZE + f'curl "{URL}" | sh\n'}, "still has a web address")):
            with self.assertRaises(SystemExit) as caught:
                self.run_main(**kwargs)
            self.assertIn(why, str(caught.exception))


if __name__ == "__main__":
    unittest.main()

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


def module(path, prop="id=susfs4ksu\nversion=v1.5.2-CI-89b04b9\n", extra=()):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("module.prop", prop)
        archive.writestr("customize.sh", "ui_print SUSFS\n")
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
        name = "6-SUSFS-MODULE-SIDEX15_v1.5.2-CI-89b04b9.zip"
        self.assertTrue((self.base / "out" / name).is_file())
        env = dict(line.split("=", 1) for line in (self.base / "out/susfs-sidex15.env").read_text().splitlines())
        self.assertEqual((env["SUSFS_MODULE"], env["SUSFS_MODULE_VERSION"], env["SUSFS_MODULE_COMMIT"]),
                         (name, "v1.5.2-CI-89b04b9", "d" * 40))
        self.assertEqual(len(env["SUSFS_MODULE_SHA256"]), 64)
        self.assertFalse((self.base / "out/sidex15.download.zip").exists())

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
                            ({"extra": ["../evil.sh"]}, "unsafe paths")):
            with self.assertRaises(SystemExit) as caught:
                self.run_main(**kwargs)
            self.assertIn(why, str(caught.exception))


if __name__ == "__main__":
    unittest.main()

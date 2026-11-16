#!/usr/bin/env python3
"""Offline tests for hybrid_susfs, the 6th file (owner 2026-11-17): resolve.susfs_hybrid and kernel/susfs_hybrid.py."""
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from kernel import resolve as r
from kernel import susfs_hybrid as hy


def module_zip(module_id="hybrid_susfs", version="v0.5", script=b"#!/system/bin/sh\necho ok\n"):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("module.prop", f"id={module_id}\nversion={version}\n")
        archive.writestr("customize.sh", script)
        archive.writestr("service.sh", "#!/system/bin/sh\n")
    return data.getvalue()


def release(tag="v0.5", draft=False, prerelease=True, assets=("hybrid_susfs_v0.5.zip",)):
    return {"tag_name": tag, "draft": draft, "prerelease": prerelease, "published_at": "2026-11-16T18:55:31Z",
            "html_url": f"https://hybrid/{tag}",
            "assets": [{"name": name, "browser_download_url": f"https://hybrid/{name}", "digest": "sha256:" + "a" * 64}
                       for name in assets]}


class ResolveTest(unittest.TestCase):
    def test_newest_published_release_with_its_zip(self):
        found = r.susfs_hybrid(lambda path: [release("v0.6", draft=True), release(), release("v0.4")])
        self.assertEqual((found["tag"], found["prerelease"], found["name"]), ("v0.5", True, "hybrid_susfs_v0.5.zip"))
        self.assertEqual(found["digest"], "sha256:" + "a" * 64)

    def test_waits_without_a_zip_or_a_release(self):
        self.assertIn("Tunggu Cogan menerbitkan ZIP modul hybrid_susfs v0.5", r.susfs_hybrid(lambda path: [release(assets=())])["wait"]["id"])
        self.assertIn("Tunggu rilis hybrid_susfs pertama", r.susfs_hybrid(lambda path: [])["wait"]["id"])


class FetchTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        (self.base / "snapshots").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def run_with(self, data, digest=None):
        info = {**r.susfs_hybrid(lambda path: [release()]), "digest": digest or "sha256:" + hashlib.sha256(data).hexdigest()}
        (self.base / "snapshots" / "KSU.json").write_text(json.dumps({"root": "KSU", "susfs_hybrid": info}))
        return hy.main(["--snapshots", str(self.base / "snapshots"), "--out", str(self.base / "out")],
                       fetch=lambda url, dest: Path(dest).write_bytes(data))

    def test_checked_and_named_as_file_6(self):
        self.assertEqual(self.run_with(module_zip()), 0)
        self.assertTrue((self.base / "out/6-SUSFS-MODULE-HYBRID_v0.5.zip").exists())
        env = (self.base / "out/susfs-hybrid.env").read_text()
        self.assertIn("SUSFS_MODULE=6-SUSFS-MODULE-HYBRID_v0.5.zip\n", env)
        self.assertIn("SUSFS_MODULE_PRERELEASE=1\n", env)

    def test_a_different_sha256_stops(self):
        self.assertEqual(self.run_with(module_zip(), digest="sha256:" + "b" * 64), 1)
        self.assertFalse((self.base / "out/6-SUSFS-MODULE-HYBRID_v0.5.zip").exists())

    def test_another_module_or_a_download_in_its_scripts_stops(self):
        with self.assertRaises(SystemExit):
            self.run_with(module_zip(module_id="susfs4ksu"))
        with self.assertRaises(SystemExit):
            self.run_with(module_zip(script=b"#!/system/bin/sh\ncurl -o x https://example.com/ksu_susfs\n"))

    def test_without_a_snapshot_entry_it_waits(self):
        (self.base / "snapshots" / "KSU.json").write_text(json.dumps({"root": "KSU"}))
        self.assertEqual(hy.main(["--snapshots", str(self.base / "snapshots"), "--out", str(self.base / "out")]), 1)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline tests for the stock kernel reference fetch (a local repository stands in for ACK)."""
import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from kernel.scripts import stock_reference as sr


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


class StockReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.ack = base / "ack"
        for path, text in (("Makefile", "VERSION = 6\nPATCHLEVEL = 1\nSUBLEVEL = 138\n"),
                           ("build.config.common", "KMI_GENERATION=11\n"),
                           ("android/abi_gki_aarch64_mtk", "[abi_symbol_list]\n  x\n"),
                           ("include/trace/hooks/sched.h", "DECLARE_HOOK(android_vh_x, a, b);\n"),
                           ("mm/shmem.c", "not needed by the gate\n")):
            (self.ack / path).parent.mkdir(parents=True, exist_ok=True)
            (self.ack / path).write_text(text)
        git(self.ack.parent, "init", "-q", str(self.ack))
        git(self.ack, "config", "uploadpack.allowFilter", "true")
        git(self.ack, "config", "uploadpack.allowAnySHA1InWant", "true")
        git(self.ack, "add", ".")
        git(self.ack, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "stock")
        self.commit = git(self.ack, "rev-parse", "HEAD")
        self.dest = base / "stock"

    def fetch(self, **stock):
        pinned = [dict(sr.DEVICES["rothko"]["stocks"][0], commit=self.commit, **stock)]
        with mock.patch.dict(sr.DEVICES["rothko"], {"stocks": pinned}):
            return sr.main(["--device", "rothko", str(self.dest), "--repo", self.ack.as_uri()])

    def test_fetches_only_what_the_gate_reads_at_the_stock_commit(self):
        self.assertEqual(self.fetch(), 0)
        ref = self.dest / "6.1.138"
        self.assertEqual(git(ref, "rev-parse", "HEAD"), self.commit)
        self.assertTrue((ref / "android/abi_gki_aarch64_mtk").is_file())
        self.assertTrue((ref / "include/trace/hooks/sched.h").is_file())
        self.assertFalse((ref / "mm").exists())

    def test_wrong_version_or_used_destination_is_refused(self):
        self.assertEqual(self.fetch(version="6.1.155"), 1)
        self.assertEqual(self.fetch(), 1)  # destination no longer empty

    def test_every_supported_hyperos_stock_kernel_is_fetched(self):
        stocks = sr.DEVICES["rothko"]["stocks"]
        self.assertEqual([(s["hyperos"], s["version"], s["commit"]) for s in stocks],
                         [("OS3.0.301.0.WNNIDXM", "6.1.138", "6ab8c9a86a331cece499c7edac062ceffbe2e320"),
                          ("OS3.0.302.0.WNNIDXM", "6.1.157", "0baf70f2581d2bef029fb08cb61255e420858d10")])
        for stock in stocks:
            self.assertTrue(stock["kernel"].startswith(stock["version"] + "-android14-11-g" + stock["commit"][:12]))


if __name__ == "__main__":
    unittest.main()

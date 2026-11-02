#!/usr/bin/env python3
"""BBRv3 patch sets per ACK sublevel: build.sh takes the set of the sublevel or the newest one below it."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETS = ROOT / "kernel/patches/bbrv3"
BUILD = (ROOT / "kernel/build.sh").read_text()
PICK = re.search(r'^  BBR_SUB=""\n.*?^  done\n', BUILD, re.S | re.M)[0]


def picked(sublevel):
    script = f'HERE={ROOT / "kernel"}\nSUBLEVEL={sublevel}\n{PICK}echo "$BBR_SUB"'
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True).stdout.strip()


def body(path):
    text = path.read_text()
    return text[text.index("diff --git"):]


class Bbrv3SetsTest(unittest.TestCase):
    def test_every_set_is_complete(self):
        for folder in sorted(p for p in SETS.iterdir() if p.is_dir()):
            for name in ("bbrv3.patch", "bbrv3-kabi.patch"):
                self.assertTrue((folder / name).is_file(), f"{folder.name}/{name}")

    def test_sublevel_picks_its_own_set_or_the_newest_below(self):
        # Issue #105: 6.1.141 moved tcp_in_ack_event(), so 141 needs its own set (138's no longer fits).
        self.assertEqual([picked(s) for s in (138, 140, 141, 144, 145, 176, 180)],
                         ["138", "138", "141", "141", "145", "176", "176"])

    def test_141_is_the_145_diff(self):
        # Same added and removed lines as the tested sets; only the header differs.
        for name in ("bbrv3.patch", "bbrv3-kabi.patch"):
            self.assertEqual(body(SETS / "141" / name), body(SETS / "145" / name))


if __name__ == "__main__":
    unittest.main()

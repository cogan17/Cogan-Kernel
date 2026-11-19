#!/usr/bin/env python3
"""Build time and release tag date in WIB (owner 2026-11-19); a disguised build keeps the stock kernel's UTC time."""
import re
import subprocess
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = (ROOT / "kernel/build.sh").read_text()
WORKFLOW = (ROOT / ".github/workflows/build-kernel.yml").read_text()
STAMP = BUILD.split('if [ "${DISGUISE:-false}" = "true" ]; then STAMP_TZ', 1)[1]
STAMP = 'if [ "${DISGUISE:-false}" = "true" ]; then STAMP_TZ' + STAMP.split("export KBUILD_BUILD_TIMESTAMP", 1)[0]
CHECK = textwrap.dedent(WORKFLOW.split('          if [ "$BUILD_TIME" != "N" ]; then\n', 1)[1].split("          fi\n", 1)[0])


def stamp(build_time="N", disguise="false"):
    script = 'fail() { echo "FAIL $*"; exit 1; }\n' + STAMP + 'echo "$KBUILD_BUILD_TIMESTAMP"'
    run = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                         env={"PATH": "/usr/bin:/bin", "BUILD_TIME": build_time, "DISGUISE": disguise})
    return run.stdout.strip()


def form_ok(build_time):
    return subprocess.run(["bash", "-c", CHECK], env={"PATH": "/usr/bin:/bin", "BUILD_TIME": build_time},
                          capture_output=True).returncode == 0


class BuildTimeTests(unittest.TestCase):
    def test_now_is_wib_and_a_disguise_keeps_utc(self):
        self.assertRegex(stamp(), r"^[A-Z][a-z]{2} [A-Z][a-z]{2} \d{2} \d{2}:\d{2}:\d{2} WIB \d{4}$")
        self.assertRegex(stamp(disguise="true"), r" UTC \d{4}$")

    def test_a_typed_time_in_wib_or_utc_lands_in_the_build_zone(self):
        self.assertEqual(stamp("Thu Jan 1 07:00:00 WIB 2026"), "Thu Jan 01 07:00:00 WIB 2026")
        self.assertEqual(stamp("Thu Jan 1 00:00:00 UTC 2026"), "Thu Jan 01 07:00:00 WIB 2026")
        self.assertEqual(stamp("Thu Jan 1 07:00:00 WIB 2026", disguise="true"), "Thu Jan 01 00:00:00 UTC 2026")
        self.assertIn("FAIL Invalid Build Time", stamp("kemarin sore"))

    def test_the_form_checks_the_weekday_in_the_written_zone(self):
        self.assertTrue(form_ok("Thu Jan 1 01:00:00 WIB 2026"))   # still Wednesday in UTC
        self.assertTrue(form_ok("Thu Jan 1 00:00:00 UTC 2026"))
        self.assertFalse(form_ok("Fri Jan 1 01:00:00 WIB 2026"))  # uutils date on the runner took this
        self.assertFalse(form_ok("Thu Jan 1 07:00:00 CET 2026"))
        self.assertFalse(form_ok("kemarin sore"))
        self.assertIn('description: "Build Time: N = sekarang (WIB) / now (WIB)"', WORKFLOW)

    def test_the_release_tag_date_is_wib_and_one_per_run(self):
        line = [l for l in BUILD.splitlines() if l.startswith('RELEASE_DATE="${RELEASE_DATE:-')][0]
        self.assertEqual(line, 'RELEASE_DATE="${RELEASE_DATE:-$(TZ=WIB-7 date +%y.%m.%d)}"')
        self.assertIn('RELEASE="v$RELEASE_DATE-$REVISION"', BUILD)
        self.assertIn('echo "release_date=$(TZ=WIB-7 date +%y.%m.%d)" >> "$GITHUB_OUTPUT"', WORKFLOW)
        self.assertIn("release_date: ${{ steps.plan.outputs.release_date }}", WORKFLOW)
        self.assertIn("RELEASE_DATE: ${{ needs.resolve.outputs.release_date }}", WORKFLOW)
        # 17:30 UTC is already the next day in WIB.
        run = subprocess.run(["bash", "-c", "TZ=WIB-7 date -d '2026-11-18 17:30 UTC' +%y.%m.%d"],
                             capture_output=True, text=True)
        self.assertEqual(run.stdout.strip(), "26.11.19")

    def test_the_real_identity_time_is_wib(self):
        self.assertTrue(re.search(r"TZ=WIB-7 date '\+%a %b %d %H:%M:%S WIB %Y'\)\" > drivers/misc/cogan_identity.h", BUILD))


if __name__ == "__main__":
    unittest.main()

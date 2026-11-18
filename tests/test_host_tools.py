#!/usr/bin/env python3
"""Host tools of the kernel build on a newer glibc (Builder run 44370376662, runner Ubuntu 26.04).

glibc 2.43 makes strchr() return const char * for a const argument; ACK 6.1's libbpf (built for
resolve_btfids with -Werror) assigns that to char *. build.sh keeps only that diagnostic a warning, for host
tools only: the flag goes through HOSTCFLAGS, never KCFLAGS."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = (ROOT / "kernel/build.sh").read_text()
FLAG = "-Wno-error=incompatible-pointer-types-discards-qualifiers"


class HostToolsTests(unittest.TestCase):
    def test_flag_is_for_host_tools_before_the_build(self):
        export = f'export HOSTCFLAGS="${{HOSTCFLAGS:+$HOSTCFLAGS }}{FLAG}"'
        self.assertIn(export, BUILD)
        self.assertLess(BUILD.index(export), BUILD.index('"${MAKE[@]}" gki_defconfig'))
        self.assertNotIn(FLAG, BUILD.split(export)[0])   # not in KCFLAGS or anything the kernel image uses

    @unittest.skipUnless(shutil.which("clang"), "no clang")
    def test_the_flag_keeps_werror_for_everything_else(self):
        code = "const char *f(const char *s); void g(const char *s) { char *p; p = f(s); (void)p; }\n"
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "t.c"
            src.write_text(code)
            compile_ = lambda *flags: subprocess.run(["clang", "-c", *flags, "-Werror", "-Wall", str(src), "-o",
                                                       str(Path(tmp) / "t.o")], capture_output=True, text=True)
            self.assertNotEqual(compile_().returncode, 0)          # libbpf's case, as on the runner
            self.assertEqual(compile_(FLAG).returncode, 0)         # a warning with the flag
            src.write_text(code + "int h(void) { int x; return x; }\n")
            self.assertNotEqual(compile_(FLAG).returncode, 0)      # other -Werror diagnostics still stop


if __name__ == "__main__":
    unittest.main()

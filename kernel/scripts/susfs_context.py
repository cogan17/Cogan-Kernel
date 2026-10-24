#!/usr/bin/env python3
"""Fit the newest SUSFS kernel patch to older ACK releases by context only (owner 2026-10-24).

simonpunk writes 50_add_susfs_in_gki-android14-6.1.patch against the newest ACK. A few lines that
newer ACK releases added serve only as context of its hunks, so older releases refuse the hunk
although nothing SUSFS adds depends on them. For a known line that the kernel source lacks, the
line is dropped from the context of that file's hunks (and the hunk header counts shrink by one).
Lines SUSFS adds or removes are never touched; any other mismatch still stops the build
("Tunggu simonpunk").

  fs/namespace.c   #include <trace/hooks/blk.h>   (ACK 6.1.157 and newer)

Usage: susfs_context.py PATCH KERNEL_SOURCE > ADAPTED_PATCH
Prints what was adapted to stderr.
"""
import re
import sys
from pathlib import Path

CONTEXT_ONLY = {"fs/namespace.c": ["#include <trace/hooks/blk.h>"]}
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def adapt(patch, source):
    """(adapted patch text, ["file: line", ...] dropped from the context)."""
    out, dropped, path, hunk, missing = [], [], None, None, []
    for line in patch.split("\n"):
        if line.startswith("diff --git "):
            path, hunk = line.split(" b/", 1)[1] if " b/" in line else None, None
            missing = [c for c in CONTEXT_ONLY.get(path, []) if not has_line(source / path, c)]
        elif line.startswith("@@"):
            hunk = len(out)
        if hunk is not None and line.startswith(" ") and line[1:] in missing:
            old, old_n, new, new_n, rest = HUNK.match(out[hunk]).groups()
            out[hunk] = f"@@ -{old},{int(old_n or 1) - 1} +{new},{int(new_n or 1) - 1} @@{rest}"
            dropped.append(f"{path}: {line[1:]}")
            continue
        out.append(line)
    return "\n".join(out), dropped


def has_line(path, wanted):
    return path.is_file() and wanted in path.read_text(errors="replace").splitlines()


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        sys.stderr.write(__doc__)
        return 2
    text, dropped = adapt(Path(args[0]).read_text(), Path(args[1]))
    sys.stdout.write(text)
    for item in dropped:
        sys.stderr.write(f"SUSFS context adapted (line not in this ACK release): {item}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

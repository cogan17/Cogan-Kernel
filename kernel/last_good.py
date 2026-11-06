#!/usr/bin/env python3
"""Pilih sumber: Stabil (terakhir berhasil) / Stable (last good build) (owner 2026-11-06).

The Builder's form offers two sources: always the newest versions (kernel/resolve.py, which waits when one
does not fit yet), or the exact components of the newest build of that root manager that passed build and
the KMI gate, read from the permanent records in kernel/history/ (kernel/build_history.py). Every component
comes from that one build: ACK release, root manager and its manager APK, SUSFS, sidex15 module, NoMount,
Baseband Guard, AnyKernel3, Neutron clang and the Unicode fix; they built together before, so they build
again. Only the ACK sublevels that passed in that run can be picked.

The run picked is the newest one on main whose build of this root matches the form: SUSFS ticked or not, and
NoMount, Baseband Guard and the Unicode fix present when ticked (a feature unticked in the form is left out).
Official CI artifacts (the manager of KernelSU, KernelSU Next or BakaSU main, the sidex15 module) are kept
90 days by GitHub: an expired one stops with a message instead of a failed download later.

Usage: last_good.py --root KSUN|BSU|KSU|SUKI|CSU [--sublevel lts|N|N,M|semua] [--no-susfs] [--unicode]
                    [--no-nomount] [--no-bbg] --out FILE.json
Exit 0 with the snapshot, 2 with {"wait": ...} when no build fits, 1 on an error.
"""
import argparse
import copy
import json
import re
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_history  # noqa: E402
import resolve  # noqa: E402

FEATURES = {"nomount": "NoMount", "bbg": "Baseband Guard", "unicode": "Unicode fix"}


class NotFound(Exception):
    """(Indonesian, English) of why no last good build fits the form."""

    def __init__(self, id_text, en_text):
        super().__init__(en_text)
        self.id_text, self.en_text = id_text, en_text


def has_susfs(snap):
    return snap.get("susfs_box", "susfs" in snap) and "susfs" in snap


def fits(snap, susfs_box, wanted):
    return has_susfs(snap) == susfs_box and all(feature in snap for feature in wanted)


def wanted_sublevels(text, available):
    """The sublevels picked from those that passed: lts = the newest, semua/empty = all, N or N,M = those."""
    text = text.strip().lower().replace(" ", "")
    if text in ("", "semua", "all"):
        return sorted(available)
    if text == "lts":
        return [max(available)]
    if not re.fullmatch(r"\d+(,\d+)*", text):
        raise ValueError("Kernel Sublevel: lts, a number such as 176, several (162,172) or semua")
    numbers = sorted({int(n) for n in text.split(",")})
    missing = [n for n in numbers if n not in available]
    if missing:
        have = ", ".join(f"6.1.{n}" for n in sorted(available))
        raise NotFound(f"Stabil: 6.1.{', 6.1.'.join(map(str, missing))} tidak ada di build terakhir yang berhasil (ada: {have}).",
                       f"Stable: 6.1.{', 6.1.'.join(map(str, missing))} is not in the last good build (it has: {have}).")
    return numbers


def pick(records, root, sublevel="lts", susfs_box=True, unicode=False, nomount=True, bbg=True):
    """The snapshot of the newest build of root on main that matches the form, with its source noted."""
    wanted = [name for name, on in (("nomount", nomount), ("bbg", bbg), ("unicode", unicode)) if on]
    name = build_history.ROOTS[root]
    for run in sorted(records, key=lambda r: (r["id"], r["attempt"]), reverse=True):
        if run.get("branch") != "main":
            continue
        passed = [b for b in run["builds"] if b["root"] == root and b["status"] == "ok" and fits(b["snap"], susfs_box, wanted)]
        if not passed:
            continue
        by_sublevel = {b["sublevel"]: b for b in passed}
        snap = copy.deepcopy(passed[0]["snap"])
        for feature in FEATURES:
            if feature not in wanted:
                snap.pop(feature, None)
        snap["ack"] = [by_sublevel[n]["snap"]["ack"][0] for n in wanted_sublevels(sublevel, by_sublevel)]
        snap["source"] = {"kind": "stable", "run": run["number"], "run_id": run["id"], "url": run["url"], "date": run["date"],
                          "record": build_history.filename(run)}
        return snap
    box = "dengan SUSFS" if susfs_box else "tanpa SUSFS"
    box_en = "with SUSFS" if susfs_box else "without SUSFS"
    extra = ", ".join(FEATURES[f] for f in wanted)
    raise NotFound(f"Stabil: belum ada build {name} {box} yang berhasil di main" + (f" (dengan {extra})" if extra else "") +
                   ". Pakai Selalu terbaru (CI), atau sesuaikan centang fitur.",
                   f"Stable: no successful {name} build {box_en} on main yet" + (f" (with {extra})" if extra else "") +
                   ". Use Always newest (CI), or change the feature boxes.")


def artifacts(snap):
    """(label, repo, artifact id) of the official CI artifacts the build will download."""
    found = []
    manager = snap.get("manager", {})
    if manager.get("kind") in ("ci", "ksun-ci"):
        found += [(f"manager {key}", manager["repo"], manager[key]) for key in ("manager", "spoofed") if key in manager]
    if "artifact" in snap.get("susfs_sidex", {}):
        found.append(("sidex15 SUSFS module", snap["susfs_sidex"]["repo"], snap["susfs_sidex"]["artifact"]))
    return found


def check_artifacts(snap, api=resolve.api):
    """Stop early when an official CI artifact of the last good build has expired (GitHub keeps them 90 days)."""
    for label, repo, artifact in artifacts(snap):
        try:
            expired = api(f"repos/{repo}/actions/artifacts/{artifact}").get("expired", False)
        except urllib.error.HTTPError as error:
            expired = error.code in (404, 410)
            if not expired:
                raise
        if expired:
            source = snap["source"]
            raise NotFound(f"Stabil: {label} dari build terakhir yang berhasil (run #{source['run']}) sudah kedaluwarsa "
                           "(GitHub menyimpan artifact CI 90 hari). Pakai Selalu terbaru (CI).",
                           f"Stable: the {label} of the last good build (run #{source['run']}) has expired "
                           "(GitHub keeps CI artifacts 90 days). Use Always newest (CI).")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", choices=sorted(build_history.ROOTS), required=True)
    parser.add_argument("--sublevel", default="lts")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-susfs", action="store_true")
    parser.add_argument("--unicode", action="store_true")
    parser.add_argument("--no-nomount", action="store_true")
    parser.add_argument("--no-bbg", action="store_true")
    parser.add_argument("--history", type=Path, default=build_history.DIRECTORY)
    parser.add_argument("--no-artifact-check", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        snap = pick(build_history.load(args.history), args.root, args.sublevel, not args.no_susfs, args.unicode,
                    not args.no_nomount, not args.no_bbg)
        if not args.no_artifact_check:
            check_artifacts(snap)
    except NotFound as missing:
        args.out.write_text(json.dumps({"root": args.root, "wait": {"id": missing.id_text, "en": missing.en_text}}, indent=1))
        print(f"WAIT: {missing.en_text}")
        return 2
    except (OSError, ValueError, KeyError) as exc:
        print(f"::error::{args.root}: {exc}")
        return 1
    args.out.write_text(json.dumps(snap, indent=1))
    print(json.dumps(snap, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

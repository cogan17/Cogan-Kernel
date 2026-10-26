#!/usr/bin/env python3
"""Supported ACK sublevels: record build results, write the README table.

kernel/sublevels.json is a record of what the Cogan Kernel Builder proved, not a lock: no build
reads it. Per sublevel: the ACK release tag, and per root manager (KSUN, BSU) the result of the
newest run that built it (ok, gagal, tunggu with whom to wait for). "pendahulu" marks sublevels
proven only in the predecessor repository. The README row follows the newest result here: built,
waiting for an upstream update, or (nothing built here yet) proven in the predecessor; a sublevel
that failed here is not listed. Recording is started by hand (workflow Catat sublevel); newest
versions, new ACK releases too, are checked by Cek pembaruan (kernel/updates.py), which builds
nothing (owner 2026-10-26: one check, not two).

Usage: sublevels.py record --info DIR --snapshots DIR --run RUN_ID
       sublevels.py readme
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD = HERE / "sublevels.json"
READMES = {"id": HERE.parent / "README.md", "en": HERE.parent / "README.en.md"}
START, END = "<!-- sublevel:start -->", "<!-- sublevel:end -->"
ROOTS = {"KSUN": "KernelSU Next", "BSU": "BakaSU"}
WORDS = {"id": {"head": "| Sublevel | Rilis ACK | Status |", "ok": "✅ {roots}: [build + gate KMI]({url})",
                "tunggu": "⏳ {roots}: [{why}]({url})", "pendahulu": "🧪 lolos build + gate KMI di repo pendahulu"},
         "en": {"head": "| Sublevel | ACK release | Status |", "ok": "✅ {roots}: [build + KMI gate]({url})",
                "tunggu": "⏳ {roots}: [{why}]({url})",
                "pendahulu": "🧪 passed build + KMI gate in the predecessor repository"}}


def load(path=RECORD):
    return json.loads(path.read_text()) if path.is_file() else {}


def save(record, path=RECORD):
    ordered = {key: record[key] for key in sorted(record, key=int, reverse=True)}
    path.write_text(json.dumps(ordered, indent=1, ensure_ascii=False) + "\n")


# ---- recording a Builder run ------------------------------------------------------------------

def outcome(folder):
    """(ok, gagal or tunggu, ACK tag, whom to wait for) from the files a build left behind
    (see kernel/run_summary.py)."""
    env = dict(line.split("=", 1) for line in (folder / "build.env").read_text().splitlines() if "=" in line) \
        if (folder / "build.env").is_file() else {}
    if env.get("ZIP_SHA256"):
        return "ok", env.get("ACK_TAG", ""), None
    if (folder / "wait.json").is_file():
        return "tunggu", "", json.loads((folder / "wait.json").read_text())
    return "gagal", "", None


def snapshot_tags(snapshots):
    """{sublevel: ACK tag} the run planned, from its resolve snapshots (also for failed builds)."""
    tags = {}
    for path in snapshots.glob("*.json") if snapshots else []:
        for ack in json.loads(path.read_text()).get("ack", []):
            tags[str(ack["sublevel"])] = ack["tag"]
    return tags


def record_run(record, info, run_id, tags=None):
    """Update the record from one Builder run's build-info-<root>-<sublevel> folders."""
    changed = []
    for folder in sorted(info.glob("build-info-*-*")):
        match = re.fullmatch(r"build-info-(KSUN|BSU)-(\d+)", folder.name)
        if not match:
            continue
        root, sublevel = match[1], match[2]
        status, tag, wait = outcome(folder)
        entry = record.setdefault(sublevel, {})
        tag = tag or (tags or {}).get(sublevel) or entry.get("tag", "")
        if entry.get("tag") and tag and entry["tag"] != tag:
            entry = record[sublevel] = {k: v for k, v in entry.items() if k == "note"}  # a newer release of it
        entry["tag"] = tag
        if status == "ok":
            entry.pop("pendahulu", None)  # proven in this repository now
        entry[root] = {"status": status, "run": int(run_id), **({"wait": wait} if wait else {})}
        changed.append((sublevel, ROOTS[root], status))
    return changed


# ---- README table -----------------------------------------------------------------------------

def table(record, lang, repo="cogan17/Cogan-Kernel"):
    w = WORDS[lang]
    rows, lts = [], max((int(s) for s in record if shown(record[s])), default=None)
    for sublevel in sorted(record, key=int, reverse=True):
        entry = record[sublevel]
        if not shown(entry):
            continue
        status = w["pendahulu"]
        for kind in ("ok", "tunggu"):
            found = [r for r in ROOTS if entry.get(r, {}).get("status") == kind]
            if found:
                run = max(entry[r]["run"] for r in found)
                why = entry[found[0]].get("wait", {}).get(lang, "").rstrip(".")
                status = w[kind].format(roots=" · ".join(ROOTS[r] for r in found), why=why,
                                        url=f"https://github.com/{repo}/actions/runs/{run}")
                break
        note = entry.get("note", {}).get(lang)
        name = f"**{sublevel}** (`lts`)" if int(sublevel) == lts else sublevel
        tag = entry.get("tag", "").replace("android14-6.1-", "")
        rows.append(f"| {name} | `{tag}` | {status}{f' · {note}' if note else ''} |")
    return "\n".join([w["head"], "|---|---|---|", *rows])


def shown(entry):
    """Built or waiting here, or not built here yet but proven in the predecessor."""
    results = [entry[r]["status"] for r in ROOTS if r in entry]
    return "ok" in results or "tunggu" in results or (entry.get("pendahulu") and not results)


def write_readmes(record, paths=READMES):
    changed = []
    for lang, path in paths.items():
        text = path.read_text()
        start, end = text.index(START) + len(START), text.index(END)
        new = text[:start] + "\n" + table(record, lang) + "\n" + text[end:]
        if new != text:
            path.write_text(new)
            changed.append(path.name)
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["record", "readme"])
    parser.add_argument("--info", type=Path)
    parser.add_argument("--snapshots", type=Path)
    parser.add_argument("--run")
    args = parser.parse_args(argv)
    record = load()
    if args.command == "record":
        for sublevel, root, status in record_run(record, args.info, args.run, snapshot_tags(args.snapshots)):
            print(f"6.1.{sublevel} {root}: {status}")
        save(record)
    print("README:", ", ".join(write_readmes(load())) or "unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())

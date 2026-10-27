#!/usr/bin/env python3
"""Permanent Builder records in kernel/history/run-<id>-<attempt>.md.

Each Markdown file contains a readable table and its original metadata in a marked JSON block.
The Builder writes its own record; Cek pembaruan only reads. Cleanup is independent and unchanged.
No kernel, APK or log is stored here. Writes merge on a contents-API SHA conflict, without a branch
or force push. Different runs have different files, so concurrent runs cannot replace one another.
"""
import argparse
import base64
import copy
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent / "history"
START, END = "<!-- cogan-history:start -->", "<!-- cogan-history:end -->"
ROOTS = {"KSUN": "KernelSU Next", "BSU": "BakaSU"}
IDENTITY = {"name": "Cogan", "email": "79615344+cogan17@users.noreply.github.com"}


def filename(run):
    return f"run-{run['id']}-{run['attempt']}.md"


def parse(text):
    data = json.loads(text.split(START + "\n```json\n", 1)[1].split("\n```\n" + END, 1)[0])
    if data.get("schema") != 1 or not isinstance(data.get("id"), int) or not isinstance(data.get("attempt"), int) or not isinstance(data.get("builds"), list):
        raise ValueError("Invalid Builder history / riwayat Builder tidak valid")
    return data


def load(directory=DIRECTORY):
    return [parse(path.read_text()) for path in sorted(directory.glob("run-*.md"))]


def merge(old, new):
    """Enrich the same run/attempt; an incomplete repeat cannot erase a successful result."""
    if (old["id"], old["attempt"]) != (new["id"], new["attempt"]):
        raise ValueError("Different Builder runs / run Builder berbeda")
    builds = {(b["root"], b.get("sublevel", 0)): copy.deepcopy(b) for b in old["builds"]}
    for build in new["builds"]:
        key = build["root"], build.get("sublevel", 0)
        if builds.get(key, {}).get("status") != "ok" or build["status"] == "ok":
            builds[key] = copy.deepcopy(build)
    return {**old, **new, "builds": [builds[key] for key in sorted(builds)]}


def collect(run, info, snapshots):
    """Keep only the successful ACK sublevels, not the entire plan from a resolve snapshot."""
    if run["path"].split("@")[0] != ".github/workflows/build-kernel.yml":
        raise ValueError("Not a Builder run / bukan run Builder")
    record = {"schema": 1, "id": run["id"], "attempt": run.get("run_attempt", 1), "number": run["run_number"],
              "url": run["html_url"], "date": run["created_at"], "sha": run["head_sha"], "branch": run["head_branch"], "builds": []}
    for path in sorted(snapshots.glob("*.json")):
        snap = json.loads(path.read_text())
        root = snap.get("root")
        if root not in ROOTS:
            continue
        if "wait" in snap:
            record["builds"].append({"root": root, "status": "wait", "wait": snap["wait"]})
            continue
        for ack in snap.get("ack", []):
            folder = info / f"build-info-{root}-{ack['sublevel']}"
            env_path = folder / "build.env"
            env = dict(line.split("=", 1) for line in env_path.read_text().splitlines() if "=" in line) if env_path.is_file() else {}
            ok = bool(re.fullmatch(r"[0-9a-f]{64}", env.get("ZIP_SHA256", "")))
            if ok and (env.get("ROOT_COMMIT") != snap["root_source"]["commit"] or env.get("ACK_TAG") != ack["tag"]):
                raise ValueError(f"Snapshot and build info differ / snapshot berbeda: {root} {ack['sublevel']}")
            saved = {**copy.deepcopy(snap), "ack": [ack]}
            for field, setting in (("nomount", "NOMOUNT"), ("bbg", "BBG_COMMIT"), ("unicode", "UNICODE_FIX")):
                if env.get(setting) == "-":
                    saved.pop(field, None)
            wait = folder / "wait.json"
            entry = {"root": root, "sublevel": ack["sublevel"], "status": "ok" if ok else "wait" if wait.is_file() else "failed", "snap": saved, "env": env}
            if wait.is_file() and not ok:
                entry["wait"] = json.loads(wait.read_text())
            record["builds"].append(entry)
    return record


def markdown(run):
    date = datetime.fromisoformat(run["date"].replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=7)))
    lines = [f"# Builder #{run['number']} · run {run['id']} · attempt {run['attempt']}", "",
             f"Sumber / Source: [Builder]({run['url']}) · `{run['sha']}` · branch `{run['branch']}`", "",
             f"Waktu mulai / Started: {date:%Y-%m-%d %H:%M} WIB", "",
             "Catatan ini tetap ada setelah log, artifact atau run dihapus. "
             "Cek pembaruan membaca metadata di bawah; catatan ini tidak menentukan versi build berikutnya.", "",
             "This record survives deletion of logs, artifacts or the run. "
             "Check for updates reads the metadata below; this record never selects the next build's versions.", "",
             "| Root | Kernel | Hasil / Result | ACK | Root commit | SUSFS | NoMount |", "|---|---|---|---|---|---|---|"]
    for build in run["builds"]:
        snap = build.get("snap", {})
        result = {"ok": "✅ Build + KMI", "failed": "❌ Gagal / Failed", "wait": "⏳ Tunggu / Waiting"}[build["status"]]
        ack = ", ".join(a["tag"] for a in snap.get("ack", []))
        lines.append(f"| {ROOTS[build['root']]} | {('6.1.' + str(build['sublevel'])) if build.get('sublevel') else '-'} | {result} | {ack or '-'} | "
                     f"{snap.get('root_source', {}).get('commit', '-')[:12]} | {snap.get('susfs', {}).get('commit', '-')[:12]} | {snap.get('nomount', {}).get('tag', '-')} |")
    if run.get("restored_from"):
        lines += ["", "Dipulihkan dari bukti yang masih tersedia / Restored from retained evidence:", "",
                  *[f"- {url}" for url in run["restored_from"]], "",
                  "Hanya data yang terbukti disimpan; field yang tidak tersedia tidak ditebak. / Only proven data is recorded; unavailable fields are not guessed."]
    lines += ["", "<details><summary>Metadata untuk sinkronisasi / Sync metadata</summary>", "", START, "```json",
              json.dumps(run, indent=2, ensure_ascii=False), "```", END, "", "</details>", ""]
    return "\n".join(lines)


def latest(records, repo):
    """Newest successful build per root on main, unaffected by a later failure, wait or other branch."""
    found = {}
    for run in sorted(records, key=lambda v: (v["id"], v["attempt"]), reverse=True):
        if run.get("branch") != "main":
            continue
        for root in ROOTS:
            passed = [b for b in run["builds"] if b["root"] == root and b["status"] == "ok"]
            if root in found or not passed:
                continue
            snap = copy.deepcopy(passed[0]["snap"])
            snap["ack"] = [ack for build in passed for ack in build["snap"].get("ack", [])]
            found[root] = {"run": run["number"], "run_id": run["id"], "url": run["url"], "date": run["date"], "snap": snap,
                           "record_url": f"https://github.com/{repo}/blob/main/kernel/history/{filename(run)}", "env": passed[0].get("env", {})}
    return found


def api(path, payload=None):
    command = ["gh", "api", path]
    if payload is not None:
        command += ["--method", "PUT", "--input", "-"]
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)


def persist(repo, record, call=api):
    """One Markdown file per run/attempt, in main, author and committer = owner."""
    path = f"repos/{repo}/contents/kernel/history/{filename(record)}"
    for attempt in range(3):
        sha, previous = None, None
        try:
            file = call(path + "?ref=main")
            previous = parse(base64.b64decode(file["content"]).decode())
            sha = file["sha"]
        except RuntimeError as exc:
            if "HTTP 404" not in str(exc):
                raise
        combined = merge(previous, record) if previous else record
        if combined == previous:
            return False
        payload = {"message": f"docs(build): catat Builder run {record['id']}", "branch": "main", "author": IDENTITY, "committer": IDENTITY,
                   "content": base64.b64encode(markdown(combined).encode()).decode()}
        if sha:
            payload["sha"] = sha
        try:
            call(path, payload)
            return True
        except RuntimeError as exc:
            if attempt == 2 or not any(code in str(exc) for code in ("HTTP 409", "HTTP 422")):
                raise
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--info", type=Path, required=True)
    parser.add_argument("--snapshots", type=Path, required=True)
    args = parser.parse_args(argv)
    run = api(f"repos/{args.repo}/actions/runs/{args.run}")
    if run["head_branch"] != "main":
        print("History: main builds only / hanya build dari main")
        return 0
    record = collect(run, args.info, args.snapshots)
    persist(args.repo, record)
    print(f"Riwayat tersimpan / History saved: kernel/history/{filename(record)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

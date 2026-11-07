#!/usr/bin/env python3
"""CoganSU in one step (owner 2026-11-07: "buat jadi satu langkah pakai PAT"): when the newest CoganSU release
lacks the newest KernelSU main, or SUSFS needs a newer CoganSU (resolve.BuildFirst), the Builder runs
"Build CoganSU" on cogan17/CoganSU itself (it merges KernelSU main by itself), waits for it, and resolves again.

    cogansu_auto.py need SNAPSHOT                prints why a new CoganSU build is needed; exit 0 yes, 1 no
    cogansu_auto.py build --release-type TYPE    run Build CoganSU on main and wait; exit 0 when it succeeded

The token is a fine-grained PAT in the secret COGANSU_TOKEN (repository cogan17/CoganSU, Actions: read and
write); GITHUB_TOKEN cannot start a workflow of another repository. Steps: docs/cogansu-token.md.
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

REPO = "cogan17/CoganSU"
WORKFLOW = "build-cogansu.yml"
API = "https://api.github.com/"
# Cogan Kernel's Release Type → the CoganSU release it needs: a CI kernel build makes a Pre-Release.
RELEASE_TYPES = {"CI": "Pre-Release", "Pre-Release": "Pre-Release", "Release": "Release"}


class Stop(Exception):
    """(Indonesian, English): the automatic Build CoganSU could not be done."""

    def __init__(self, id_text, en_text):
        super().__init__(en_text)
        self.id_text, self.en_text = id_text, en_text


def need(snap):
    """(id, en) of why the CoganSU snapshot needs a new Build CoganSU, or None."""
    wait = snap.get("wait") or {}
    if wait.get("kind") == "build-first":
        return wait["id"], wait["en"]
    src = snap.get("root_source") or {}
    if src.get("kernelsu_main") and src.get("kernelsu_in_release") is False:
        short = src["kernelsu_main"][:12]
        return (f"Rilis CoganSU {src.get('tag')} belum memuat KernelSU main `{short}`.",
                f"CoganSU release {src.get('tag')} does not carry KernelSU main `{short}` yet.")
    return None


def call(method, path, token, body=None):
    """(HTTP status, JSON or None) of a GitHub API call with the CoganSU token."""
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(API + path, data=data, method=method, headers={
        "Accept": "application/vnd.github+json", "Authorization": "Bearer " + token,
        "User-Agent": "cogan-rothko-builder", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            text = response.read()
            return response.status, json.loads(text) if text else None
    except urllib.error.HTTPError as error:
        return error.code, None


def token_problem(status):
    return Stop(f"COGANSU_TOKEN ditolak GitHub (HTTP {status}): token kedaluwarsa atau izinnya kurang "
                f"(perlu repositori {REPO}, Actions: Read and write). Lihat docs/cogansu-token.md.",
                f"GitHub refused COGANSU_TOKEN (HTTP {status}): expired or missing permission "
                f"(repository {REPO}, Actions: Read and write). See docs/cogansu-token.md.")


def utc(stamp):
    return datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def build(token, release_type, api=call, sleep=time.sleep, now=None, timeout=3600, every=30):
    """Run Build CoganSU on main (empty Build Revision = its run number) and wait; returns the finished run."""
    now = now or (lambda: datetime.datetime.now(datetime.timezone.utc))
    started = now() - datetime.timedelta(seconds=30)
    status, _ = api("POST", f"repos/{REPO}/actions/workflows/{WORKFLOW}/dispatches", token,
                    {"ref": "main", "inputs": {"release_type": release_type, "build_revision": ""}})
    if status not in (200, 204):   # 204 No Content; newer API versions may answer 200 with the run
        raise token_problem(status)
    run = None
    for _ in range(20):   # the dispatched run shows up within seconds
        sleep(6)
        status, data = api("GET", f"repos/{REPO}/actions/workflows/{WORKFLOW}/runs?event=workflow_dispatch"
                                  f"&branch=main&per_page=10", token)
        if status != 200:
            raise token_problem(status)
        fresh = [r for r in (data or {}).get("workflow_runs", []) if utc(r["created_at"]) >= started]
        if fresh:
            run = min(fresh, key=lambda r: r["created_at"])
            break
    if not run:
        raise Stop("Build CoganSU sudah diminta tetapi run-nya tidak muncul di cogan17/CoganSU.",
                   "Build CoganSU was requested but its run did not show up in cogan17/CoganSU.")
    print(f"Build CoganSU: {run['html_url']}", flush=True)
    waited = 0
    while run.get("status") != "completed":
        if waited >= timeout:
            raise Stop(f"Build CoganSU belum selesai setelah {timeout // 60} menit: {run['html_url']}",
                       f"Build CoganSU did not finish within {timeout // 60} minutes: {run['html_url']}")
        sleep(every)
        waited += every
        status, data = api("GET", f"repos/{REPO}/actions/runs/{run['id']}", token)
        if status != 200:
            raise token_problem(status)
        run = data
    if run.get("conclusion") != "success":
        raise Stop(f"Build CoganSU gagal ({run.get('conclusion')}): {run['html_url']}. Baca log run itu.",
                   f"Build CoganSU failed ({run.get('conclusion')}): {run['html_url']}. Read that run's log.")
    return run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("need")
    check.add_argument("snapshot")
    run = sub.add_parser("build")
    run.add_argument("--release-type", choices=sorted(RELEASE_TYPES), required=True)
    run.add_argument("--summary", default=os.environ.get("GITHUB_STEP_SUMMARY"))
    args = parser.parse_args(argv)
    if args.command == "need":
        with open(args.snapshot) as handle:
            reason = need(json.load(handle))
        if reason:
            print(reason[0])
        return 0 if reason else 1
    token = os.environ.get("COGANSU_TOKEN", "")
    release_type = RELEASE_TYPES[args.release_type]
    try:
        if not token:
            raise Stop("Secret COGANSU_TOKEN belum ada, jadi Build CoganSU tidak bisa dijalankan otomatis. "
                       "Lihat docs/cogansu-token.md, atau jalankan Build CoganSU sendiri lebih dulu.",
                       "Secret COGANSU_TOKEN is missing, so Build CoganSU cannot run automatically. "
                       "See docs/cogansu-token.md, or run Build CoganSU yourself first.")
        finished = build(token, release_type)
    except Stop as stop:
        print(f"::error::{stop.id_text} / {stop.en_text}")
        if args.summary:
            with open(args.summary, "a") as out:
                out.write(f"\n> [!CAUTION]\n> ❌ **CoganSU:** {stop.id_text}\n>\n> 🇬🇧 {stop.en_text}\n")
        return 1
    if args.summary:
        with open(args.summary, "a") as out:
            out.write(f"\n> [!NOTE]\n> 🔄 **CoganSU** dibangun otomatis ({release_type}) agar memuat KernelSU terbaru: "
                      f"[Build CoganSU]({finished['html_url']}).\n>\n> 🇬🇧 CoganSU was built automatically "
                      f"({release_type}) to carry the newest KernelSU.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

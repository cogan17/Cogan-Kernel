#!/usr/bin/env python3
"""Newest version of every component of a rothko build, and whom to wait for when one does not fit.

No lock, pin or frozen tree (owner 2026-10-23): every run takes the newest official ACK
android14-6.1 release, the newest KernelSU Next (pershoot dev-susfs) or BakaSU release (BakaSU main
while its newest release does not take the newest SUSFS yet), the newest SUSFS, NoMount release,
Baseband Guard, AnyKernel3 and Neutron clang. The commits found here are
the run's snapshot, passed to every build job so they all build the same thing.

When the newest version cannot work on rothko yet, the variant is not built and the summary says
whom to wait for, in Indonesian and English. The KMI gate of the build is not part of this: it
always runs and fails closed.

--unicode (the Unicode fix box, off by default) also takes the newest commit of WildKernel's
kernel_patches for its unicode bypass fix; without it nothing of WildKernel is read.

Usage: resolve.py --root KSUN|BSU [--sublevel lts|N|N,M|semua] [--unicode] --out FILE.json
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ACK = "https://android.googlesource.com/kernel/common"
ACK_TAG = re.compile(r"android14-6\.1-(\d{4})-(\d{2})_r(\d+)")
ACK_SINCE = (2025, 6)  # the phone's own release (6.1.138, 2025-06_r11); older ones predate its vendor modules
KSUN_FORK = "https://github.com/pershoot/KernelSU-Next"
KSUN_FORK_BRANCH = "dev-susfs"
KSUN_CI = ("KernelSU-Next/KernelSU-Next", "build-manager-ci.yml", {"manager": "manager", "spoofed": "manager-spoofed"})
BAKASU = "https://github.com/Baka-SU/BakaSU"
# BakaSU's official CI builds the manager of every main commit with its release key, like its releases.
BAKASU_CI = ("Baka-SU/BakaSU", "build-manager.yml", {"manager": "Manager-release", "spoofed": "Spoofed-Manager-release"})
SUSFS = "https://gitlab.com/simonpunk/susfs4ksu"
SUSFS_BRANCH = "gki-android14-6.1"
SUSFS_PATCH = "kernel_patches/50_add_susfs_in_gki-android14-6.1.patch"
NOMOUNT = "https://github.com/maxsteeel/nomount"
BBG = "https://github.com/vc-teahouse/Baseband-guard"
ANYKERNEL = "https://github.com/osm0sis/AnyKernel3"
NEUTRON = "Neutron-Toolchains/clang-build-catalogue"
# The patch touches only fs/unicode/utf8-norm.c. That file is the same in Linux stable 6.1 to 6.1.190
# (kernel.org, not ACK) and in ACK 6.1.138; proven on ACK 6.1.138 (local) and 6.1.176 (CI). Other ACK
# releases are expected to fit; a release where it does not stops the build (wait for WildKernel).
UNICODE_FIX = "https://github.com/WildKernels/kernel_patches"
UNICODE_FIX_PATCH = "common/unicode_bypass_fix_6.1+.patch"
RELEASE = re.compile(r"v(\d+)\.(\d+)\.(\d+)(?:-rc(\d+))?")
STABLE = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
# Root-driver hooks a SUSFS kernel patch may call; BakaSU must define them as global functions.
HOOKS = ("my_setprocattr", "my_write_context", "my_write_access", "ksu_setup_preinit_file",
         "ksu_preinit_handle_post_execveat")


class Wait(Exception):
    """A component is not ready for rothko yet: (Indonesian, English) of whom to wait for."""

    def __init__(self, id_text, en_text):
        super().__init__(en_text)
        self.id_text, self.en_text = id_text, en_text


def run(*cmd, cwd=None, timeout=900):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True, timeout=timeout).stdout


def ls_remote(url, *patterns):
    """{ref: commit}, annotated tags peeled to their commit."""
    refs = {}
    for line in run("git", "ls-remote", url, *patterns).splitlines():
        sha, ref = line.split("\t")
        if ref.endswith("^{}"):
            refs[ref[:-3]] = sha
        else:
            refs.setdefault(ref, sha)
    return refs


def http(url, token=None, attempts=3, sleep=time.sleep):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "cogan-rothko-builder"}
    if token and "api.github.com" in url:
        headers["Authorization"] = "Bearer " + token
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            # googlesource answers 429 when asked too often: wait as it says, then try again.
            if error.code not in (429, 503) or attempt == attempts:
                raise
            retry = error.headers.get("Retry-After", "") if error.headers else ""
            sleep(int(retry) if retry.isdigit() else 15 * attempt)


def api(path):
    return json.loads(http("https://api.github.com/" + path, os.environ.get("GH_TOKEN")))


# ---- ACK ------------------------------------------------------------------------------------

def ack_releases(refs):
    """[(tag, commit)] of android14-6.1 releases since the phone's own, newest first."""
    found = []
    for ref, sha in refs.items():
        match = ACK_TAG.fullmatch(ref.removeprefix("refs/tags/"))
        if match and (int(match[1]), int(match[2])) >= ACK_SINCE:
            found.append(((int(match[1]), int(match[2]), int(match[3])), match[0], sha))
    return [(tag, sha) for _, tag, sha in sorted(found, reverse=True)]


def ack_sublevel(tag, fetch=http):
    text = base64.b64decode(fetch(f"{ACK}/+/refs/tags/{tag}/Makefile?format=TEXT")).decode()
    return int(re.search(r"^SUBLEVEL = (\d+)$", text, re.MULTILINE)[1])


def pick_ack(releases, wanted, sublevel_of=ack_sublevel):
    """[(tag, commit, sublevel)]: lts = the newest release; N or N,M = the newest release of each
    sublevel; semua = the newest release of every sublevel since the phone's own."""
    wanted = wanted.strip().lower() or "lts"
    if not releases:
        raise ValueError("no android14-6.1 release found")
    if wanted == "lts":
        tag, sha = releases[0]
        return [(tag, sha, sublevel_of(tag))]
    numbers = None
    if wanted != "semua":
        if not re.fullmatch(r"\d+(,\d+)*", wanted.replace(" ", "")):
            raise ValueError("Kernel Sublevel: lts, a number such as 176, several (162,172) or semua")
        numbers = {int(n) for n in wanted.replace(" ", "").split(",")}
    picked, months = {}, set()
    for tag, sha in releases:  # newest first: the first release of a sublevel is its newest
        # Every _rN of a month comes from that month's release branch, at the same sublevel:
        # read one Makefile per month (googlesource refuses too many requests, HTTP 429).
        month = tag.rsplit("_r", 1)[0]
        if month in months:
            continue
        months.add(month)
        sublevel = sublevel_of(tag)
        if sublevel not in picked and (numbers is None or sublevel in numbers):
            picked[sublevel] = (tag, sha, sublevel)
        if numbers is not None and numbers <= picked.keys():
            break
    if numbers is not None and numbers - picked.keys():
        missing = ", ".join(f"6.1.{n}" for n in sorted(numbers - picked.keys()))
        raise ValueError(f"no official android14-6.1 release since 2025-06 has sublevel {missing}")
    return [picked[n] for n in sorted(picked)]


# ---- root managers and SUSFS ----------------------------------------------------------------

def release_key(tag):
    match = RELEASE.fullmatch(tag)
    if not match:
        return None
    major, minor, patch, rc = match.groups()
    return (int(major), int(minor), int(patch), int(rc) if rc else 10**6)  # final after its rcs


def newest_tag(refs, pattern=RELEASE):
    tags = [(release_key(ref.removeprefix("refs/tags/")), ref.removeprefix("refs/tags/"), sha)
            for ref, sha in refs.items() if pattern.fullmatch(ref.removeprefix("refs/tags/"))]
    if not tags:
        raise ValueError("no release tag")
    _, tag, sha = max(tags)
    return tag, sha


def fetch_history(repo, url, *refspecs):
    run("git", "-C", repo, "fetch", "-q", "--filter=tree:0", url, *refspecs)


def ksun_version(repo, head, base_branch):
    """(base commit, KSU_VERSION) the way the fork's Kbuild counts it: the merge-base of HEAD with
    origin/<base branch>, 30000 + its commit count. The official manager of that commit matches."""
    base = run("git", "-C", repo, "merge-base", head, base_branch).strip()
    return base, 30000 + int(run("git", "-C", repo, "rev-list", "--count", base).strip())


def ci_manager(ci, run_info, api=api):
    """Manager artifacts of one official CI run, or None when its manager is gone (expired)."""
    repo, _, names = ci
    # BakaSU's runs have 30 artifacts, the API's default page: ask for 100.
    listed = api(f"repos/{repo}/actions/runs/{run_info['id']}/artifacts?per_page=100")["artifacts"]
    artifacts = {a["name"]: a for a in listed if not a["expired"]}
    if names["manager"] not in artifacts:
        return None
    return {"repo": repo, "run": run_info["id"], "url": run_info["html_url"],
            **{key: artifacts[name]["id"] for key, name in names.items() if name in artifacts}}


def ksun_manager(base, api=api):
    """Official KernelSU Next CI run that built the manager at the kernel's base commit."""
    repo, workflow, _ = KSUN_CI
    runs = api(f"repos/{repo}/actions/workflows/{workflow}/runs?head_sha={base}&status=success&per_page=5")
    for ci in runs.get("workflow_runs", []):
        found = ci_manager(KSUN_CI, ci, api)
        if found:
            return found
    raise Wait(f"Tunggu build CI resmi manager KernelSU Next untuk commit `{base[:12]}` "
               "(belum ada atau artifact-nya sudah kedaluwarsa).",
               f"Wait for the official KernelSU Next CI manager build of commit `{base[:12]}` "
               "(none yet, or its artifact expired).")


def bakasu_main(api=api):
    """(commit, manager) of the newest BakaSU main commit the official CI built a manager for.
    Commits that only change other files get no CI run, so the newest main commit may not be it."""
    repo, workflow, _ = BAKASU_CI
    runs = api(f"repos/{repo}/actions/workflows/{workflow}/runs?branch=main&event=push&status=success&per_page=1")
    for ci in runs.get("workflow_runs", []):
        found = ci_manager(BAKASU_CI, ci, api)
        if found:
            return ci["head_sha"], found
    raise Wait("Tunggu build CI resmi manager BakaSU di main (belum ada atau artifact-nya sudah kedaluwarsa).",
               "Wait for the official BakaSU CI manager build on main (none yet, or its artifact expired).")


def needed_hooks(susfs_patch_text):
    added = "\n".join(line for line in susfs_patch_text.splitlines() if line.startswith("+"))
    return [name for name in HOOKS if re.search(rf"\b{name}\b", added)]


def hook_state(grep_output):
    """global / static / missing from `git grep` lines of a hook name (definitions start at column 0)."""
    defs = [line for line in grep_output.splitlines()
            if re.match(r"[A-Za-z_]", line) and not line.rstrip().endswith(";")]
    if not defs:
        return "missing"
    return "static" if all(line.startswith("static") for line in defs) else "global"


def bakasu_ready(repo, bakasu_ref, susfs_ref):
    """None when BakaSU at bakasu_ref can take SUSFS at susfs_ref, else what is missing."""
    def grep(*args, path="kernel"):
        return subprocess.run(["git", "-C", repo, "grep", *args, bakasu_ref, "--", path],
                              capture_output=True, text=True).stdout
    # The suspension (BakaSU 48fa4bb7): an unconditional $(error) in its SUSFS makefile.
    blocked = (grep("-E", r"^\$\(error", path=":(glob)kernel/**/*susfs*").strip()
               or grep("-F", "Please wait susfs update").strip())

    def find_hook(name):
        found = hook_state(grep("-h", "-E", rf"(^|[^A-Za-z0-9_]){name}[[:space:]]*\("))
        if found != "missing":
            return found
        # A hook may be the macro name of another function, e.g. BakaSU main (24 Oct 2026):
        # "#define ksu_handle_selinux_setprocattr my_setprocattr" once SUSFS brings its SELinux hide.
        defines = grep("-h", "-E", rf"^[[:space:]]*#[[:space:]]*define[[:space:]]+[A-Za-z_][A-Za-z0-9_]*[[:space:]]+{name}[[:space:]]*$")
        for alias in re.findall(rf"define\s+([A-Za-z_]\w*)\s+{name}\s*$", defines, re.M):
            found = hook_state(grep("-h", "-E", rf"(^|[^A-Za-z0-9_]){alias}[[:space:]]*\("))
            if found != "missing":
                return found
        return "missing"

    needed = needed_hooks(run("git", "-C", repo, "show", f"{susfs_ref}:{SUSFS_PATCH}"))
    states = {name: find_hook(name) for name in needed}
    problems = (["SUSFS diblokir di BakaSU / SUSFS blocked in BakaSU"] if blocked else []) + [
        f"`{name}` {state}" for name, state in states.items() if state != "global"]
    return ", ".join(problems) or None


def unicode_fix(ls_remote=ls_remote):
    """The newest WildKernel unicode bypass fix (Unicode fix box)."""
    return {"repo": UNICODE_FIX, "commit": ls_remote(UNICODE_FIX, "refs/heads/main")["refs/heads/main"],
            "path": UNICODE_FIX_PATCH}


# ---- the whole snapshot ---------------------------------------------------------------------

def resolve(root, sublevel, work, unicode=False):
    snap = {"root": root}
    snap["ack"] = [{"tag": tag, "commit": sha, "sublevel": sub}
                   for tag, sha, sub in pick_ack(ack_releases(ls_remote(ACK, "refs/tags/android14-6.1-*")), sublevel)]
    susfs = ls_remote(SUSFS, f"refs/heads/{SUSFS_BRANCH}")[f"refs/heads/{SUSFS_BRANCH}"]
    snap["susfs"] = {"repo": SUSFS, "branch": SUSFS_BRANCH, "commit": susfs}
    repo = str(work)
    run("git", "init", "-q", repo)
    run("git", "-C", repo, "config", "gc.auto", "0")
    run("git", "-C", repo, "fetch", "-q", "--depth=1", SUSFS, f"{susfs}:refs/check/susfs")
    if root == "KSUN":
        refs = ls_remote(KSUN_FORK, f"refs/heads/{KSUN_FORK_BRANCH}", "refs/heads/dev")
        head, dev = refs[f"refs/heads/{KSUN_FORK_BRANCH}"], refs["refs/heads/dev"]
        fetch_history(repo, KSUN_FORK, f"{head}:refs/check/ksun", f"{dev}:refs/check/ksun-dev")
        base, version = ksun_version(repo, "refs/check/ksun", "refs/check/ksun-dev")
        snap["root_source"] = {"repo": KSUN_FORK, "branch": KSUN_FORK_BRANCH, "commit": head,
                               "base": base, "ksu_version": version}
        snap["manager"] = {"kind": "ksun-ci", **ksun_manager(base)}
    else:
        tag, sha = newest_tag(ls_remote(BAKASU, "refs/tags/v*"))
        run("git", "-C", repo, "fetch", "-q", "--depth=1", BAKASU, f"{sha}:refs/check/bakasu")
        problem = bakasu_ready(repo, "refs/check/bakasu", "refs/check/susfs")
        if problem:
            # Before the next release, BakaSU main may already take the newest SUSFS (owner 24 Okt 2026,
            # Baka-SU/BakaSU#214). Kernel and manager then come from the same main commit.
            try:
                main, manager = bakasu_main()
                run("git", "-C", repo, "fetch", "-q", "--depth=1", BAKASU, f"{main}:refs/check/bakasu-main")
                main_problem = bakasu_ready(repo, "refs/check/bakasu-main", "refs/check/susfs")
            except Wait as wait:
                main, main_problem = None, wait.en_text
            if main_problem:
                where = f"main `{main[:12]}`" if main else "main"
                raise Wait(f"Tunggu pengembang BakaSU: rilis terbaru {tag} belum siap untuk SUSFS terbaru "
                           f"`{susfs[:12]}` ({problem}); {where} juga belum ({main_problem}). "
                           "Atau tunggu simonpunk menyesuaikan SUSFS.",
                           f"Wait for the BakaSU developer: the newest release {tag} is not ready for the newest "
                           f"SUSFS `{susfs[:12]}` ({problem}); {where} is not either ({main_problem}). "
                           "Or wait for simonpunk to adapt SUSFS.")
            snap["root_source"] = {"repo": BAKASU, "branch": "main", "commit": main}
            snap["manager"] = {"kind": "ci", **manager}
        else:
            release = api(f"repos/Baka-SU/BakaSU/releases/tags/{tag}")
            apks = [a for a in release["assets"] if a["name"].endswith(".apk")]
            if not apks:
                raise Wait(f"Tunggu pengembang BakaSU menerbitkan APK manager untuk {tag}.",
                           f"Wait for the BakaSU developer to publish the manager APK of {tag}.")
            apk = next((a for a in apks if "universal" in a["name"] or "arm64" in a["name"]), apks[0])
            snap["root_source"] = {"repo": BAKASU, "tag": tag, "commit": sha}
            snap["manager"] = {"kind": "release", "name": apk["name"], "url": apk["browser_download_url"],
                               "digest": apk.get("digest", "")}
    tag, sha = newest_tag(ls_remote(NOMOUNT, "refs/tags/v*"), STABLE)
    release = api(f"repos/maxsteeel/nomount/releases/tags/{tag}")
    module = next((a for a in release["assets"] if a["name"].endswith(".zip")), None)
    if module is None:
        raise Wait(f"Tunggu maxsteeel menerbitkan ZIP modul NoMount {tag}.",
                   f"Wait for maxsteeel to publish the NoMount {tag} module ZIP.")
    snap["nomount"] = {"repo": NOMOUNT, "tag": tag, "commit": sha, "module": module["name"],
                       "url": module["browser_download_url"], "digest": module.get("digest", "")}
    snap["bbg"] = {"repo": BBG, "commit": ls_remote(BBG, "refs/heads/main")["refs/heads/main"]}
    # rothko (Dimensity 9300+) runs no 32-bit code: the flasher tools come from osm0sis's own
    # arm64-tools branch, the scripts from master.
    ak3 = ls_remote(ANYKERNEL, "HEAD", "refs/heads/arm64-tools")
    snap["anykernel"] = {"repo": ANYKERNEL, "commit": ak3["HEAD"], "arm64_tools": ak3["refs/heads/arm64-tools"]}
    neutron = api(f"repos/{NEUTRON}/releases/latest")
    snap["neutron"] = {"tag": neutron["tag_name"],
                       "url": f"https://github.com/{NEUTRON}/releases/download/{neutron['tag_name']}/"
                              f"neutron-clang-{neutron['tag_name']}.tar.zst"}
    if unicode:
        snap["unicode"] = unicode_fix()
    return snap


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", choices=["KSUN", "BSU"], required=True)
    parser.add_argument("--sublevel", default="lts")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--unicode", action="store_true", help="the Unicode fix box is ticked")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="resolve-") as work:
        try:
            snap = resolve(args.root, args.sublevel, work, args.unicode)
        except Wait as wait:
            args.out.write_text(json.dumps({"root": args.root, "wait": {"id": wait.id_text, "en": wait.en_text}},
                                           indent=1))
            print(f"WAIT: {wait.en_text}")
            return 2
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
            print(f"::error::{args.root}: {exc}")
            return 1
    args.out.write_text(json.dumps(snap, indent=1))
    print(json.dumps(snap, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

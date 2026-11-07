#!/usr/bin/env python3
"""Newest version of every component of a rothko build, and whom to wait for when one does not fit.

No lock, pin or frozen tree (owner 2026-10-23): every run takes the newest official ACK
android14-6.1 release, the newest KernelSU Next (pershoot dev-susfs) or BakaSU release (BakaSU main
while its newest release does not take the newest SUSFS yet) or official KernelSU (tiann, main: the
newest commit its CI built a manager for) or SukiSU Ultra (builtin branch with SUSFS, the newest release
without; manager from the newest release), the newest SUSFS, NoMount release,
Baseband Guard, AnyKernel3 and Neutron clang. The commits found here are
the run's snapshot, passed to every build job so they all build the same thing.

When the newest version cannot work on rothko yet, the variant is not built and the summary says
whom to wait for, in Indonesian and English. The KMI gate of the build is not part of this: it
always runs and fails closed.

--unicode (the Unicode fix box, ticked by default since 1 Nov 2026) also takes the newest commit of WildKernel's
kernel_patches for its unicode bypass fix; without it nothing of WildKernel is read.

--no-susfs (the SUSFS box unticked) builds the plain root manager: no SUSFS, no sidex15 module, BakaSU
from its newest release.

CoganSU (owner 2026-11-04, cogan17/CoganSU, "dibuat khusus untuk cogan kernel"): KernelSU with Cogan's own
manager identity; kernel and manager from the same newest CoganSU release.

Usage: resolve.py --root KSUN|BSU|KSU|SUKI|CSU [--sublevel lts|N|N,M|semua|""] [--unicode] [--no-susfs] --out FILE.json
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
# Official KernelSU (owner 2026-11-02, "integrasi dengan ksu (induk segala induk)"): SUSFS ships its own
# patch for it, written against KernelSU main, so kernel and manager come from the newest main commit
# the official CI built a manager for (signed with the official key, like a release).
KSU = "https://github.com/tiann/KernelSU"
KSU_CI = ("tiann/KernelSU", "build-manager.yml", {"manager": "manager"})
SUSFS_KSU_PATCH = "kernel_patches/KernelSU/10_enable_susfs_for_ksu.patch"
# SukiSU Ultra (owner 2026-11-02): SUSFS lives only in its kernel-only `builtin` branch (built in, so no
# patch for the root driver; simonpunk's kernel patch is still applied). Without SUSFS the kernel is the
# newest release's own commit. The manager is always the newest release's APK, as the owner chose: with
# SUSFS, kernel and manager therefore do not come from the same commit (the builtin branch has no manager).
SUKISU = "https://github.com/SukiSU-Ultra/SukiSU-Ultra"
SUKISU_BUILTIN = "builtin"
# CoganSU (owner 2026-11-04): KernelSU with Cogan's own manager (package com.cogan.su, its own release key,
# kernel/cogansu.mk). Kernel and manager come from the same newest CoganSU release (vYY.MM.DD-rN), which its
# Build CoganSU form only publishes once kernel/cogansu.mk carries the release key's certificate. SUSFS
# through simonpunk's patch for KernelSU, exactly as for official KernelSU.
COGANSU = "https://github.com/cogan17/CoganSU"
COGANSU_TAG = re.compile(r"v(\d+)\.(\d+)\.(\d+)-r(\d+)")
SUSFS = "https://gitlab.com/simonpunk/susfs4ksu"
SUSFS_BRANCH = "gki-android14-6.1"
SUSFS_PATCH = "kernel_patches/50_add_susfs_in_gki-android14-6.1.patch"
# sidex15's SUSFS module (WebUI), the 6th file of a run (owner 2026-10-26: SUSFS has two developers). It has
# no releases: its "Build and Release" CI zips the module of branch v1.5.2+ on every push.
SUSFS_SIDEX = ("sidex15/susfs4ksu-module", "build.yml", "v1.5.2+")
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


class BuildFirst(Wait):
    """Not a wait: one build of ours to run first (owner 2026-11-07: "tunggu" only when a main developer
    waits). The Builder still stops; Cek pembaruan shows it as something new, not as waiting."""


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
    sublevel; semua or empty = the newest release of every sublevel since the phone's own (owner
    2026-10-31: "Jika dikosongkan maka semua sublevel muncul"). The form cannot send an empty value: GitHub
    replaces it with the default lts (run 41377075131), so the form says semua (owner 2026-11-02)."""
    wanted = wanted.strip().lower() or "semua"
    wanted = "semua" if wanted == "all" else wanted
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
    The manager artifact is enough: the run itself may still be posting to Telegram, or fail
    there (owner 24 Okt 2026). Commits that only change other files get no CI run."""
    repo, workflow, _ = BAKASU_CI
    runs = api(f"repos/{repo}/actions/workflows/{workflow}/runs?branch=main&event=push&per_page=5")
    for ci in runs.get("workflow_runs", []):
        found = ci_manager(BAKASU_CI, ci, api)
        if found:
            return ci["head_sha"], found
    raise Wait("Tunggu build CI resmi manager BakaSU di main (belum ada atau artifact-nya sudah kedaluwarsa).",
               "Wait for the official BakaSU CI manager build on main (none yet, or its artifact expired).")


def susfs_sidex(api=api):
    """The newest CI build of sidex15's SUSFS module that still has its artifact, or what to wait for."""
    repo, workflow, branch = SUSFS_SIDEX
    runs = api(f"repos/{repo}/actions/workflows/{workflow}/runs?branch={branch.replace('+', '%2B')}&status=success&per_page=5")
    for ci in runs.get("workflow_runs", []):
        artifacts = api(f"repos/{repo}/actions/runs/{ci['id']}/artifacts?per_page=100")["artifacts"]
        module = next((a for a in artifacts if a["name"].startswith("release-") and not a["expired"]), None)
        if module:
            return {"repo": repo, "run": ci["id"], "url": ci["html_url"], "commit": ci["head_sha"],
                    "date": ci.get("created_at", ""), "artifact": module["id"], "name": module["name"]}
    return {"wait": {"id": f"Tunggu sidex15 membangun modul SUSFS lagi (build CI {branch} tidak ada atau artifact-nya kedaluwarsa).",
                     "en": f"Wait for sidex15 to build the SUSFS module again (no {branch} CI build, or its artifact expired)."}}


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


def is_bakasu(repo, ref):
    """True when the tree at ref is BakaSU, not yet ReSukiSU: the project was renamed in BakaSU main
    97c102ba (5 Oct 2026, "treewide: rename project"), which also changed the manager signature. Release
    v4.2.0-rc3 (23 Sep 2026) predates it, so it is ReSukiSU (owner 2 Nov 2026, run 41361024017)."""
    return subprocess.run(["git", "-C", repo, "grep", "-q", "-i", "-F", "bakasu", ref, "--", "kernel/Kconfig"],
                          capture_output=True).returncode == 0


def unicode_fix(ls_remote=ls_remote):
    """The newest WildKernel unicode bypass fix (Unicode fix box)."""
    return {"repo": UNICODE_FIX, "commit": ls_remote(UNICODE_FIX, "refs/heads/main")["refs/heads/main"],
            "path": UNICODE_FIX_PATCH}


# ---- the whole snapshot ---------------------------------------------------------------------

def ksu_main(api=api):
    """(commit, manager) of the newest official KernelSU main commit the CI built a manager for."""
    repo, workflow, _ = KSU_CI
    runs = api(f"repos/{repo}/actions/workflows/{workflow}/runs?branch=main&event=push&status=success&per_page=5")
    for ci in runs.get("workflow_runs", []):
        found = ci_manager(KSU_CI, ci, api)
        if found:
            return ci["head_sha"], found
    raise Wait("Tunggu build CI resmi manager KernelSU di main (belum ada atau artifact-nya sudah kedaluwarsa).",
               "Wait for the official KernelSU CI manager build on main (none yet, or its artifact expired).")


def release_manager(url, who, tag, api=api):
    """The manager APK of release tag of the repository at url: the universal (or arm64) one, never spoofed."""
    release = api(f"repos/{url.removeprefix('https://github.com/')}/releases/tags/{tag}")
    apks = [a for a in release.get("assets", []) if a["name"].endswith(".apk") and "spoofed" not in a["name"].lower()]
    if not apks:
        raise Wait(f"Tunggu pengembang {who} menerbitkan APK manager untuk {tag}.",
                   f"Wait for the {who} developer to publish the manager APK of {tag}.")
    arch = re.compile(r"arm64-v8a|armeabi-v7a|x86_64|riscv64")
    apk = (next((a for a in apks if not arch.search(a["name"])), None)
           or next((a for a in apks if "arm64-v8a" in a["name"]), None) or apks[0])
    return {"kind": "release", "tag": tag, "name": apk["name"], "url": apk["browser_download_url"],
            "digest": apk.get("digest", "")}


def sukisu_manager(tag, api=api):
    """The manager APK of SukiSU release tag."""
    return release_manager(SUKISU, "SukiSU", tag, api)


def cogansu_release(refs):
    """(tag, commit) of the newest CoganSU release vYY.MM.DD-rN, or None."""
    tags = []
    for ref, sha in refs.items():
        match = COGANSU_TAG.fullmatch(ref.removeprefix("refs/tags/"))
        if match:
            tags.append((tuple(int(n) for n in match.groups()), ref.removeprefix("refs/tags/"), sha))
    return max(tags)[1:] if tags else None


def cogansu_identity(repo, ref):
    """True when kernel/cogansu.mk at ref carries the manager certificate (size and hash)."""
    text = subprocess.run(["git", "-C", repo, "show", f"{ref}:kernel/cogansu.mk"], capture_output=True, text=True).stdout
    values = dict(re.findall(r"^(COGANSU_EXPECTED_(?:SIZE|HASH))[ \t]*:=[ \t]*(\S*)[ \t]*$", text, re.M))
    return bool(values.get("COGANSU_EXPECTED_SIZE")) and bool(values.get("COGANSU_EXPECTED_HASH"))


SUSFS_HEADER = "kernel_patches/include/linux/susfs.h"


def guarded_functions(header):
    """{susfs function: CONFIG symbol} of the functions susfs.h declares only under an #ifdef CONFIG_..."""
    found, guard = {}, None
    for line in header.splitlines():
        match = re.match(r"\s*#\s*ifdef\s+CONFIG_(\w+)", line)
        if match:
            guard = match[1]
        elif re.match(r"\s*#\s*endif", line):
            guard = None
        elif guard:
            for name in re.findall(r"\b(susfs_\w+)\s*\(", line):
                found[name] = guard
    return found


def sukisu_ready(repo, sukisu_ref, susfs_ref):
    """None when SukiSU's builtin SUSFS at sukisu_ref compiles with SUSFS at susfs_ref, else what is missing:
    a SUSFS function SukiSU calls whose CONFIG symbol SUSFS added but SukiSU's Kconfig does not define yet
    (SUSFS f06acf7, 2 Nov 2026: priority_uid_filter became CONFIG_KSU_SUSFS_PRIORITY_UID_FILTER)."""
    def grep(*args):
        return subprocess.run(["git", "-C", repo, "grep", *args, sukisu_ref, "--", "kernel"],
                              capture_output=True, text=True).stdout
    defined = set(re.findall(r"^config\s+(\w+)\s*$", grep("-h", "-E", r"^config\s"), re.M))
    missing = set()
    for name, symbol in guarded_functions(run("git", "-C", repo, "show", f"{susfs_ref}:{SUSFS_HEADER}")).items():
        if symbol in defined:
            continue
        for path in grep("-l", "-w", name).splitlines():
            path = path.split(":", 1)[-1]
            text = run("git", "-C", repo, "show", f"{sukisu_ref}:{path}")
            if f"CONFIG_{symbol}" not in text:   # called outside any guard of that symbol
                missing.add(f"CONFIG_{symbol}")
    return ", ".join(sorted(missing)) or None


def has_builtin_susfs(repo, ref):
    """True when SukiSU at ref carries SUSFS for the root driver (config KSU_SUSFS in its Kconfig)."""
    return subprocess.run(["git", "-C", repo, "grep", "-q", "-E", r"^config KSU_SUSFS$", ref, "--", "kernel/Kconfig"],
                          capture_output=True).returncode == 0


def patch_fits(repo, ref, patch_text):
    """True when patch_text applies as it is to the tree of ref (checked on a scratch index, no checkout)."""
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmp, "index"))}
        subprocess.run(["git", "-C", repo, "read-tree", ref], env=env, check=True, capture_output=True)
        return subprocess.run(["git", "-C", repo, "apply", "--cached", "--check", "-"], input=patch_text,
                              env=env, text=True, capture_output=True).returncode == 0


def cogansu_susfs_wait(repo, tag, sha, susfs, patch):
    """Why the newest SUSFS patch for KernelSU does not fit CoganSU release tag. Build CoganSU merges the newest
    KernelSU main by itself (owner 2026-11-07: "tidak perlu ada kata menunggu … Kecuali dari Dev utama ada
    kata menunggu"), so a CoganSU that only lags KernelSU is not a wait but one Build CoganSU to run; only
    SUSFS not fitting KernelSU main either is a wait (for simonpunk)."""
    main = ls_remote(COGANSU, "refs/heads/main").get("refs/heads/main")
    if main and main != sha:
        run("git", "-C", repo, "fetch", "-q", "--depth=1", COGANSU, f"{main}:refs/check/cogansu-main")
        if patch_fits(repo, "refs/check/cogansu-main", patch):
            return BuildFirst(f"Jalankan Build CoganSU dengan Release Type Release: CoganSU main `{main[:12]}` sudah cocok "
                        f"dengan SUSFS `{susfs[:12]}`, rilis {tag} belum.",
                        f"Run Build CoganSU with Release Type Release: CoganSU main `{main[:12]}` already fits "
                        f"SUSFS `{susfs[:12]}`, release {tag} does not.")
    ksu = ls_remote(KSU, "refs/heads/main").get("refs/heads/main")
    if ksu:
        run("git", "-C", repo, "fetch", "-q", "--depth=1", KSU, f"{ksu}:refs/check/ksu")
        if patch_fits(repo, "refs/check/ksu", patch):
            return BuildFirst(f"Jalankan Build CoganSU dengan Release Type Release: ia menggabung KernelSU main `{ksu[:12]}` "
                        f"otomatis, yang sudah cocok dengan SUSFS `{susfs[:12]}` (rilis {tag} belum).",
                        f"Run Build CoganSU with Release Type Release: it merges KernelSU main `{ksu[:12]}` by itself, "
                        f"which already fits SUSFS `{susfs[:12]}` (release {tag} does not).")
    return Wait(f"Tunggu simonpunk menyesuaikan SUSFS `{susfs[:12]}` dengan KernelSU "
                f"(patch SUSFS untuk KernelSU belum cocok dengan KernelSU main maupun CoganSU {tag}).",
                f"Wait for simonpunk to adapt SUSFS `{susfs[:12]}` to KernelSU "
                f"(the SUSFS patch for KernelSU fits neither KernelSU main nor CoganSU {tag}).")


def resolve(root, sublevel, work, unicode=False, susfs_box=True):
    """susfs_box False (the SUSFS box unticked, owner 2026-11-02): the plain root manager without SUSFS;
    no SUSFS, no sidex15 module, and BakaSU from its newest release with no SUSFS readiness check."""
    snap = {"root": root, "susfs_box": susfs_box}
    snap["ack"] = [{"tag": tag, "commit": sha, "sublevel": sub}
                   for tag, sha, sub in pick_ack(ack_releases(ls_remote(ACK, "refs/tags/android14-6.1-*")), sublevel)]
    repo = str(work)
    run("git", "init", "-q", repo)
    run("git", "-C", repo, "config", "gc.auto", "0")
    susfs = None
    if susfs_box:
        susfs = ls_remote(SUSFS, f"refs/heads/{SUSFS_BRANCH}")[f"refs/heads/{SUSFS_BRANCH}"]
        snap["susfs"] = {"repo": SUSFS, "branch": SUSFS_BRANCH, "commit": susfs}
        snap["susfs_sidex"] = susfs_sidex()
        run("git", "-C", repo, "fetch", "-q", "--depth=1", SUSFS, f"{susfs}:refs/check/susfs")
    if root == "KSUN":
        refs = ls_remote(KSUN_FORK, f"refs/heads/{KSUN_FORK_BRANCH}", "refs/heads/dev")
        head, dev = refs[f"refs/heads/{KSUN_FORK_BRANCH}"], refs["refs/heads/dev"]
        fetch_history(repo, KSUN_FORK, f"{head}:refs/check/ksun", f"{dev}:refs/check/ksun-dev")
        base, version = ksun_version(repo, "refs/check/ksun", "refs/check/ksun-dev")
        snap["root_source"] = {"repo": KSUN_FORK, "branch": KSUN_FORK_BRANCH, "commit": head,
                               "base": base, "ksu_version": version}
        snap["manager"] = {"kind": "ksun-ci", **ksun_manager(base)}
    elif root == "KSU":
        main, manager = ksu_main()
        run("git", "-C", repo, "fetch", "-q", "--depth=1", KSU, f"{main}:refs/check/ksu")
        if susfs_box and not patch_fits(repo, "refs/check/ksu", run("git", "-C", repo, "show", f"refs/check/susfs:{SUSFS_KSU_PATCH}")):
            raise Wait(f"Tunggu simonpunk menyesuaikan SUSFS `{susfs[:12]}` dengan KernelSU main terbaru `{main[:12]}` "
                       "(patch SUSFS untuk KernelSU belum cocok).",
                       f"Wait for simonpunk to adapt SUSFS `{susfs[:12]}` to the newest KernelSU main `{main[:12]}` "
                       "(the SUSFS patch for KernelSU does not fit yet).")
        snap["root_source"] = {"repo": KSU, "branch": "main", "commit": main}
        snap["manager"] = {"kind": "ci", **manager}
    elif root == "CSU":
        found = cogansu_release(ls_remote(COGANSU, "refs/tags/v*"))
        if not found:
            raise Wait("Tunggu rilis CoganSU pertama: jalankan Build CoganSU dengan Release Type Pre-Release/Release "
                       "setelah kernel/cogansu.mk diisi (lihat docs/kunci.md di CoganSU).",
                       "Wait for the first CoganSU release: run Build CoganSU with Release Type Pre-Release/Release "
                       "once kernel/cogansu.mk is filled in (see docs/kunci.en.md in CoganSU).")
        tag, sha = found
        run("git", "-C", repo, "fetch", "-q", "--depth=1", COGANSU, f"{sha}:refs/check/cogansu")
        if not cogansu_identity(repo, "refs/check/cogansu"):
            raise Wait(f"Tunggu CoganSU: kernel/cogansu.mk di rilis {tag} belum berisi sertifikat manager.",
                       f"Wait for CoganSU: kernel/cogansu.mk of release {tag} carries no manager certificate yet.")
        if susfs_box:
            patch = run("git", "-C", repo, "show", f"refs/check/susfs:{SUSFS_KSU_PATCH}")
            if not patch_fits(repo, "refs/check/cogansu", patch):
                raise cogansu_susfs_wait(repo, tag, sha, susfs, patch)
        snap["root_source"] = {"repo": COGANSU, "tag": tag, "commit": sha}
        snap["manager"] = release_manager(COGANSU, "CoganSU", tag, api)
    elif root == "SUKI":
        tag, sha = newest_tag(ls_remote(SUKISU, "refs/tags/v*"))
        snap["manager"] = sukisu_manager(tag, api)
        if susfs_box:
            builtin = ls_remote(SUKISU, f"refs/heads/{SUKISU_BUILTIN}")[f"refs/heads/{SUKISU_BUILTIN}"]
            run("git", "-C", repo, "fetch", "-q", "--depth=1", SUKISU, f"{builtin}:refs/check/sukisu")
            if not has_builtin_susfs(repo, "refs/check/sukisu"):
                raise Wait(f"Tunggu pengembang SukiSU: cabang {SUKISU_BUILTIN} `{builtin[:12]}` tidak lagi membawa SUSFS.",
                           f"Wait for the SukiSU developer: branch {SUKISU_BUILTIN} `{builtin[:12]}` no longer carries SUSFS.")
            problem = sukisu_ready(repo, "refs/check/sukisu", "refs/check/susfs")
            if problem:
                raise Wait(f"Tunggu pengembang SukiSU menyesuaikan cabang {SUKISU_BUILTIN} `{builtin[:12]}` dengan SUSFS "
                           f"terbaru `{susfs[:12]}` (belum mengenal {problem}). Atau lepas centang SUSFS.",
                           f"Wait for the SukiSU developer to adapt branch {SUKISU_BUILTIN} `{builtin[:12]}` to the newest "
                           f"SUSFS `{susfs[:12]}` (it does not know {problem} yet). Or untick SUSFS.")
            snap["root_source"] = {"repo": SUKISU, "branch": SUKISU_BUILTIN, "commit": builtin, "manager_tag": tag}
        else:
            snap["root_source"] = {"repo": SUKISU, "tag": tag, "commit": sha}
    else:
        tag, sha = newest_tag(ls_remote(BAKASU, "refs/tags/v*"))
        run("git", "-C", repo, "fetch", "-q", "--depth=1", BAKASU, f"{sha}:refs/check/bakasu")
        if not is_bakasu(repo, "refs/check/bakasu"):
            problem = (f"rilis {tag} masih ReSukiSU, sebelum ganti nama ke BakaSU / "
                       f"release {tag} is still ReSukiSU, from before the rename to BakaSU")
        else:
            problem = bakasu_ready(repo, "refs/check/bakasu", "refs/check/susfs") if susfs_box else None
        if problem:
            # Before the next release, BakaSU main may already take the newest SUSFS (owner 24 Okt 2026,
            # Baka-SU/BakaSU#214). Kernel and manager then come from the same main commit.
            try:
                main, manager = bakasu_main()
                run("git", "-C", repo, "fetch", "-q", "--depth=1", BAKASU, f"{main}:refs/check/bakasu-main")
                main_problem = bakasu_ready(repo, "refs/check/bakasu-main", "refs/check/susfs") if susfs_box else None
                main_id = main_en = f"main `{main[:12]}`: {main_problem}"
            except Wait as wait:
                main, main_problem, main_id, main_en = None, True, wait.id_text, wait.en_text
            if main_problem and not susfs_box:
                raise Wait(f"Tunggu pengembang BakaSU: rilis terbaru {tag} belum bisa dipakai ({problem}); {main_id}.",
                           f"Wait for the BakaSU developer: the newest release {tag} cannot be used ({problem}); {main_en}.")
            if main_problem:
                raise Wait(f"Tunggu pengembang BakaSU: rilis terbaru {tag} belum siap untuk SUSFS terbaru "
                           f"`{susfs[:12]}` ({problem}); {main_id}. Atau tunggu simonpunk menyesuaikan SUSFS.",
                           f"Wait for the BakaSU developer: the newest release {tag} is not ready for the newest "
                           f"SUSFS `{susfs[:12]}` ({problem}); {main_en}. Or wait for simonpunk to adapt SUSFS.")
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
    parser.add_argument("--root", choices=["KSUN", "BSU", "KSU", "SUKI", "CSU"], required=True)
    parser.add_argument("--sublevel", default="lts")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--unicode", action="store_true", help="the Unicode fix box is ticked")
    parser.add_argument("--no-susfs", action="store_true", help="the SUSFS box is unticked")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="resolve-") as work:
        try:
            snap = resolve(args.root, args.sublevel, work, args.unicode, not args.no_susfs)
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

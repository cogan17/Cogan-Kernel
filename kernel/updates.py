#!/usr/bin/env python3
"""Cek pembaruan: the newest version of every component of a Cogan Kernel build against the last build,
in Indonesian and English (owner 2026-10-26). It only checks: nothing is built, published or written.

For each component: the version the last Builder run used, the newest stable release and the newest
CI (branch) version with their dates, which one is newer, what is new and what was fixed since the
last build (commit titles, or the release notes), and whether it can be built now. BakaSU against the
newest SUSFS and the KernelSU Next CI manager are checked the way kernel/resolve.py checks them, so the
summary also says whom to wait for (e.g. "SUSFS blocked in BakaSU", Baka-SU/BakaSU#214).

The last build is the newest Cogan Kernel Builder run on main that built a kernel of that root
manager (its snapshot artifact, kept 90 days). Upstream text (commit titles, release notes) is shown
as its authors wrote it.

SUSFS has two developers (owner 2026-10-26): simonpunk (kernel patch and module, file 5) and sidex15
(module with WebUI, file 6, CI builds only); both are checked.

Usage: updates.py --repo OWNER/REPO [--out FILE]   (GH_TOKEN for the GitHub API)
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

if __package__:  # imported as kernel.updates (tests): the same resolve module as the caller
    from . import resolve as r
else:            # run as kernel/updates.py
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import resolve as r  # noqa: E402  (the Builder's own version finder)

WIB = timezone(timedelta(hours=7))
GITLAB = "https://gitlab.com/api/v4/projects/simonpunk%2Fsusfs4ksu"
KSUN_UPSTREAM = "KernelSU-Next/KernelSU-Next"
FIX = re.compile(r"\b(fix(e[sd])?|bug|crash|revert|regression|leak|panic|hotfix)\b|^fix[(:]", re.I)
MONTHS_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
LIMIT = 12  # commit titles per component

T = {
    "id": {
        "flag": "🇮🇩 Bahasa Indonesia", "title": "Cek pembaruan", "component": "Komponen", "last": "Build terakhir",
        "newest": "Terbaru", "status": "Status", "same": "✅ sama", "new": "🆕 ada yang baru", "wait": "⏳ tunggu",
        "unknown": "ℹ️ belum pernah dibangun", "error": "⚠️ tidak bisa dicek", "off": "➖ tidak dipakai",
        "stable": "Stabil", "ci": "CI", "newer_ci": "CI lebih baru dari rilis stabil", "newer_stable": "rilis stabil paling baru",
        "build": "🆕 **Ada pembaruan: {names}.** Silakan jalankan **Cogan Kernel Builder** (Release Type CI dulu untuk bukti build).",
        "nothing": "✅ **Semua komponen sama dengan build terakhir.** Belum perlu build.",
        "waits": "⏳ **Belum bisa dibangun:**",
        "lastrun": "Build terakhir: {roots}.", "norun": "Belum ada run Builder dengan kernel dalam 90 hari terakhir.",
        "changes": "Yang baru dan perbaikan sejak build terakhir", "fixes": "🔧 Perbaikan", "news": "✨ Baru",
        "more": "… dan {n} commit lain", "notes": "Catatan rilis {tag}", "none": "tidak ada commit baru",
        "only": "Hanya cek: tidak ada yang dibangun atau diterbitkan. Teks commit dan catatan rilis ditulis apa adanya oleh pengembangnya.",
        "ksun_ci": "Manager CI resmi untuk commit ini: {state}", "ready": "ada", "bakasu_rel": "Rilis {tag}: {state}",
        "bakasu_main": "main `{sha}`: {state}", "fits": "siap untuk SUSFS terbaru", "takes": "Builder akan memakai: {what}",
        "unicode_off": "Build terakhir tanpa Unicode fix.", "patch_same": "patch Unicode fix tidak berubah",
    },
    "en": {
        "flag": "🇬🇧 English", "title": "Check for updates", "component": "Component", "last": "Last build",
        "newest": "Newest", "status": "Status", "same": "✅ same", "new": "🆕 newer", "wait": "⏳ waiting",
        "unknown": "ℹ️ never built", "error": "⚠️ could not check", "off": "➖ not used",
        "stable": "Stable", "ci": "CI", "newer_ci": "CI is newer than the stable release", "newer_stable": "the stable release is the newest",
        "build": "🆕 **Updates: {names}.** Run **Cogan Kernel Builder** (Release Type CI first, as build proof).",
        "nothing": "✅ **Every component equals the last build.** No build needed yet.",
        "waits": "⏳ **Cannot be built yet:**",
        "lastrun": "Last build: {roots}.", "norun": "No Builder run with a kernel in the last 90 days.",
        "changes": "New and fixed since the last build", "fixes": "🔧 Fixes", "news": "✨ New",
        "more": "… and {n} more commits", "notes": "Release notes {tag}", "none": "no new commits",
        "only": "Check only: nothing is built or published. Commit titles and release notes are shown as their developers wrote them.",
        "ksun_ci": "Official CI manager for this commit: {state}", "ready": "available", "bakasu_rel": "Release {tag}: {state}",
        "bakasu_main": "main `{sha}`: {state}", "fits": "ready for the newest SUSFS", "takes": "The Builder would take: {what}",
        "unicode_off": "The last build was without the Unicode fix.", "patch_same": "the Unicode fix patch is unchanged",
    },
}


# ---- small helpers ------------------------------------------------------------------------------

def when(stamp, lang):
    """'26 Okt 2026 12.34 WIB' (id) / '26 Oct 2026 12:34 WIB' (en) from an ISO 8601 time, '' if unknown."""
    if not stamp:
        return ""
    try:
        moment = datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(WIB)
    except ValueError:
        return stamp
    if lang == "id":
        return f"{moment.day} {MONTHS_ID[moment.month - 1]} {moment.year} {moment:%H.%M} WIB"
    return f"{moment.day} {MONTHS_EN[moment.month - 1]} {moment.year} {moment:%H:%M} WIB"


def gitiles_time(text):
    """ISO time of a gitiles JSON time such as 'Thu Oct 09 05:25:51 2026 +0000' ('' if unknown)."""
    for fmt in ("%a %b %d %H:%M:%S %Y %z", "%a %b %d %H:%M:%S %Y"):
        try:
            moment = datetime.strptime(text, fmt)
            return (moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)).isoformat()
        except (TypeError, ValueError):
            continue
    return ""


def newer(a, b):
    """True when ISO time a is later than ISO time b (False when either is unknown)."""
    try:
        return datetime.fromisoformat(a.replace("Z", "+00:00")) > datetime.fromisoformat(b.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return False


def short(sha):
    return (sha or "")[:12]


def excerpt(body, lines=12):
    """The first lines of release notes, without images, HTML comments and empty lines."""
    body = re.sub(r"<!--.*?-->", "", body or "", flags=re.S)
    kept = [line.rstrip() for line in body.splitlines()
            if line.strip() and not re.match(r"\s*!\[|\s*<img", line)]
    text = "\n".join(kept[:lines])
    return text + ("\n…" if len(kept) > lines else "")


def split_changes(commits):
    """(fixes, new) commit dicts, by their titles."""
    fixes = [c for c in commits if FIX.search(c["title"])]
    return fixes, [c for c in commits if c not in fixes]


# ---- network (one object, so the tests can replace it) -----------------------------------------

class Net:
    def api(self, path):
        return r.api(path)

    def gitlab(self, path):
        return json.loads(r.http(GITLAB + path))

    def http(self, url):
        return r.http(url)

    def ls_remote(self, url, *patterns):
        return r.ls_remote(url, *patterns)

    def download(self, repo, artifact, dest):
        """An artifact's ZIP through gh (it follows GitHub's redirect without sending the token on)."""
        with open(dest, "wb") as out:
            subprocess.run(["gh", "api", f"repos/{repo}/actions/artifacts/{artifact}/zip"], stdout=out, check=True)

    def ksun_manager(self, base):
        return r.ksun_manager(base)

    @staticmethod
    def git_dir(repo):
        """A scratch repository without background gc or maintenance (Cek pembaruan run 3: git still wrote
        into .git while the folder was being removed, "Directory not empty")."""
        r.run("git", "init", "-q", repo)
        r.run("git", "-C", repo, "config", "gc.auto", "0")
        r.run("git", "-C", repo, "config", "maintenance.auto", "false")

    def ksu_version(self, head, dev):
        with tempfile.TemporaryDirectory(prefix="updates-ksun-", ignore_cleanup_errors=True) as repo:
            self.git_dir(repo)
            r.fetch_history(repo, r.KSUN_FORK, f"{head}:refs/check/ksun", f"{dev}:refs/check/ksun-dev")
            return r.ksun_version(repo, "refs/check/ksun", "refs/check/ksun-dev")

    def bakasu_ready(self, release, main, susfs):
        """(problem of the release, problem of main) against SUSFS commit susfs; None = ready."""
        with tempfile.TemporaryDirectory(prefix="updates-bakasu-", ignore_cleanup_errors=True) as repo:
            self.git_dir(repo)
            r.run("git", "-C", repo, "fetch", "-q", "--depth=1", r.SUSFS, f"{susfs}:refs/check/susfs")
            found = []
            for name, sha in (("release", release), ("main", main)):
                if not sha:
                    found.append(None)
                    continue
                r.run("git", "-C", repo, "fetch", "-q", "--depth=1", r.BAKASU, f"{sha}:refs/check/{name}")
                found.append(r.bakasu_ready(repo, f"refs/check/{name}", "refs/check/susfs"))
            return tuple(found)


# ---- the last build ----------------------------------------------------------------------------

def last_builds(net, repo, runs=30):
    """{root: {"run", "url", "date", "snap"}} of the newest Builder run on main that built a kernel of
    that root manager, from its snapshot artifact (kept 90 days)."""
    found = {}
    listed = net.api(f"repos/{repo}/actions/workflows/build-kernel.yml/runs?branch=main&status=completed&per_page={runs}")
    for run in listed.get("workflow_runs", []):
        artifacts = [a for a in net.api(f"repos/{repo}/actions/runs/{run['id']}/artifacts?per_page=100")["artifacts"]
                     if not a.get("expired")]
        kernels = [a["name"] for a in artifacts if a["name"].startswith("1-KERNEL_")]
        snapshot = next((a for a in artifacts if a["name"].startswith("snapshots-")), None)
        if not kernels or snapshot is None:
            continue
        with tempfile.TemporaryDirectory(prefix="updates-run-") as work:
            net.download(repo, snapshot["id"], Path(work) / "snap.zip")
            with zipfile.ZipFile(Path(work) / "snap.zip") as archive:
                snaps = [json.loads(archive.read(name)) for name in archive.namelist() if name.endswith(".json")]
        for snap in snaps:
            root = snap.get("root")
            tag = "KernelSU-Next" if root == "KSUN" else "BakaSU"
            if root in found or "wait" in snap or not any(tag in name for name in kernels):
                continue
            found[root] = {"run": run["run_number"], "url": run["html_url"], "date": run.get("created_at", ""), "snap": snap}
        if {"KSUN", "BSU"} <= found.keys():
            break
    return found


def base_of(builds, *path):
    """A value of the newest last build's snapshot (KSUN first), e.g. base_of(builds, "susfs", "commit")."""
    for root in ("KSUN", "BSU"):
        value = builds.get(root, {}).get("snap")
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        if value:
            return value
    return None


def github_changes(net, repo, base, head):
    """Commits of a GitHub repository from base to head, oldest first: [{sha, date, title}]."""
    if not base or base == head:
        return []
    data = net.api(f"repos/{repo}/compare/{base}...{head}")
    return [{"sha": c["sha"], "date": c["commit"]["committer"]["date"], "title": c["commit"]["message"].splitlines()[0]}
            for c in data.get("commits", [])]


def github_commit(net, repo, sha):
    data = net.api(f"repos/{repo}/commits/{sha}")
    return {"sha": data["sha"], "date": data["commit"]["committer"]["date"], "title": data["commit"]["message"].splitlines()[0]}


def github_release(net, repo, tag=None):
    data = net.api(f"repos/{repo}/releases/tags/{tag}" if tag else f"repos/{repo}/releases/latest")
    return {"tag": data["tag_name"], "date": data.get("published_at", ""), "url": data.get("html_url", ""),
            "notes": excerpt(data.get("body", "")), "prerelease": data.get("prerelease", False)}


def item(key, name, **values):
    base = {"key": key, "name": name, "base": None, "stable": None, "ci": None, "changes": [], "status": "same",
            "notes": None, "lines": [], "wait": None, "error": "", "log": False}   # log: commits were compared
    base.update(values)
    return base


# ---- the components ------------------------------------------------------------------------------

def ack_key(tag):
    match = r.ACK_TAG.fullmatch(tag or "")
    return tuple(int(n) for n in match.groups()) if match else (0, 0, 0)


def check_ack(net, builds):
    # The newest ACK release any last build used: a compile proof of old sublevels (e.g. 138 and 145)
    # must not hide that 176 was already built (Cek pembaruan run 2, 26 Okt 2026).
    built = [ack["tag"] for build in builds.values() for ack in build.get("snap", {}).get("ack", [])]
    base_tag = max(built, key=ack_key) if built else None
    releases = r.ack_releases(net.ls_remote(r.ACK, "refs/tags/android14-6.1-*"))
    tag, sha = releases[0]
    sublevel = r.ack_sublevel(tag, net.http)
    # gitiles JSON of the release commit (the tag is peeled by ls-remote), after its ")]}'" guard line.
    meta = json.loads(net.http(f"{r.ACK}/+/{sha}?format=JSON").decode().split("\n", 1)[1])
    stable = {"tag": tag, "label": f"`{tag}` (6.1.{sublevel})", "date": gitiles_time(meta.get("committer", {}).get("time", ""))}
    tags = [t for t, _ in releases]
    newer_tags = tags[:tags.index(base_tag)] if base_tag in tags else []
    shown = ", ".join(f"`{t}`" for t in newer_tags[:8])
    more = len(newer_tags) - 8
    lines = ([{"id": "Rilis ACK baru: " + shown + (f" dan {more} lainnya" if more > 0 else ""),
               "en": "New ACK releases: " + shown + (f" and {more} more" if more > 0 else "")}] if newer_tags else [])
    return item("ack", "ACK android14-6.1", base={"label": f"`{base_tag}`"} if base_tag else None, stable=stable,
                status="unknown" if not base_tag else "same" if base_tag == tag else "new", lines=lines)


def check_susfs(net, builds):
    base = base_of(builds, "susfs", "commit")
    head = net.ls_remote(r.SUSFS, f"refs/heads/{r.SUSFS_BRANCH}")[f"refs/heads/{r.SUSFS_BRANCH}"]
    commit = net.gitlab(f"/repository/commits/{head}")
    header = net.http(f"{GITLAB}/repository/files/{'kernel_patches%2Finclude%2Flinux%2Fsusfs.h'}/raw?ref={head}").decode()
    version = (re.search(r'#define SUSFS_VERSION "([^"]+)"', header) or [None, "?"])[1]
    changes = []
    if base and base != head:
        compared = net.gitlab(f"/repository/compare?from={base}&to={head}")
        changes = [{"sha": c["id"], "date": c["created_at"], "title": c["title"]} for c in compared.get("commits", [])]
    ci = {"label": f"{version} `{short(head)}`", "date": commit.get("created_at", ""), "sha": head,
          "url": f"{r.SUSFS}/-/commits/{r.SUSFS_BRANCH}"}
    return item("susfs", "SUSFS (simonpunk)", base={"label": f"`{short(base)}`"} if base else None, ci=ci,
                changes=changes, status="unknown" if not base else "same" if base == head else "new", log=True)


def check_sidex(net, builds):
    """sidex15's SUSFS module (WebUI), the 6th file: no releases, the Builder takes its newest CI build."""
    base = base_of(builds, "susfs_sidex", "commit")
    repo = r.SUSFS_SIDEX[0]
    newest = r.susfs_sidex(net.api)
    lines = [{"id": "Tanpa rilis: Builder mengambil build CI terbarunya (cabang v1.5.2+).",
              "en": "No releases: the Builder takes its newest CI build (branch v1.5.2+)."}]
    if "wait" in newest:
        return item("sidex", "SUSFS modul (sidex15)", base={"label": f"`{short(base)}`"} if base else None,
                    status="wait", wait=newest["wait"], lines=lines)
    head = newest["commit"]
    ci = {"label": f"{newest['name']} `{short(head)}`", "date": newest.get("date", ""), "sha": head, "url": newest["url"]}
    return item("sidex", "SUSFS modul (sidex15)", base={"label": f"`{short(base)}`"} if base else None, ci=ci,
                changes=github_changes(net, repo, base, head), lines=lines,
                status="unknown" if not base else "same" if base == head else "new", log=True)


def check_ksun(net, builds):
    snap = builds.get("KSUN", {}).get("snap", {})
    base = snap.get("root_source", {})
    refs = net.ls_remote(r.KSUN_FORK, f"refs/heads/{r.KSUN_FORK_BRANCH}", "refs/heads/dev")
    head, dev = refs[f"refs/heads/{r.KSUN_FORK_BRANCH}"], refs["refs/heads/dev"]
    fork = r.KSUN_FORK.removeprefix("https://github.com/")
    top = github_commit(net, fork, head)
    lines = []
    version = ""
    try:
        merge_base, number = net.ksu_version(head, dev)
        version = f" ({number})"
        try:
            net.ksun_manager(merge_base)
            state = {"id": T["id"]["ready"], "en": T["en"]["ready"]}
            wait = None
        except r.Wait as missing:
            state, wait = {"id": missing.id_text, "en": missing.en_text}, {"id": missing.id_text, "en": missing.en_text}
        lines.append({lang: T[lang]["ksun_ci"].format(state=state[lang]) for lang in ("id", "en")})
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        wait = None
        lines.append({"id": f"Versi KSU tidak terbaca: {exc}", "en": f"KSU version unreadable: {exc}"})
    stable = github_release(net, KSUN_UPSTREAM)
    ci = {"label": f"{r.KSUN_FORK_BRANCH} `{short(head)}`{version}", "date": top["date"], "sha": head,
          "url": f"{r.KSUN_FORK}/commits/{r.KSUN_FORK_BRANCH}"}
    status = "unknown" if not base else "same" if base.get("commit") == head else "new"
    if wait:
        status = "wait"
    return item("ksun", "KernelSU Next", base={"label": f"{r.KSUN_FORK_BRANCH} `{short(base.get('commit'))}`"} if base else None,
                stable={"label": stable["tag"], "date": stable["date"], "url": stable["url"]}, ci=ci,
                changes=github_changes(net, fork, base.get("commit"), head), status=status, wait=wait, lines=lines,
                notes={"tag": stable["tag"], "text": stable["notes"]})


def check_bakasu(net, builds, susfs_head):
    snap = builds.get("BSU", {}).get("snap", {})
    base = snap.get("root_source", {})
    repo = r.BAKASU.removeprefix("https://github.com/")
    tag, tag_sha = r.newest_tag(net.ls_remote(r.BAKASU, "refs/tags/v*"))   # the release the Builder would take
    try:
        release = net.api(f"repos/{repo}/releases/tags/{tag}")
    except OSError:
        release = None   # a tag without a published release
    try:
        main, _ = r.bakasu_main(net.api)
        main_info = github_commit(net, repo, main)
    except r.Wait:
        main, main_info = None, None
    rel_problem, main_problem = net.bakasu_ready(tag_sha, main, susfs_head)
    lines = []
    if tag:
        lines.append({lang: T[lang]["bakasu_rel"].format(tag=tag, state=rel_problem or T[lang]["fits"]) for lang in ("id", "en")})
    if main:
        lines.append({lang: T[lang]["bakasu_main"].format(sha=main[:8], state=main_problem or T[lang]["fits"]) for lang in ("id", "en")})
    wait = None
    if tag and not rel_problem:
        takes, sha = tag, tag_sha
    elif main and not main_problem:
        takes, sha = f"main `{main[:8]}` (CI)", main
    else:
        takes, sha = None, None
        wait = {"id": f"Tunggu pengembang BakaSU: rilis {tag} dan main belum siap untuk SUSFS terbaru "
                      f"`{short(susfs_head)}` ({rel_problem or '-'}; main: {main_problem or '-'}). Atau tunggu simonpunk menyesuaikan SUSFS.",
                "en": f"Wait for the BakaSU developer: release {tag} and main are not ready for the newest SUSFS "
                      f"`{short(susfs_head)}` ({rel_problem or '-'}; main: {main_problem or '-'}). Or wait for simonpunk to adapt SUSFS."}
    if takes:
        lines.append({lang: T[lang]["takes"].format(what=takes) for lang in ("id", "en")})
    status = "wait" if wait else "unknown" if not base else "same" if base.get("commit") == sha else "new"
    base_label = (base.get("tag") or "main") + f" `{short(base.get('commit'))}`" if base else None
    return item("bakasu", "BakaSU", base={"label": base_label} if base else None,
                stable={"label": tag, "date": release.get("published_at", ""), "url": release.get("html_url", "")} if release else None,
                ci={"label": f"main `{short(main)}`", "date": main_info["date"], "sha": main} if main_info else None,
                changes=github_changes(net, repo, base.get("commit"), main) if main else [], status=status, wait=wait,
                lines=lines, notes={"tag": tag, "text": excerpt(release.get("body", ""))} if release else None)


def check_nomount(net, builds):
    base = base_of(builds, "nomount", "tag")
    repo = r.NOMOUNT.removeprefix("https://github.com/")
    tag, _ = r.newest_tag(net.ls_remote(r.NOMOUNT, "refs/tags/v*"), r.STABLE)
    release = github_release(net, repo, tag)
    head = net.ls_remote(r.NOMOUNT, "HEAD")["HEAD"]
    top = github_commit(net, repo, head)
    after = github_changes(net, repo, tag, head)   # on the main branch after the newest release
    lines = ([{"id": f"{len(after)} commit di main sesudah {tag} (belum dirilis; Builder memakai rilis)",
               "en": f"{len(after)} commit(s) on main after {tag} (not released; the Builder takes the release)"}] if after else [])
    return item("nomount", "NoMount", base={"label": base} if base else None,
                stable={"label": tag, "date": release["date"], "url": release["url"]},
                ci={"label": f"main `{short(head)}`", "date": top["date"], "sha": head},
                changes=github_changes(net, repo, base, tag) if base and base != tag else [],
                status="unknown" if not base else "same" if base == tag else "new", lines=lines,
                notes={"tag": tag, "text": release["notes"]})


def check_branch(net, builds, key, name, url, ref="refs/heads/main", path=None):
    """A component the Builder takes from a branch head (Baseband Guard, AnyKernel3)."""
    base = base_of(builds, *(path or (key, "commit")))
    head = net.ls_remote(url, ref)[ref]
    repo = url.removeprefix("https://github.com/")
    top = github_commit(net, repo, head)
    return item(key, name, base={"label": f"`{short(base)}`"} if base else None,
                ci={"label": f"`{short(head)}`", "date": top["date"], "sha": head},
                changes=github_changes(net, repo, base, head),
                status="unknown" if not base else "same" if base == head else "new", log=True)


def check_anykernel(net, builds):
    """AnyKernel3: the scripts from master (HEAD) and the arm64 flasher tools from arm64-tools."""
    entry = check_branch(net, builds, "anykernel", "AnyKernel3", r.ANYKERNEL, "HEAD")
    base = base_of(builds, "anykernel", "arm64_tools")
    tools = net.ls_remote(r.ANYKERNEL, "refs/heads/arm64-tools")["refs/heads/arm64-tools"]
    if base and base != tools:
        entry["status"] = "new"
        entry["lines"].append({"id": f"Cabang arm64-tools berubah: `{short(base)}` → `{short(tools)}`",
                               "en": f"The arm64-tools branch changed: `{short(base)}` → `{short(tools)}`"})
    return entry


def check_neutron(net, builds):
    base = base_of(builds, "neutron", "tag")
    release = github_release(net, r.NEUTRON)
    return item("neutron", "Neutron clang", base={"label": base} if base else None,
                stable={"label": release["tag"], "date": release["date"], "url": release["url"]},
                status="unknown" if not base else "same" if base == release["tag"] else "new")


def check_unicode(net, builds):
    base = base_of(builds, "unicode", "commit")
    repo = r.UNICODE_FIX.removeprefix("https://github.com/")
    touched = net.api(f"repos/{repo}/commits?path={r.UNICODE_FIX_PATCH.replace('+', '%2B')}&per_page=5")
    newest = touched[0] if touched else None
    ci = ({"label": f"`{short(newest['sha'])}`", "date": newest["commit"]["committer"]["date"], "sha": newest["sha"]}
          if newest else None)
    if not base:
        return item("unicode", "Unicode fix (WildKernel)", ci=ci, status="off",
                    lines=[{"id": T["id"]["unicode_off"], "en": T["en"]["unicode_off"]}])
    # The Builder takes the branch head; only commits that touch the patch change the kernel.
    since = github_changes(net, repo, base, net.ls_remote(r.UNICODE_FIX, "refs/heads/main")["refs/heads/main"])
    changed = [c for c in since if newest and c["sha"] in {t["sha"] for t in touched}]
    return item("unicode", "Unicode fix (WildKernel)", base={"label": f"`{short(base)}`"}, ci=ci, changes=changed,
                status="new" if changed else "same",
                lines=[] if changed else [{"id": T["id"]["patch_same"], "en": T["en"]["patch_same"]}])


def gather(net, repo):
    try:
        builds = last_builds(net, repo)
    except Exception as exc:  # noqa: BLE001 - the newest versions are still worth showing
        builds = {"error": str(exc)}
    clean = {k: v for k, v in builds.items() if k in ("KSUN", "BSU")}
    found = []
    susfs_head = None
    checks = [("ack", lambda: check_ack(net, clean)), ("susfs", lambda: check_susfs(net, clean)),
              ("sidex", lambda: check_sidex(net, clean)), ("ksun", lambda: check_ksun(net, clean)), ("bakasu", lambda: check_bakasu(net, clean, susfs_head)),
              ("nomount", lambda: check_nomount(net, clean)),
              ("bbg", lambda: check_branch(net, clean, "bbg", "Baseband Guard", r.BBG)),
              ("anykernel", lambda: check_anykernel(net, clean)),
              ("neutron", lambda: check_neutron(net, clean)), ("unicode", lambda: check_unicode(net, clean))]
    names = {"ack": "ACK android14-6.1", "susfs": "SUSFS (simonpunk)", "sidex": "SUSFS modul (sidex15)",
             "ksun": "KernelSU Next", "bakasu": "BakaSU",
             "nomount": "NoMount", "bbg": "Baseband Guard", "anykernel": "AnyKernel3", "neutron": "Neutron clang",
             "unicode": "Unicode fix (WildKernel)"}
    for key, check in checks:
        try:
            found.append(check())
        except Exception as exc:  # noqa: BLE001 - one source down must not hide the others
            found.append(item(key, names[key], status="error", error=str(exc)[:300]))
        if key == "susfs" and found[-1].get("ci"):
            susfs_head = found[-1]["ci"]["sha"]
    return builds, found


# ---- the summary ---------------------------------------------------------------------------------

def version_cell(entry, lang):
    t = T[lang]
    parts = []
    for kind in ("stable", "ci"):
        value = entry.get(kind)
        if value and value.get("label"):
            date = when(value.get("date", ""), lang)
            text = f"{t[kind]}: {value['label']}"
            if date:   # "(6.1.180)" becomes "(6.1.180, 22 Okt 2026 12.25 WIB)"
                text = text[:-1] + f", {date})" if text.endswith(")") else text + f" ({date})"
            parts.append(text)
    stable, ci = entry.get("stable") or {}, entry.get("ci") or {}
    if stable.get("date") and ci.get("date"):
        parts.append(t["newer_ci"] if newer(ci["date"], stable["date"]) else t["newer_stable"])
    return "<br>".join(parts) or "-"


def status_cell(entry, lang):
    t = T[lang]
    text = t[entry["status"]]
    if entry["status"] == "error":
        text += f": {entry['error']}"
    return text


def change_lines(entry, lang):
    t = T[lang]
    commits = entry.get("changes") or []
    lines = [f"- {line[lang]}" for line in entry.get("lines", [])]
    if entry["status"] in ("new", "wait") and commits:
        fixes, news = split_changes(list(reversed(commits)))  # newest first
        for label, group in ((t["fixes"], fixes), (t["news"], news)):
            if group:
                lines.append(f"- {label}:")
                lines += [f"  - `{c['sha'][:8]}` {when(c['date'], lang)} · {c['title']}" for c in group[:LIMIT]]
                if len(group) > LIMIT:
                    lines.append("  - " + t["more"].format(n=len(group) - LIMIT))
    elif entry["status"] == "new" and entry.get("log"):
        lines.append(f"- {t['none']}")
    notes = entry.get("notes")
    if notes and notes.get("text") and entry["status"] in ("new", "wait", "unknown"):
        lines += ["", f"<details><summary>{t['notes'].format(tag=notes.get('tag') or '')}</summary>", "",
                  "```text", notes["text"], "```", "", "</details>"]
    return lines


def summary(builds, found):
    roots = {k: v for k, v in builds.items() if k in ("KSUN", "BSU")}
    news = [e["name"] for e in found if e["status"] == "new"]
    waits = [e for e in found if e.get("wait")]
    out = ["## 🔎 Cek pembaruan / Check for updates", ""]
    for lang in ("id", "en"):
        t = T[lang]
        out += [f"<details{' open' if lang == 'id' else ''}><summary>{t['flag']}</summary>", ""]
        if roots:
            out.append(t["build"].format(names=", ".join(news)) if news else t["nothing"])
        if waits:
            out += ["", t["waits"], *[f"- {e['name']}: {e['wait'][lang]}" for e in waits]]
        if roots:
            runs = ", ".join(f"{'KernelSU Next' if k == 'KSUN' else 'BakaSU'} [run #{v['run']}]({v['url']}) ({when(v['date'], lang)})"
                             for k, v in sorted(roots.items(), key=lambda kv: kv[0] != "KSUN"))
            out += ["", t["lastrun"].format(roots=runs)]
        else:
            out += [t["norun"] + (f" ({builds['error']})" if builds.get("error") else "")]
        out += ["", f"| {t['component']} | {t['last']} | {t['newest']} | {t['status']} |", "|---|---|---|---|"]
        for entry in found:
            base = (entry.get("base") or {}).get("label", "-")
            out.append(f"| {entry['name']} | {base} | {version_cell(entry, lang)} | {status_cell(entry, lang)} |".replace("\n", " "))
        details = [(e, change_lines(e, lang)) for e in found]
        details = [(e, lines) for e, lines in details if lines]
        if details:
            out += ["", f"### {t['changes']}", ""]
            for entry, lines in details:
                out += [f"**{entry['name']}**", "", *lines, ""]
        out += ["", f"<sub>{t['only']}</sub>", "", "</details>", ""]
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    builds, found = gather(Net(), args.repo)
    text = summary(builds, found)
    if args.out:
        args.out.write_text(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

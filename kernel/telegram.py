#!/usr/bin/env python3
"""Telegram post of one kernel build, in Indonesian and English, ready to copy (owner 2026-10-24).

What's new is measured, not written by hand: this build (build.env) against the previous release of
the same root manager (kernel, root, SUSFS, NoMount, features). Fixes are the fix(kernel...) commits
since that release; the owner's note at publishing time is added as it is.

Usage: telegram.py BUILD_ENV --repo OWNER/REPO --sha COMMIT --link URL [--tested] [--note TEXT]
                   --out DIR [--summary]
Writes DIR/id.txt and DIR/en.txt; --summary also prints both as a summary section, each in a code
block (GitHub puts a copy button at its top right).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RELEASE_TAG = re.compile(r"^v\d{2}\.\d{2}\.\d{2}-r\d+$")  # this repository's kernels (not arsip-, cogan-smart-)
WORDS = {
    "id": {"new": "✨ Baru", "fixes": "🔧 Perbaikan", "note": "📝 Catatan", "features": "🧩 Fitur",
           "same": "Komponen sama dengan {prev}", "first": "Rilis pertama varian ini",
           "baseline": "Dibandingkan dengan {prev}", "unknown": "Riwayat rilis belum dapat dibaca; perubahan belum dapat dibandingkan",
           "no_fixes": "Tidak ada commit perbaikan kernel tambahan yang tercatat pada rentang ini",
           "first_fixes": "Belum ada rilis pembanding untuk varian ini",
           "unknown_fixes": "Daftar commit perbaikan belum dapat dibaca",
           "kernel": "Kernel ACK {old} → {new}", "root": "{name} `{old}` → `{new}`", "susfs": "SUSFS {old} → {new}",
           "ack": "Rilis ACK {old} → {new}", "unicode": "Unicode fix WildKernel `{old}` → `{new}`",
           "neutron": "Neutron clang {old} → {new}",
           "nomount": "NoMount {old} → {new}", "added": "Fitur baru: {names}", "removed": "Fitur dilepas: {names}",
           "tested": "✅ Diuji di HP", "untested": "⚠️ Belum diuji di HP", "download": "⬇️ Unduh"},
    "en": {"new": "✨ New", "fixes": "🔧 Fixes", "note": "📝 Note", "features": "🧩 Features",
           "same": "Same components as {prev}", "first": "First release of this variant",
           "baseline": "Compared with {prev}", "unknown": "Release history could not be read; changes could not be compared",
           "no_fixes": "No additional kernel fix commits recorded in this range",
           "first_fixes": "No earlier release of this variant to compare with",
           "unknown_fixes": "The fix commit list could not be read",
           "kernel": "ACK kernel {old} → {new}", "root": "{name} `{old}` → `{new}`", "susfs": "SUSFS {old} → {new}",
           "ack": "ACK release {old} → {new}", "unicode": "WildKernel Unicode fix `{old}` → `{new}`",
           "neutron": "Neutron clang {old} → {new}",
           "nomount": "NoMount {old} → {new}", "added": "New features: {names}", "removed": "Features dropped: {names}",
           "tested": "✅ Tested on the phone", "untested": "⚠️ Not tested on the phone yet", "download": "⬇️ Download"},
}


def read_env(path):
    return dict(line.split("=", 1) for line in Path(path).read_text().splitlines() if "=" in line)


def feature_names(text):
    """'SUSFS, BBRv3 (default, also bbr3), BBG' -> ['SUSFS', 'BBRv3', 'BBG']."""
    return [name.strip() for name in re.sub(r"\([^)]*\)", "", text).split(",") if name.strip()]


def parse_release(body):
    """The component lines that kernel/release_notes.py writes into a release."""
    found = {}
    for pattern, key in ((r"^- Kernel: `([^`]+)`", "kernel"), (r"^- Root: (.+?) [^ ]+ `([0-9a-f]{7,})`", "root"),
                         (r"\+ SUSFS (\S+) `([0-9a-f]{7,})`", "susfs"), (r"^- NoMount: (\S+)", "nomount"),
                         (r"^- Fitur / features: (.+)$", "features"), (r"\(ACK `([^`]+)`\)", "ack"),
                         (r"^- Unicode fix: WildKernel `([0-9a-f]+)`", "unicode"),
                         (r"Neutron clang (\S+)", "neutron"),
                         (r"^<!-- cogan-build-sha: ([0-9a-f]{40}) -->$", "sha")):
        match = re.search(pattern, body, re.MULTILINE)
        if match:
            found[key] = match.groups() if len(match.groups()) > 1 else match[1]
    return found


def previous(releases, env):
    """Newest earlier kernel release of the same root manager, or None."""
    for release in releases:  # the API lists the newest first
        if release.get("draft") or not RELEASE_TAG.match(release.get("tag_name", "")):
            continue
        # Text-only previews of old runs must not compare against their own or a newer release.
        current = env.get("RELEASE", "")
        if RELEASE_TAG.fullmatch(current) and tuple(map(int, re.findall(r"\d+", release["tag_name"]))) >= \
                tuple(map(int, re.findall(r"\d+", current))):
            continue
        # A Release From Run can contain both root managers, each under its own ## heading.
        # Read the matching section so BakaSU never inherits KernelSU Next's component versions.
        for section in re.split(r"(?=^## )", release.get("body") or "", flags=re.MULTILINE):
            parsed = parse_release(section)
            if parsed.get("root", ("",))[0].startswith(env.get("ROOT_NAME", "?")):
                return {"tag": release["tag_name"], "sha": release.get("target_commitish", ""), **parsed}
    return None


def fixes(commits):
    """fix(kernel...) commit titles, without the prefix and the PR number."""
    found = []
    for message in commits:
        title = message.splitlines()[0] if message else ""
        match = re.match(r"fix\(kernel[^)]*\):\s*(.+?)(?:\s*\(#\d+\))?$", title)
        if match:
            found.append(match[1])
    return found


def whats_new(env, prev, lang, history_available=True):
    w = WORDS[lang]
    if not history_available:
        return [w["unknown"]]
    if not prev:
        return [w["first"]]
    items = []
    if prev.get("kernel") and prev["kernel"] != env.get("LINUX_VERSION"):
        items.append(w["kernel"].format(old=prev["kernel"], new=env.get("LINUX_VERSION")))
    if prev.get("ack") and env.get("ACK_TAG") and prev["ack"] != env["ACK_TAG"]:
        items.append(w["ack"].format(old=prev["ack"], new=env["ACK_TAG"]))
    if prev.get("root") and not env.get("ROOT_COMMIT", "").startswith(prev["root"][1]):
        items.append(w["root"].format(name=env.get("ROOT_NAME"), old=prev["root"][1][:12], new=env.get("ROOT_COMMIT", "")[:12]))
    if prev.get("susfs") and not env.get("SUSFS_COMMIT", "").startswith(prev["susfs"][1]):
        items.append(w["susfs"].format(old=f"{prev['susfs'][0]} `{prev['susfs'][1][:12]}`",
                                       new=f"{env.get('SUSFS_VERSION')} `{env.get('SUSFS_COMMIT', '')[:12]}`"))
    if prev.get("nomount") and prev["nomount"] != env.get("NOMOUNT"):
        items.append(w["nomount"].format(old=prev["nomount"], new=env.get("NOMOUNT")))
    if prev.get("unicode") and env.get("UNICODE_FIX", "-") != "-" and not env["UNICODE_FIX"].startswith(prev["unicode"]):
        items.append(w["unicode"].format(old=prev["unicode"], new=env["UNICODE_FIX"][:12]))
    if prev.get("neutron") and env.get("NEUTRON") and prev["neutron"] != env["NEUTRON"]:
        items.append(w["neutron"].format(old=prev["neutron"], new=env["NEUTRON"]))
    old, new = feature_names(prev.get("features", "")), feature_names(env.get("FEATURES", ""))
    if [n for n in new if n not in old]:
        items.append(w["added"].format(names=", ".join(n for n in new if n not in old)))
    if [n for n in old if n not in new]:
        items.append(w["removed"].format(names=", ".join(n for n in old if n not in new)))
    return items or [w["same"].format(prev=prev["tag"])]


def fix_items(lang, prev, fix_titles, history_available=True, fixes_available=True):
    if fix_titles:
        return list(fix_titles)
    key = "unknown_fixes" if not history_available or not fixes_available else "no_fixes" if prev else "first_fixes"
    return [WORDS[lang][key]]


def changelog_section(env, repo, prev=None, fix_titles=(), history_available=True, fixes_available=True, source_sha=""):
    """The same measured changes as the Telegram post, included in the published release notes."""
    lines = ["### What's New & Fixes", ""]
    for lang in ("id", "en"):
        w = WORDS[lang]
        lines += [f"**{HEADINGS[lang][0]}**", ""]
        if prev:
            link = f"[{prev['tag']}](https://github.com/{repo}/releases/tag/{prev['tag']})"
            lines += [w["baseline"].format(prev=link), ""]
        lines += [f"**{w['new']}**", *[f"- {item}" for item in whats_new(env, prev, lang, history_available)], "",
                  f"**{w['fixes']}**", *[f"- {item}" for item in fix_items(lang, prev, fix_titles, history_available, fixes_available)], ""]
    if re.fullmatch(r"[0-9a-f]{40}", source_sha):
        lines += [f"<!-- cogan-build-sha: {source_sha} -->", ""]
    return "\n".join(lines)


def post(env, lang, prev=None, fix_titles=(), link="", tested=False, note="", history_available=True,
         fixes_available=True, source_sha=""):
    w = WORDS[lang]
    lines = ["🧠 Cogan Kernel · Xiaomi 14T Pro (rothko)",
             f"📦 {env.get('RELEASE', '')} · ACK {env.get('LINUX_VERSION', '')} · {env.get('ROOT_NAME', '')} + SUSFS "
             f"{env.get('SUSFS_VERSION', '')}"]
    if prev:
        lines += ["", "📌 " + w["baseline"].format(prev=prev["tag"])]
    lines += ["", w["new"], *[f"• {item}" for item in whats_new(env, prev, lang, history_available)],
              "", w["fixes"], *[f"• {title}" for title in fix_items(lang, prev, fix_titles, history_available, fixes_available)]]
    if note.strip():
        lines += ["", w["note"], *note.replace("\\n", "\n").strip().splitlines()]
    lines += ["", f"{w['features']}: {env.get('FEATURES', '')}", w["tested"] if tested else w["untested"]]
    if link:
        lines.append(f"{w['download']}: {link}")
    return "\n".join(lines) + "\n"


HEADINGS = {"id": ("🇮🇩 Bahasa Indonesia", "**📣 Teks Telegram** (salin lewat tombol di pojok kanan atas kotak)"),
            "en": ("🇬🇧 English", "**📣 Telegram post** (copy with the button at the top right of the box)")}


def block(lang, text):
    """Markdown lines of one post: a heading and a code block (copy button on GitHub)."""
    return [HEADINGS[lang][1], "", "```text", text.rstrip("\n"), "```", ""]


def summary_section(posts):
    lines = []
    for lang in ("id", "en"):
        lines += [f"<details{' open' if lang == 'id' else ''}><summary>{HEADINGS[lang][0]}</summary>", "",
                  *block(lang, posts[lang]), "</details>", ""]
    return "\n".join(lines)


def gh(path):
    try:
        result = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=120)
        return json.loads(result.stdout) if result.returncode == 0 and result.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def changes(env, repo, sha="", api=gh):
    """Read the comparison once; release notes and both copyable posts use the same result."""
    releases = api(f"repos/{repo}/releases?per_page=50")
    available = isinstance(releases, list)
    prev = previous(releases if available else [], env)
    titles, compared = [], False
    if prev and re.fullmatch(r"[0-9a-f]{40}", prev["sha"]) and re.fullmatch(r"[0-9a-f]{40}", sha):
        comparison = api(f"repos/{repo}/compare/{prev['sha']}...{sha}")
        if isinstance(comparison, dict) and isinstance(comparison.get("commits"), list) and comparison.get("status") != "behind":
            titles = fixes(commit["commit"]["message"] for commit in comparison["commits"])
            compared = True
    return {"prev": prev, "fix_titles": titles, "history_available": available,
            "fixes_available": compared or (available and prev is None), "source_sha": sha}


def main(argv=None, api=gh):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("build_env", type=Path)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", default="")
    parser.add_argument("--link", default="")
    parser.add_argument("--tested", action="store_true")
    parser.add_argument("--note", default="")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", action="store_true", help="also print a bilingual summary section")
    args = parser.parse_args(argv)
    env = read_env(args.build_env)
    measured = changes(env, args.repo, args.sha, api)
    args.out.mkdir(parents=True, exist_ok=True)
    posts = {lang: post(env, lang, link=args.link, tested=args.tested, note=args.note, **measured) for lang in ("id", "en")}
    for lang, text in posts.items():
        (args.out / f"{lang}.txt").write_text(text)
    if args.summary:
        sys.stdout.write(summary_section(posts))
    return 0


if __name__ == "__main__":
    sys.exit(main())

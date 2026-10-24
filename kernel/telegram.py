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
           "kernel": "Kernel ACK {old} → {new}", "root": "{name} `{old}` → `{new}`", "susfs": "SUSFS {old} → {new}",
           "nomount": "NoMount {old} → {new}", "added": "Fitur baru: {names}", "removed": "Fitur dilepas: {names}",
           "tested": "✅ Diuji di HP", "untested": "⚠️ Belum diuji di HP", "download": "⬇️ Unduh"},
    "en": {"new": "✨ New", "fixes": "🔧 Fixes", "note": "📝 Note", "features": "🧩 Features",
           "same": "Same components as {prev}", "first": "First release of this variant",
           "kernel": "ACK kernel {old} → {new}", "root": "{name} `{old}` → `{new}`", "susfs": "SUSFS {old} → {new}",
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
                         (r"^- Fitur / features: (.+)$", "features")):
        match = re.search(pattern, body, re.MULTILINE)
        if match:
            found[key] = match.groups() if len(match.groups()) > 1 else match[1]
    return found


def previous(releases, env):
    """Newest earlier kernel release of the same root manager, or None."""
    for release in releases:  # the API lists the newest first
        if release.get("draft") or not RELEASE_TAG.match(release.get("tag_name", "")):
            continue
        if release["tag_name"] == env.get("RELEASE"):
            continue
        parsed = parse_release(release.get("body") or "")
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


def whats_new(env, prev, lang):
    w = WORDS[lang]
    if not prev:
        return [w["first"]]
    items = []
    if prev.get("kernel") and prev["kernel"] != env.get("LINUX_VERSION"):
        items.append(w["kernel"].format(old=prev["kernel"], new=env.get("LINUX_VERSION")))
    if prev.get("root") and not env.get("ROOT_COMMIT", "").startswith(prev["root"][1]):
        items.append(w["root"].format(name=env.get("ROOT_NAME"), old=prev["root"][1][:12], new=env.get("ROOT_COMMIT", "")[:12]))
    if prev.get("susfs") and not env.get("SUSFS_COMMIT", "").startswith(prev["susfs"][1]):
        items.append(w["susfs"].format(old=f"{prev['susfs'][0]} `{prev['susfs'][1][:12]}`",
                                       new=f"{env.get('SUSFS_VERSION')} `{env.get('SUSFS_COMMIT', '')[:12]}`"))
    if prev.get("nomount") and prev["nomount"] != env.get("NOMOUNT"):
        items.append(w["nomount"].format(old=prev["nomount"], new=env.get("NOMOUNT")))
    old, new = feature_names(prev.get("features", "")), feature_names(env.get("FEATURES", ""))
    if [n for n in new if n not in old]:
        items.append(w["added"].format(names=", ".join(n for n in new if n not in old)))
    if [n for n in old if n not in new]:
        items.append(w["removed"].format(names=", ".join(n for n in old if n not in new)))
    return items or [w["same"].format(prev=prev["tag"])]


def post(env, lang, prev=None, fix_titles=(), link="", tested=False, note=""):
    w = WORDS[lang]
    lines = ["🧠 Cogan Kernel · Xiaomi 14T Pro (rothko)",
             f"📦 {env.get('RELEASE', '')} · ACK {env.get('LINUX_VERSION', '')} · {env.get('ROOT_NAME', '')} + SUSFS "
             f"{env.get('SUSFS_VERSION', '')}", "", w["new"], *[f"• {item}" for item in whats_new(env, prev, lang)]]
    if fix_titles:
        lines += ["", w["fixes"], *[f"• {title}" for title in fix_titles]]
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
    result = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=120)
    return json.loads(result.stdout) if result.returncode == 0 and result.stdout.strip() else None


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
    # Best effort: without the API the post still lists what this build is.
    prev = previous(api(f"repos/{args.repo}/releases?per_page=50") or [], env)
    fix_titles = []
    if prev and re.fullmatch(r"[0-9a-f]{40}", prev["sha"]) and re.fullmatch(r"[0-9a-f]{40}", args.sha):
        compare = api(f"repos/{args.repo}/compare/{prev['sha']}...{args.sha}") or {}
        fix_titles = fixes(c["commit"]["message"] for c in compare.get("commits", []))
    args.out.mkdir(parents=True, exist_ok=True)
    posts = {lang: post(env, lang, prev, fix_titles, args.link, args.tested, args.note) for lang in ("id", "en")}
    for lang, text in posts.items():
        (args.out / f"{lang}.txt").write_text(text)
    if args.summary:
        sys.stdout.write(summary_section(posts))
    return 0


if __name__ == "__main__":
    sys.exit(main())

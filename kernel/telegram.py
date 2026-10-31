#!/usr/bin/env python3
"""Telegram post of one kernel build, in Indonesian and English, ready to copy (owner 2026-10-24).

What's new is measured, not written by hand: this build (build.env) against the previous release of
the same root manager (kernel, root, SUSFS, NoMount, features). Fixes are the fix(kernel...) commits
since that release. Each language uses its own fix descriptions and owner note.

Usage: telegram.py BUILD_ENV --repo OWNER/REPO --sha COMMIT --link URL [--tested] [--note TEXT] [--note-en TEXT]
                   --out DIR [--summary]
Writes DIR/id.txt and DIR/en.txt; --summary also prints both as a summary section, each in a code
block (GitHub puts a copy button at its top right).
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

if __package__:  # imported as kernel.telegram
    from . import upstream as up
else:            # run as kernel/telegram.py (Builder summary)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import upstream as up  # noqa: E402

SUSFS_REPO = "https://gitlab.com/simonpunk/susfs4ksu"
RELEASE_TAG = re.compile(r"^v\d{2}\.\d{2}\.\d{2}-r\d+$")  # this repository's kernels (not arsip-, cogan-smart-)
# Reviewed translations of historical subjects. New commits can supply Release-Fix-ID/EN trailers.
FIX_EN = {
    "BakaSU main cukup punya artifact manager, tidak menunggu Telegram":
        "Use BakaSU main when manager artifacts are available, without waiting for Telegram upload",
    "SUSFS terbaru terpasang di ACK 6.1.138 dan 6.1.145":
        "Apply the latest SUSFS patch to ACK 6.1.138 and 6.1.145",
    "alat AnyKernel3 arm64 untuk rothko; Rilis dari run tidak membongkar ZIP kernel":
        "Use ARM64 AnyKernel3 tools for rothko and preserve the kernel ZIP in Release From Run",
    "ccache di ~/.ccache supaya cache tersimpan":
        "Store ccache in ~/.ccache so the build cache is saved",
}
WORDS = {
    "id": {"new": "✨ Baru", "fixes": "🔧 Perbaikan", "note": "📝 Catatan", "features": "🧩 Fitur",
           "same": "Komponen sama dengan {prev}", "first": "Rilis pertama varian ini",
           "baseline": "Dibandingkan dengan {prev}", "unknown": "Riwayat rilis belum dapat dibaca; perubahan belum dapat dibandingkan",
           "no_fixes": "Tidak ada perbaikan baru",
           "first_fixes": "Belum ada rilis pembanding untuk varian ini",
           "unknown_fixes": "Daftar commit perbaikan belum dapat dibaca",
           "untranslated_fix": "Perbaikan kernel tercatat dalam riwayat sumber",
           "kernel": "Kernel ACK {old} → {new}", "susfs": "SUSFS {version} diperbarui",
           "ack": "Rilis ACK {old} → {new}", "unicode": "Unicode fix WildKernel diperbarui",
           "neutron": "Neutron clang {old} → {new}",
           "nomount": "NoMount {old} → {new}", "added": "Fitur baru: {names}", "removed": "Fitur dilepas: {names}",
           "tested": "✅ Diuji di HP", "untested": "⚠️ Belum diuji di HP", "download": "⬇️ Unduh"},
    "en": {"new": "✨ New", "fixes": "🔧 Fixes", "note": "📝 Note", "features": "🧩 Features",
           "same": "Same components as {prev}", "first": "First release of this variant",
           "baseline": "Compared with {prev}", "unknown": "Release history could not be read; changes could not be compared",
           "no_fixes": "No new fixes",
           "first_fixes": "No earlier release of this variant to compare with",
           "unknown_fixes": "The fix commit list could not be read",
           "untranslated_fix": "Kernel fix recorded in the source history; English description not supplied",
           "kernel": "ACK kernel {old} → {new}", "susfs": "SUSFS {version} updated",
           "ack": "ACK release {old} → {new}", "unicode": "WildKernel Unicode fix updated",
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


def fixes(commits, lang="id"):
    """Localized fix descriptions; never pass an unlabelled source subject to English output."""
    found = []
    for commit in commits:
        message = commit["commit"]["message"] if isinstance(commit, dict) else commit
        title = message.splitlines()[0] if message else ""
        match = re.match(r"fix\(kernel[^)]*\):\s*(.+?)(?:\s*\(#\d+\))?$", title)
        if match:
            localized = re.search(rf"^Release-Fix-{lang.upper()}:[ \t]*(.+)$", message, re.MULTILINE)
            text = localized[1].strip() if localized else match[1] if lang == "id" else FIX_EN.get(match[1])
            if not text:
                text = WORDS[lang]["untranslated_fix"]
                if isinstance(commit, dict) and re.fullmatch(r"[0-9a-f]{40}", commit.get("sha", "")):
                    sha = commit["sha"]
                    url = commit.get("html_url")
                    text += f" ([{sha[:12]}]({url}))" if url else f" (`{sha[:12]}`)"
            found.append(text)
    return found


def upstream_lines(env, prev, lang, upstream=None):
    """[(What's new line, fix line or None)] of the root manager and SUSFS when their commit changed, in plain
    words without hashes (owner 2026-10-31). upstream: {"root"/"susfs": new commit titles, None = unreadable}."""
    found, upstream = [], upstream or {}
    if prev and prev.get("root") and not env.get("ROOT_COMMIT", "").startswith(prev["root"][1]):
        # KernelSU Next: the kernel comes from the fork, its manager from KernelSU Next's own CI.
        found.append(up.describe(env.get("ROOT_NAME", ""), upstream.get("root"), lang,
                                 kernel_only=env.get("ROOT_NAME") == "KernelSU Next"))
    if prev and prev.get("susfs") and not env.get("SUSFS_COMMIT", "").startswith(prev["susfs"][1]):
        old, new = prev["susfs"][0], env.get("SUSFS_VERSION", "")
        head = f"SUSFS {old} → {new}" if old != new else WORDS[lang]["susfs"].format(version=new)
        found.append(up.describe("SUSFS", upstream.get("susfs"), lang, head=head))
    return found


def whats_new(env, prev, lang, history_available=True, upstream=None):
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
    items += [line for line, _ in upstream_lines(env, prev, lang, upstream)]
    if prev.get("nomount") and prev["nomount"] != env.get("NOMOUNT"):
        items.append(w["nomount"].format(old=prev["nomount"], new=env.get("NOMOUNT")))
    if prev.get("unicode") and env.get("UNICODE_FIX", "-") != "-" and not env["UNICODE_FIX"].startswith(prev["unicode"]):
        items.append(w["unicode"])
    if prev.get("neutron") and env.get("NEUTRON") and prev["neutron"] != env["NEUTRON"]:
        items.append(w["neutron"].format(old=prev["neutron"], new=env["NEUTRON"]))
    old, new = feature_names(prev.get("features", "")), feature_names(env.get("FEATURES", ""))
    if [n for n in new if n not in old]:
        items.append(w["added"].format(names=", ".join(n for n in new if n not in old)))
    if [n for n in old if n not in new]:
        items.append(w["removed"].format(names=", ".join(n for n in old if n not in new)))
    return items or [w["same"].format(prev=prev["tag"])]


def fix_items(lang, prev, fix_titles, history_available=True, fixes_available=True, upstream_fixes=()):
    """This repository's kernel fixes, then what the root manager and SUSFS developers fixed."""
    items = own_fixes(lang, prev, fix_titles, history_available, fixes_available)
    if upstream_fixes and items == [WORDS[lang]["no_fixes"]]:
        items = []
    return items + list(upstream_fixes)


def own_fixes(lang, prev, fix_titles, history_available=True, fixes_available=True):
    if isinstance(fix_titles, dict):
        if fix_titles.get(lang):
            return list(fix_titles[lang])
        if any(fix_titles.values()):
            return [WORDS[lang]["untranslated_fix"]]
    elif fix_titles:
        return fixes([f"fix(kernel): {title}" for title in fix_titles], lang)
    key = "unknown_fixes" if not history_available or not fixes_available else "no_fixes" if prev else "first_fixes"
    return [WORDS[lang][key]]


def upstream_fixes(env, prev, lang, upstream=None):
    return [fix for _, fix in upstream_lines(env, prev, lang, upstream) if fix]


def changelog_section(env, repo, prev=None, fix_titles=(), history_available=True, fixes_available=True, source_sha="",
                      upstream=None):
    """The same measured changes as the Telegram post, included in the published release notes."""
    lines = ["### What's New & Fixes", ""]
    for lang in ("id", "en"):
        w = WORDS[lang]
        lines += [f"**{HEADINGS[lang][0]}**", ""]
        if prev:
            link = f"[{prev['tag']}](https://github.com/{repo}/releases/tag/{prev['tag']})"
            lines += [w["baseline"].format(prev=link), ""]
        lines += [f"**{w['new']}**", *[f"- {item}" for item in whats_new(env, prev, lang, history_available, upstream)], "",
                  f"**{w['fixes']}**", *[f"- {item}" for item in fix_items(lang, prev, fix_titles, history_available,
                                                                          fixes_available, upstream_fixes(env, prev, lang, upstream))], ""]
    if re.fullmatch(r"[0-9a-f]{40}", source_sha):
        lines += [f"<!-- cogan-build-sha: {source_sha} -->", ""]
    return "\n".join(lines)


def post(env, lang, prev=None, fix_titles=(), link="", tested=False, note="", history_available=True,
         fixes_available=True, source_sha="", note_en="", upstream=None):
    w = WORDS[lang]
    lines = ["🧠 Cogan Kernel · Xiaomi 14T Pro (rothko)",
             f"📦 {env.get('RELEASE', '')} · ACK {env.get('LINUX_VERSION', '')} · {env.get('ROOT_NAME', '')} + SUSFS "
             f"{env.get('SUSFS_VERSION', '')}"]
    if prev:
        lines += ["", "📌 " + w["baseline"].format(prev=prev["tag"])]
    lines += ["", w["new"], *[f"• {item}" for item in whats_new(env, prev, lang, history_available, upstream)],
              "", w["fixes"], *[f"• {title}" for title in fix_items(lang, prev, fix_titles, history_available, fixes_available,
                                                                     upstream_fixes(env, prev, lang, upstream))]]
    localized_note = note if lang == "id" else note_en
    if localized_note.strip():
        lines += ["", w["note"], *localized_note.replace("\\n", "\n").strip().splitlines()]
    lines += ["", f"{w['features']}: {env.get('FEATURES', '')}", w["tested"] if tested else w["untested"]]
    if link:
        lines.append(f"{w['download']}: {link}")
    return "\n".join(lines) + "\n"


def merged(groups):
    """[(label, items)] -> the items every group has, once, then each group's own items under its label."""
    common = [item for item in groups[0][1] if all(item in items for _, items in groups[1:])]
    own = [item if item.startswith(label) else f"{label}: {item}"
           for label, items in groups for item in items if item not in common]
    return common + own


def joined(values):
    return " / ".join(dict.fromkeys(value for value in values if value))


def release_post(builds, lang, link="", tested=False, note="", note_en=""):
    """One post for one release (owner 2026-10-26: "mesti copas 2 kali"): KernelSU Next and BakaSU of a
    Release From Run share one text, each change measured against that root manager's own previous release.
    builds: [(env, measured)] as from changes(); one build gives exactly post()."""
    if len(builds) == 1:
        env, measured = builds[0]
        return post(env, lang, link=link, tested=tested, note=note, note_en=note_en, **measured)
    w = WORDS[lang]
    envs = [env for env, _ in builds]
    versions = {env.get("LINUX_VERSION") for env in envs}
    labels = [env.get("ROOT_NAME", "") + ("" if len(versions) == 1 else f" {env.get('LINUX_VERSION', '')}") for env in envs]
    lines = ["🧠 Cogan Kernel · Xiaomi 14T Pro (rothko)",
             f"📦 {envs[0].get('RELEASE', '')} · ACK {joined(e.get('LINUX_VERSION') for e in envs)} · "
             f"{' & '.join(dict.fromkeys(e.get('ROOT_NAME', '') for e in envs))} + SUSFS {joined(e.get('SUSFS_VERSION') for e in envs)}"]
    prevs = [(label, measured["prev"]["tag"]) for label, (_, measured) in zip(labels, builds) if measured.get("prev")]
    if prevs:
        same = len(prevs) == len(builds) and len({tag for _, tag in prevs}) == 1
        lines += ["", "📌 " + w["baseline"].format(prev=prevs[0][1] if same else ", ".join(f"{tag} ({label})" for label, tag in prevs))]
    new = merged([(label, whats_new(env, measured.get("prev"), lang, measured.get("history_available", True),
                                    measured.get("upstream")))
                  for label, (env, measured) in zip(labels, builds)])
    fixed = merged([(label, fix_items(lang, measured.get("prev"), measured.get("fix_titles", ()),
                                      measured.get("history_available", True), measured.get("fixes_available", True),
                                      upstream_fixes(env, measured.get("prev"), lang, measured.get("upstream"))))
                    for label, (env, measured) in zip(labels, builds)])
    lines += ["", w["new"], *[f"• {item}" for item in new], "", w["fixes"], *[f"• {item}" for item in fixed]]
    localized_note = note if lang == "id" else note_en
    if localized_note.strip():
        lines += ["", w["note"], *localized_note.replace("\\n", "\n").strip().splitlines()]
    features = {env.get("FEATURES", "") for env in envs}
    lines.append("")
    if len(features) == 1:
        lines.append(f"{w['features']}: {envs[0].get('FEATURES', '')}")
    else:
        lines += [f"{w['features']} ({label}): {env.get('FEATURES', '')}" for label, env in zip(labels, envs)]
    lines.append(w["tested"] if tested else w["untested"])
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
    if path.startswith("gitlab:"):  # SUSFS lives on GitLab; its API needs no token for a public project
        try:
            with urllib.request.urlopen("https://gitlab.com/api/v4/" + path[len("gitlab:"):], timeout=60) as reply:
                return json.load(reply)
        except (OSError, ValueError):
            return None
    try:
        result = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=120)
        return json.loads(result.stdout) if result.returncode == 0 and result.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def new_titles(api, repo_url, old, new):
    """Titles of the commits new has and old has not, also after a force-push (the KernelSU Next fork
    rebases), or None when the comparison cannot be read."""
    github = re.fullmatch(r"https://github\.com/([^/]+/[^/]+?)(?:\.git)?/?", repo_url or "")
    gitlab = re.fullmatch(r"https://gitlab\.com/(.+?)(?:\.git)?/?", repo_url or "")

    def titles(base, head):
        if github:
            data = api(f"repos/{github[1]}/compare/{base}...{head}")
            commits = data.get("commits") if isinstance(data, dict) else None
            if isinstance(commits, list):
                return [(c.get("commit") or {}).get("message", "").split("\n")[0] for c in commits]
        elif gitlab:
            data = api(f"gitlab:projects/{urllib.parse.quote(gitlab[1], safe='')}/repository/compare?from={base}&to={head}")
            commits = data.get("commits") if isinstance(data, dict) else None
            if isinstance(commits, list):
                return [c.get("title", "") for c in commits]
        return None

    ahead = titles(old, new)
    behind = titles(new, old) if ahead else []
    if ahead is None or behind is None:
        return None
    return [title for title in ahead if title not in set(behind)]


def changes(env, repo, sha="", api=gh):
    """Read the comparison once; release notes and both copyable posts use the same result."""
    releases = api(f"repos/{repo}/releases?per_page=50")
    available = isinstance(releases, list)
    prev = previous(releases if available else [], env)
    titles, compared = {}, False
    if prev and re.fullmatch(r"[0-9a-f]{40}", prev["sha"]) and re.fullmatch(r"[0-9a-f]{40}", sha):
        comparison = api(f"repos/{repo}/compare/{prev['sha']}...{sha}")
        if isinstance(comparison, dict) and isinstance(comparison.get("commits"), list) and comparison.get("status") != "behind":
            titles = {lang: fixes(comparison["commits"], lang) for lang in ("id", "en")}
            compared = True
    upstream = {}
    if prev and prev.get("root") and not env.get("ROOT_COMMIT", "").startswith(prev["root"][1]):
        upstream["root"] = new_titles(api, env.get("ROOT_REPO", ""), prev["root"][1], env.get("ROOT_COMMIT", ""))
    if prev and prev.get("susfs") and not env.get("SUSFS_COMMIT", "").startswith(prev["susfs"][1]):
        upstream["susfs"] = new_titles(api, SUSFS_REPO, prev["susfs"][1], env.get("SUSFS_COMMIT", ""))
    return {"prev": prev, "fix_titles": titles, "history_available": available,
            "fixes_available": compared or (available and prev is None), "source_sha": sha, "upstream": upstream}


def main(argv=None, api=gh):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("build_env", type=Path)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", default="")
    parser.add_argument("--link", default="")
    parser.add_argument("--tested", action="store_true")
    parser.add_argument("--note", default="")
    parser.add_argument("--note-en", default="")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", action="store_true", help="also print a bilingual summary section")
    args = parser.parse_args(argv)
    env = read_env(args.build_env)
    measured = changes(env, args.repo, args.sha, api)
    args.out.mkdir(parents=True, exist_ok=True)
    posts = {lang: post(env, lang, link=args.link, tested=args.tested, note=args.note, note_en=args.note_en,
                        **measured) for lang in ("id", "en")}
    for lang, text in posts.items():
        (args.out / f"{lang}.txt").write_text(text)
    if args.summary:
        sys.stdout.write(summary_section(posts))
    return 0


if __name__ == "__main__":
    sys.exit(main())

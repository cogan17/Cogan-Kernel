#!/usr/bin/env python3
"""Consolidate the 'What's New & Fixes' of an already-published kernel release body (owner 2026-11-06).

Reuses the changes measured when the release was published: it only removes the per-sublevel
repetition and the version-specific ACK lines (the kernel-choices line already names the versions).
No API, no rebuild. A body with no multi-variant What's New section is returned unchanged.

Usage: tidy_release_notes.py BODY.md   (prints the tidied body; the Rapikan workflow PATCHes it back)
"""
import re
import sys
from pathlib import Path

if __package__:
    from .telegram import compact_components, merged, sublevel_key, unique, WORDS
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from telegram import compact_components, merged, sublevel_key, unique, WORDS  # noqa: E402

ACK_LINE = re.compile(r"^(Kernel ACK |Rilis ACK |ACK kernel |ACK release )")
# (lang, heading, New heading, Fixes heading, baseline prefix)
LANGS = [("id", "🇮🇩 Bahasa Indonesia", "✨ Baru", "🔧 Perbaikan", "Dibandingkan dengan "),
         ("en", "🇬🇧 English", "✨ New", "🔧 Fixes", "Compared with ")]


def bullets(lines, header):
    out, grab = [], False
    for line in lines:
        s = line.strip()
        if s == f"**{header}**":
            grab = True
        elif grab and s.startswith("**") and s.endswith("**"):
            break
        elif grab and s.startswith("- "):
            out.append(s[2:])
    return out


SHA = re.compile(r"<!-- cogan-build-sha: ([0-9a-f]{40}) -->")


def tidy_components(body):
    """Collapse the per-sublevel 'Components & features' section to one '## ROOT' section per root
    manager (owner 2026-11-06). Runs only on the old per-sublevel form (a root with >1 section);
    an already-compact or single-build section is returned unchanged, so re-running is idempotent."""
    m = re.search(r"(<summary>🧩 <b>Komponen & fitur / Components & features</b></summary>\n)(.*?)(\n</details>)",
                  body, re.S)
    if not m:
        return body
    inner = m.group(2)
    first = inner.find("## ")
    if first == -1:
        return body
    variants = []
    for chunk in re.split(r"\n## ", inner[first + 3:]):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        head = chunk.splitlines()[0]
        root = head.split(" · ")[0].strip()
        bul = [l for l in chunk.splitlines() if l.startswith("- ")]
        ver = head.split(" · ")[1].strip() if " · " in head else next(
            (re.search(r"`([^`]+)`", b)[1] for b in bul if b.startswith("- Kernel:")), "")
        sha = SHA.search(chunk)
        variants.append((root, ver, bul, sha[1] if sha else ""))
    counts = {}
    for root, *_ in variants:
        counts[root] = counts.get(root, 0) + 1
    if not variants or max(counts.values()) < 2:  # already compact or single build
        return body
    rebuilt = "\n" + "\n".join(compact_components(variants)).rstrip("\n") + "\n"
    return body[:m.start(2)] + rebuilt + body[m.end(2):]


def tidy(body):
    body = tidy_components(body)
    m = re.search(r"(<summary>✨ <b>What's New & Fixes</b></summary>\n)(.*?)(\n</details>)", body, re.S)
    if not m:
        return body
    inner = m.group(2)
    first = inner.find("#### ")
    if first == -1:
        return body
    note_md = inner[:first].strip("\n")
    chunk = inner[first:]
    if chunk.startswith("#### "):
        chunk = chunk[5:]
    parsed = []  # (root, version, {lang: {new, fixed, baseline}})
    for variant in re.split(r"\n#### ", chunk):
        variant = variant.strip("\n")
        if not variant:
            continue
        head = re.match(r"(.+?) · (\S+)", variant.splitlines()[0])
        if not head:
            continue
        data = {}
        for lang, lh, newh, fixh, basep in LANGS:
            try:
                seg = variant.split(f"**{lh}**", 1)[1]
            except IndexError:
                data[lang] = {"new": [], "fixed": [], "baseline": ""}
                continue
            other = "🇬🇧 English" if lang == "id" else "🇮🇩 Bahasa Indonesia"
            seg = re.split(r"\n<!-- ", seg.split(f"**{other}**", 1)[0])[0]
            lines = seg.splitlines()
            baseline = next((l.strip() for l in lines if l.strip().startswith(basep)), "")
            data[lang] = {"new": bullets(lines, newh), "fixed": bullets(lines, fixh), "baseline": baseline}
        parsed.append((head.group(1).strip(), head.group(2).strip(), data))
    if not parsed:
        return body
    versions = sorted(unique(v for _, v, _ in parsed), key=sublevel_key)
    multi = len(versions) > 1
    out = []
    if note_md.strip():
        out += [note_md.strip(), ""]
    for lang, lh, newh, fixh, basep in LANGS:
        w = WORDS[lang]
        out += [f"**{lh}**", ""]
        if multi:
            out += [w["choices"].format(n=len(versions), versions=", ".join(versions), newest=versions[-1]), ""]
        baselines = unique(d[lang]["baseline"] for _, _, d in parsed if d[lang]["baseline"])
        if baselines:
            out += ([baselines[0]] if len(baselines) == 1 else baselines) + [""]
        new_by_root, fix_by_root = {}, {}
        for root, _, d in parsed:
            new_by_root.setdefault(root, []).extend(x for x in d[lang]["new"] if not ACK_LINE.match(x))
            fix_by_root.setdefault(root, []).extend(d[lang]["fixed"])
        new = merged([(root, unique(items)) for root, items in new_by_root.items()])
        fixed = merged([(root, unique(items)) for root, items in fix_by_root.items()])
        out += [f"**{newh}**", *[f"- {item}" for item in new], "",
                f"**{fixh}**", *[f"- {item}" for item in fixed], ""]
    return body[:m.start(2)] + "\n" + "\n".join(out).rstrip("\n") + "\n" + body[m.end(2):]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    body = Path(argv[0]).read_text() if argv else sys.stdin.read()
    sys.stdout.write(tidy(body))
    return 0


if __name__ == "__main__":
    sys.exit(main())

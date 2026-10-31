#!/usr/bin/env python3
"""Upstream changes in plain words for the release text (owner 2026-10-31: no hashes, end users do not
read them; "memperbaiki selinux", "memperbaiki driver loop").

The commits of a root manager or SUSFS between two releases become short Indonesian and English phrases
by keyword: the area a commit touches (SELinux hiding, mount hiding, compile, ...) and whether it fixes or
improves it. Nothing is translated freely. A title that matches no area is only counted; a title that does
not reach this kernel is left out: SUSFS for the LKM variant, other kernel versions, Samsung, translations,
dependency bumps, CI and docs, and for KernelSU Next everything outside its kernel part (its manager comes
from KernelSU Next's own CI, not from the fork the kernel uses).
"""
import re

LIMIT = 3  # phrases per line; the rest are counted
CLEAN = re.compile(r"\s*\((?:issue )?https?://[^)]*\)|\s*\(#\d+\)|\s+$")
SKIP = re.compile(r"\(LKM\)|weblate|translat|\bdeps?\b|renovate|\bbump|\bcargo\b|\bcrates?\b|^ci\b|workflow|"
                  r"readme|\bdocs?\b|^merge\b|typo|clang-format|\bformat|useless|unused|clean ?up|refactor|rename|"
                  r"samsung|\bkdp\b|\brkp\b|defex|\b(?:4\.\d+|5\.\d+|6\.(?:[2-9]|1\d))\b", re.I)
FIX = re.compile(r"\bfix|\bbugs?\b|crash|leak|\brace\b|\buaf\b|use.after.free|revert|correct|prevent|avoid|"
                 r"\bdo not\b|\bdon't\b|wrong|broken|\bbalance|\bnull\b|panic|deadlock|\berror", re.I)
# (keywords, Indonesian (improves, fixes ...), English (improves, fixes ...)); the first match wins.
AREAS = [
    (r"selinux", ("meningkatkan penyembunyian SELinux", "penyembunyian SELinux"),
     ("improves SELinux hiding", "SELinux hiding")),
    (r"smaps|sus_map|\bmaps\b", ("meningkatkan anti deteksi lewat peta memori", "anti deteksi lewat peta memori"),
     ("improves anti-detection via memory maps", "anti-detection via memory maps")),
    (r"mount", ("meningkatkan penyembunyian mount", "penyembunyian mount"), ("improves mount hiding", "mount hiding")),
    (r"sus_path|dirent|readlink|hidden (?:file|name|path)", ("meningkatkan penyembunyian file dan folder",
     "penyembunyian file dan folder"), ("improves file and folder hiding", "file and folder hiding")),
    (r"kstat|statfs", ("meningkatkan penyamaran info file", "penyamaran info file"),
     ("improves file info spoofing", "file info spoofing")),
    (r"uname|cmdline|spoof", ("meningkatkan penyamaran info sistem", "penyamaran info sistem"),
     ("improves system info spoofing", "system info spoofing")),
    (r"side.?channel|timing|detect|zygote|isolated", ("meningkatkan anti deteksi", "anti deteksi"),
     ("improves anti-detection", "anti-detection")),
    (r"rebase|android14|\bgki\b|patch offset", ("menyesuaikan dengan kernel ACK terbaru", "kecocokan dengan kernel ACK"),
     ("adapts to the newest ACK kernel", "ACK kernel compatibility")),
    (r"crash|\buaf\b|use.after.free|panic|deadlock|null pointer|oops|\brace\b|leak",
     ("meningkatkan stabilitas", "potensi crash"), ("improves stability", "possible crashes")),
    (r"compil|\bbuild\b|kbuild|toolchain|clang", ("memperbarui proses compile", "error saat compile"),
     ("updates the build", "a compile error")),
    (r"\blogs?\b|logging|noisy|spam", ("mengurangi log yang tidak perlu", "log kernel"),
     ("reduces unnecessary logs", "kernel logging")),
    (r"perf\b|performance|optimi|fast ?path|faster|speed|latency|offload|kthread",
     ("meningkatkan performa", "performa"), ("improves performance", "performance")),
    (r"\bloop\b", ("memperbarui driver loop", "driver loop"), ("updates the loop driver", "the loop driver")),
    (r"module|preinit|hot.?install", ("meningkatkan dukungan modul", "dukungan modul"),
     ("improves module support", "module support")),
    (r"manager|webui|\bui\b|monet|theme", ("memperbarui aplikasi manager", "aplikasi manager"),
     ("updates the manager app", "the manager app")),
    (r"ksud|ksuinit|userspace", ("memperbarui alat root (ksud)", "alat root (ksud)"),
     ("updates the root tool (ksud)", "the root tool (ksud)")),
    (r"sync with|upstream", ("menyelaraskan dengan KernelSU resmi", "keselarasan dengan KernelSU resmi"),
     ("syncs with the official KernelSU", "sync with the official KernelSU")),
    (r"\bsu\b|allow.?list|root access|\bshell\b", ("memperbarui pengaturan akses root", "akses root"),
     ("updates root access control", "root access")),
    (r"kprobe|syscall|supercall|\bhooks?\b", ("memperbarui cara root terpasang di kernel", "cara root terpasang di kernel"),
     ("updates how root hooks into the kernel", "the kernel hooks")),
]
WORDS = {"id": {"and": "dan", "fix": "memperbaiki", "other": "{n} perubahan lain", "technical": "{n} perubahan teknis",
                "updated": "{name} diperbarui", "unknown": "{name} diperbarui ke versi terbaru dari pengembang",
                "minor": "{name} diperbarui (perubahan kecil)"},
         "en": {"and": "and", "fix": "fixes", "other": "{n} other change{s}", "technical": "{n} technical change{s}",
                "updated": "{name} updated", "unknown": "{name} updated to the developer's newest version",
                "minor": "{name} updated (minor changes)"}}


def relevant(titles, kernel_only=False):
    """Titles that reach this kernel, without links and PR numbers, each once."""
    kept = []
    for title in titles:
        title = CLEAN.sub("", title.splitlines()[0] if title else "")
        if not title or SKIP.search(title) or (kernel_only and not re.match(r"(?:fix\()?kernel", title, re.I)):
            continue
        if title not in kept:
            kept.append(title)
    return kept


def classify(titles, lang):
    """(improvement phrases, fixed things, how many titles match no area): each phrase once, in the order
    of AREAS (the parts end users notice first), whatever order the commits came in."""
    side = 0 if lang == "id" else 1
    improved, fixed, other = set(), set(), 0
    for title in titles:
        index = next((i for i, area in enumerate(AREAS) if re.search(area[0], title, re.I)), None)
        if index is None:
            other += 1
        else:
            (fixed if FIX.search(title) else improved).add(index)
    return ([AREAS[i][1 + side][0] for i in sorted(improved)], [AREAS[i][1 + side][1] for i in sorted(fixed)], other)


def listing(parts, lang):
    if len(parts) < 2:
        return "".join(parts)
    return ", ".join(parts[:-1]) + f" {WORDS[lang]['and']} " + parts[-1]


def describe(name, titles, lang, head="", kernel_only=False):
    """(What's new line, fix line or None) of one updated component. titles None = not readable.
    head replaces "<name> updated" when the version itself changed, e.g. "SUSFS v2.2.0 → v2.3.0"."""
    w = WORDS[lang]
    if titles is None:
        return head or w["unknown"].format(name=name), None
    kept = relevant(titles, kernel_only)
    if not kept:
        return head or w["minor"].format(name=name), None
    improved, fixed, other = classify(kept, lang)
    other += max(0, len(improved) - LIMIT) + max(0, len(fixed) - LIMIT)
    improved, fixed = improved[:LIMIT], fixed[:LIMIT]
    line = head or w["updated"].format(name=name)
    if improved:
        line += ": " + listing(improved + ([w["other"].format(n=other, s="s" if other > 1 else "")] if other else []), lang)
    elif other:
        line += f" ({w['technical'].format(n=other, s='s' if other > 1 else '')})"
    return line, f"{name}: {w['fix']} {listing(fixed, lang)}" if fixed else None

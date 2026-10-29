#!/usr/bin/env python3
"""Release notes of one kernel build, in Indonesian and English (owner 2026-10-23).

Shared by the Cogan Kernel Builder (Release Type Pre-Release / Release) and Release From Run.
"Diuji di HP" only when the owner tested this build on the phone (--tested).

Usage: release_notes.py BUILD_ENV FILES_DIR --run-url URL --repo OWNER/REPO [--tested] [--note TEXT]
"""
import argparse
from html import escape
import sys
from pathlib import Path
from urllib.parse import quote

USES = {
    "1": ("Flash di **Kernel Flasher** atau TWRP (partisi `boot` saja)", "Flash with **Kernel Flasher** or TWRP (`boot` only)"),
    "2": ("Aplikasi manager root", "Root manager app"),
    "3": ("Manager spoofed (nama paket disamarkan), pasang salah satu", "Spoofed manager (hidden package name), install one"),
    "4": ("Modul di manager", "Manager module"),
    "5": ("Modul SUSFS sidex15 dengan WebUI (build CI terbarunya)", "sidex15's SUSFS module with WebUI (its newest CI build)"),
}


def read_env(path):
    return dict(line.split("=", 1) for line in Path(path).read_text().splitlines() if "=" in line)


def component_lines(env):
    """Keep the component format readable by older release-history readers."""
    root = env["ROOT_NAME"] + (f" {env['ROOT_TAG']}" if env.get("ROOT_TAG") else "") + f" `{env['ROOT_COMMIT'][:12]}`"
    if env.get("KSU_VERSION"):
        root += f" ({env['KSU_VERSION']})"
    return [f"- Kernel: `{env['LINUX_VERSION']}` (ACK `{env['ACK_TAG']}`)",
             f"- Root: {root} + SUSFS {env['SUSFS_VERSION']} `{env['SUSFS_COMMIT'][:12]}`",
             f"- NoMount: {env['NOMOUNT']} · Neutron clang {env['NEUTRON']}",
             f"- Fitur / features: {env['FEATURES']}",
             *([f"- Unicode fix: WildKernel `{env['UNICODE_FIX'][:12]}`"] if env.get("UNICODE_FIX", "-") != "-" else []),
             f"- {env['KMI_COMPAT'].split('; BSP:')[0]}"]


def notes(env, files, run_url, repo, tested=False, note="", changelog=""):
    docs = f"https://github.com/{repo}/blob/main/docs"
    lines = [f"## {env['RELEASE_NAME']} — Xiaomi 14T Pro (rothko)", "", *component_lines(env), ""]
    if note.strip():
        lines += ["> [!NOTE]", *[f"> {line}" for line in note.replace("\\n", "\n").strip().splitlines()], ""]
    if changelog:
        lines += [changelog.rstrip(), ""]
    lines += ["| File | Cara pakai | How to use |", "|---|---|---|"]
    for name in sorted(files):
        id_use, en_use = USES.get(name[0], ("Pasang", "Install"))
        lines.append(f"| `{name}` | {id_use} | {en_use} |")
    lines += ["", "SHA256: `checksums.txt`.", "", "> [!CAUTION]"]
    if tested:
        lines += [f"> 🇮🇩 **Diuji owner di Xiaomi 14T Pro.** Tetap simpan `boot` stok sebelum flash. [Kembali ke stok]({docs}/kembali-ke-stok.md).",
                  f"> 🇬🇧 **Tested by the owner on the Xiaomi 14T Pro.** Keep your stock `boot` before flashing. [Back to stock]({docs}/kembali-ke-stok.en.md)."]
    else:
        lines += [f"> 🇮🇩 Lolos build dan gate KMI; **belum diuji di HP**. Simpan `boot` stok sebelum flash. [Kembali ke stok]({docs}/kembali-ke-stok.md).",
                  f"> 🇬🇧 Passed the build and the KMI gate; **not tested on the phone yet**. Keep your stock `boot` before flashing. [Back to stock]({docs}/kembali-ke-stok.en.md)."]
    lines += ["", f"<sub>Dibangun dari / built from [run]({run_url}) · ZIP kernel ditandatangani / kernel ZIP signed: "
                  f"`gh attestation verify <zip> --repo {repo}`</sub>"]
    return "\n".join(lines) + "\n"


def compact_notes(builds, run_url, repo, tested=False, note="", artifact_run=False, note_en=""):
    """README-style release: short download table, with all longer sections collapsed.

    builds contains (build.env, matching file names, measured changelog Markdown) per variant.
    """
    env = builds[0][0]
    docs = f"https://github.com/{repo}/blob/main/docs"
    base = f"https://github.com/{repo}/releases/download/{quote(env['RELEASE'], safe='')}"

    def download(name, label):
        return f"[{label}]({run_url if artifact_run else base + '/' + quote(name, safe='')})"

    lines = [f'<h2 align="center">{escape(env["RELEASE_NAME"])}</h2>', "",
             '<p align="center">Xiaomi 14T Pro · <code>rothko</code> · Android 16</p>', "",
             f"[📖 Panduan / Guide]({docs}/pasang.md) · [↩️ Pemulihan / Recovery]({docs}/kembali-ke-stok.md) · "
             f"[🔏 Kredit / Credits]({docs}/keaslian-dan-kredit.md)", "",
             "> ✅ **Diuji di HP / Tested on the phone** · Build + KMI ✅" if tested else
             "> ⚠️ **belum diuji di HP** / **not tested on the phone yet** · Build + KMI ✅", "",
             "Pilih satu kernel dan manager yang sesuai / Choose one kernel and its matching manager.", "",
             "| Varian / Variant | Kernel | Manager |", "|---|---|---|"]
    for build, files, _ in builds:
        managers = [download(name, "APK" if name.startswith("2-") else "Spoofed")
                    for name in sorted(files) if name.startswith(("2-", "3-"))]
        root = "KSUN" if build["ROOT_NAME"] == "KernelSU Next" else build["ROOT_NAME"]
        lines.append(f"| **{root}** · {build['LINUX_VERSION']} | {download(build['ZIP'], 'ZIP')} | {' · '.join(managers)} |")
    lines += ["", "Cadangkan `boot` sebelum flash / Back up `boot` before flashing.", "",
              "<details>", "<summary>✨ <b>What's New & Fixes</b></summary>", ""]
    for label, text in (("🇮🇩 Catatan", note), ("🇬🇧 Note", note_en)):
        if text.strip():
            lines += [f"**{label}**", "", *[f"> {line}" for line in text.replace("\\n", "\n").strip().splitlines()], ""]
    for build, _, changelog in builds:
        lines += [f"#### {build['ROOT_NAME']} · {build['LINUX_VERSION']}", ""]
        lines += changelog.splitlines()[1:] if changelog else ["Lihat catatan build / See build notes."]
        lines.append("")
    lines += ["</details>", "", "<details>", "<summary>📦 <b>Modul pendukung / Modules</b></summary>", ""]
    modules = sorted({name for _, files, _ in builds for name in files if name.startswith(("4-", "5-"))})
    labels = {"4": "NoMount", "5": "SUSFS · sidex15 (WebUI)"}
    lines += [f"- {download(name, labels[name[0]])}" for name in modules]
    lines += ["", "</details>", "", "<details>", "<summary>🧩 <b>Komponen & fitur / Components & features</b></summary>", ""]
    for build, _, changelog in builds:
        lines += [f"## {build['ROOT_NAME']} · {build['LINUX_VERSION']}", "", *component_lines(build), ""]
        # Each root section keeps its source commit so future comparisons use the built code.
        lines += [line for line in changelog.splitlines() if line.startswith("<!-- cogan-build-sha: ")]
        lines.append("")
    lines += ["</details>", "", "<details>", "<summary>🔏 <b>SHA256 & sumber / Source</b></summary>", ""]
    lines += [f"- {build['ROOT_NAME']}: `{build['ZIP_SHA256']}`" for build, _, _ in builds] if artifact_run else \
             [f"- {download('checksums.txt', 'checksums.txt')}"]
    lines += [f"- [Build run]({run_url})", "",
              f"`gh attestation verify <zip> --repo {repo}`", "", "</details>", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("build_env", type=Path)
    parser.add_argument("files", type=Path)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--tested", action="store_true")
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)
    files = [p.name for p in args.files.iterdir() if p.is_file() and p.name[:2] in ("1-", "2-", "3-", "4-", "5-", "6-")]
    sys.stdout.write(notes(read_env(args.build_env), files, args.run_url, args.repo, args.tested, args.note))
    return 0


if __name__ == "__main__":
    sys.exit(main())

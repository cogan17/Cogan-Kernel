#!/usr/bin/env python3
"""Release notes of one kernel build, in Indonesian and English (owner 2026-10-23).

Shared by the Cogan Kernel Builder (Release Type Pre-Release / Release) and Release From Run.
"Diuji di HP" only when the owner tested this build on the phone (--tested).

Usage: release_notes.py BUILD_ENV FILES_DIR --run-url URL --repo OWNER/REPO [--tested] [--note TEXT]
"""
import argparse
import sys
from pathlib import Path

USES = {
    "1": ("Flash di **Kernel Flasher** atau TWRP (partisi `boot` saja)", "Flash with **Kernel Flasher** or TWRP (`boot` only)"),
    "2": ("Aplikasi manager root", "Root manager app"),
    "3": ("Manager spoofed (nama paket disamarkan), pasang salah satu", "Spoofed manager (hidden package name), install one"),
    "4": ("Modul di manager", "Manager module"),
    "5": ("Modul SUSFS simonpunk (alat `ksu_susfs`, commit SUSFS yang sama dengan kernel). Pasang **salah satu**: 5 atau 6",
          "simonpunk's SUSFS module (`ksu_susfs` tool, the kernel's own SUSFS commit). Install **one**: 5 or 6"),
    "6": ("Modul SUSFS sidex15 dengan WebUI (build CI terbarunya). Pasang **salah satu**: 5 atau 6",
          "sidex15's SUSFS module with WebUI (its newest CI build). Install **one**: 5 or 6"),
}


def read_env(path):
    return dict(line.split("=", 1) for line in Path(path).read_text().splitlines() if "=" in line)


def notes(env, files, run_url, repo, tested=False, note=""):
    docs = f"https://github.com/{repo}/blob/main/docs"
    root = env["ROOT_NAME"] + (f" {env['ROOT_TAG']}" if env.get("ROOT_TAG") else "") + f" `{env['ROOT_COMMIT'][:12]}`"
    if env.get("KSU_VERSION"):
        root += f" ({env['KSU_VERSION']})"
    lines = [f"## {env['RELEASE_NAME']} — Xiaomi 14T Pro (rothko)", "",
             f"- Kernel: `{env['LINUX_VERSION']}` (ACK `{env['ACK_TAG']}`)",
             f"- Root: {root} + SUSFS {env['SUSFS_VERSION']} `{env['SUSFS_COMMIT'][:12]}`",
             f"- NoMount: {env['NOMOUNT']} · Neutron clang {env['NEUTRON']}",
             f"- Fitur / features: {env['FEATURES']}",
             *([f"- Unicode fix: WildKernel `{env['UNICODE_FIX'][:12]}`"] if env.get("UNICODE_FIX", "-") != "-" else []),
             f"- {env['KMI_COMPAT'].split('; BSP:')[0]}", ""]
    if note.strip():
        lines += ["> [!NOTE]", *[f"> {line}" for line in note.replace("\\n", "\n").strip().splitlines()], ""]
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

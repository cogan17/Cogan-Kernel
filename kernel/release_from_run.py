#!/usr/bin/env python3
"""Validate every build in a green run and prepare one release with all root variants."""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

from kernel.release_notes import compact_notes, read_env
from kernel import telegram as tg

ROOTS = {"KernelSU Next": "KernelSU-Next", "BakaSU": "BakaSU"}
REQUIRED = ("RELEASE", "RELEASE_NAME", "LINUX_VERSION", "ACK_TAG", "ROOT_NAME", "ROOT_COMMIT",
            "SUSFS_VERSION", "SUSFS_COMMIT", "NOMOUNT", "NEUTRON", "FEATURES", "KMI_COMPAT", "ZIP", "ZIP_SHA256")


def prepare(info, files, run_url, repo, tested=False, note="", sha="", api=tg.gh, telegram=None, text_only=False, note_en=""):
    folders = sorted(path for path in info.glob("build-info-*") if path.is_dir())
    if not folders:
        raise ValueError("Tidak ada info build / no build info")
    builds, selected, identities = [], set(), set()
    available = {path.name for path in files.iterdir() if path.is_file() and path.name[:2] in
                 ("1-", "2-", "3-", "4-", "5-", "6-")}
    for folder in folders:
        if not (folder / "build.env").is_file():
            raise ValueError(f"{folder.name}: build.env tidak ada / missing build.env")
        env = read_env(folder / "build.env")
        missing = [key for key in REQUIRED if not env.get(key)]
        if missing:
            raise ValueError(f"{folder.name}: metadata tidak lengkap / incomplete metadata: {', '.join(missing)}")
        root = env["ROOT_NAME"]
        if root not in ROOTS:
            raise ValueError(f"Root manager tidak dikenal / unknown root manager: {root}")
        identity = (root, env["LINUX_VERSION"])
        if identity in identities:
            raise ValueError(f"Build ganda / duplicate build: {root} {env['LINUX_VERSION']}")
        identities.add(identity)
        if not env["KMI_COMPAT"].startswith("KMI Xiaomi 14T Pro (rothko): OK;"):
            raise ValueError(f"{folder.name}: gate KMI tidak lolos / KMI gate did not pass")
        kernel = env["ZIP"]
        if kernel not in available or not kernel.startswith("1-KERNEL_") or not kernel.endswith(".zip"):
            raise ValueError(f"{folder.name}: ZIP kernel tidak ada / missing kernel ZIP: {kernel}")
        if any(kernel == other["ZIP"] for other, _ in builds):
            raise ValueError(f"ZIP dipakai dua build / ZIP shared by two builds: {kernel}")
        if hashlib.sha256((files / kernel).read_bytes()).hexdigest() != env["ZIP_SHA256"]:
            raise ValueError(f"{kernel}: SHA256 berbeda dari build / differs from the build")
        with zipfile.ZipFile(files / kernel) as archive:
            if archive.testzip():
                raise ValueError(f"{kernel}: ZIP rusak / corrupt ZIP")
        managers = sorted(name for name in available if name.startswith(f"2-MANAGER_{ROOTS[root]}_")
                          and name.endswith(".apk"))
        if len(managers) != 1:
            raise ValueError(f"{root}: harus tepat satu APK manager / exactly one manager APK required")
        own = [kernel, *managers, *sorted(name for name in available
               if name.startswith(f"3-MANAGER-SPOOFED_{ROOTS[root]}_") and name.endswith(".apk"))]
        shared = sorted(name for name in available if name.startswith("5-SUSFS-MODULE-SIMONPUNK_")
                        and name.endswith(f"_{env['SUSFS_COMMIT'][:8]}.zip"))
        if len(shared) != 1:
            raise ValueError(f"{folder.name}: modul SUSFS simonpunk tidak cocok / no matching simonpunk SUSFS module")
        if env["NOMOUNT"] != "-":
            shared.append(f"4-NOMOUNT-MODULE_{env['NOMOUNT']}.zip")
        sidex = sorted(name for name in available if name.startswith("6-SUSFS-MODULE-SIDEX15_")
                       and name.endswith(".zip"))
        if not sidex or any(name not in available for name in shared):
            raise ValueError(f"{folder.name}: modul NoMount/SUSFS tidak lengkap / missing NoMount/SUSFS modules")
        own += shared + sidex
        selected.update(own)
        builds.append((env, own))
    for key in ("RELEASE", "RELEASE_NAME"):
        if len({env[key] for env, _ in builds}) != 1:
            raise ValueError(f"{key} berbeda antarbuild / differs between builds; pilih run dengan satu versi / choose one version")
    if selected != available:
        raise ValueError("File tidak cocok dengan info build / files do not match build info: " +
                         ", ".join(sorted(available - selected)))
    metadata = {key: builds[0][0][key] for key in ("RELEASE", "RELEASE_NAME")}
    cached = {}

    def history(path):
        if path not in cached:
            cached[path] = api(path)
        return cached[path]

    link = f"https://github.com/{repo}/releases/tag/{metadata['RELEASE']}"
    if text_only:
        releases = history(f"repos/{repo}/releases?per_page=50")
        if not isinstance(releases, list) or not any(release.get("tag_name") == metadata["RELEASE"]
                                                   and not release.get("draft") for release in releases):
            link = run_url
    sections = []
    summaries = []
    for folder, (env, own) in zip(folders, builds):
        measured = tg.changes(env, repo, sha, history)
        changelog = tg.changelog_section(env, repo, **measured)
        sections.append((env, own, changelog))
        if telegram is not None:
            out = telegram / folder.name
            out.mkdir(parents=True, exist_ok=True)
            posts = {lang: tg.post(env, lang, link=link, tested=tested, note=note, note_en=note_en,
                                  **measured) for lang in ("id", "en")}
            for lang, text in posts.items():
                (out / f"{lang}.txt").write_text(text)
            summaries += ["<details>",
                          f"<summary>📣 <b>{env['ROOT_NAME']} · {env['LINUX_VERSION']} — Telegram (ID/EN)</b></summary>",
                          "", tg.summary_section(posts), "</details>", ""]
    if telegram is not None:
        (telegram / "summary.md").write_text("\n".join(summaries))
    return metadata, compact_notes(sections, run_url, repo, tested, note, artifact_run=link == run_url, note_en=note_en)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("info", type=Path)
    parser.add_argument("files", type=Path)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--tested", action="store_true")
    parser.add_argument("--note", default="")
    parser.add_argument("--note-en", default="")
    parser.add_argument("--sha", default="")
    parser.add_argument("--telegram", type=Path, default=Path("telegram"))
    parser.add_argument("--text-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        metadata, text = prepare(args.info, args.files, args.run_url, args.repo, args.tested, args.note,
                                 args.sha, telegram=args.telegram, text_only=args.text_only, note_en=args.note_en)
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        parser.exit(1, f"::error::{error}\n")
    (args.info / "release.env").write_text("".join(f"{key}={value}\n" for key, value in metadata.items()))
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

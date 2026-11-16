#!/usr/bin/env python3
"""Cogan's hybrid_susfs module for a Builder run: the 6th file, next to sidex15's (owner 2026-11-17).
hybrid_susfs (cogan17/hybrid_SusFS) is simonpunk's SUSFS engine with sidex15's WebUI and BRENE's extras. Its
newest published release ZIP (found by kernel/resolve.py, in the run's snapshot) is downloaded, checked against
the release's SHA256, checked as a module, and named 6-SUSFS-MODULE-HYBRID_<version>.zip. Unlike sidex15's, it
installs only what is in the ZIP, so nothing is rewritten; a web address in its scripts stops the run instead.

Usage: susfs_hybrid.py --snapshots DIR --out DIR   (exit 1 when there is no module)
Writes OUT/6-SUSFS-MODULE-HYBRID_<version>.zip and OUT/susfs-hybrid.env.
"""
import argparse
import hashlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path

if __package__:
    from .susfs_sidex import check, module_info
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from susfs_sidex import check, module_info  # noqa: E402


def download(url, dest):
    subprocess.run(["curl", "-fsSL", "--retry", "3", url, "-o", str(dest)], check=True)


def no_downloads(path):
    """hybrid_susfs never downloads at install or boot; a web address in its scripts means it changed."""
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.endswith(".sh") and re.search(rb"https?://", archive.read(name)):
                raise SystemExit(f"::error::hybrid_susfs module: {name} has a web address; check it again")


def main(argv=None, fetch=download):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    info = module_info(args.snapshots, "susfs_hybrid", "hybrid_susfs")
    if "wait" in info:
        print(f"::error::{info['wait']['en']}")
        return 1
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", info.get("digest", "")):
        print(f"::error::hybrid_susfs {info['tag']}: the release gives no SHA256 for {info['name']}")
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    raw = args.out / "hybrid.download.zip"
    fetch(info["url"], raw)
    digest = "sha256:" + hashlib.sha256(raw.read_bytes()).hexdigest()
    if digest != info["digest"]:
        raw.unlink()
        print(f"::error::hybrid_susfs {info['tag']}: SHA256 differs from its release")
        return 1
    version = check(raw, "hybrid_susfs", "hybrid_susfs")
    no_downloads(raw)
    name = f"6-SUSFS-MODULE-HYBRID_{version}.zip"
    raw.replace(args.out / name)
    lines = {"SUSFS_MODULE": name, "SUSFS_MODULE_SHA256": digest.removeprefix("sha256:"),
             "SUSFS_MODULE_VERSION": version, "SUSFS_MODULE_TAG": info["tag"],
             "SUSFS_MODULE_PRERELEASE": "1" if info.get("prerelease") else "0", "SUSFS_MODULE_RUN": info.get("release", "")}
    text = "".join(f"{key}={value}\n" for key, value in lines.items())
    (args.out / "susfs-hybrid.env").write_text(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

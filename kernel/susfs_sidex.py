#!/usr/bin/env python3
"""sidex15's SUSFS module (with WebUI) for a Builder run: the 5th file. It replaced simonpunk's own module
(owner 2026-10-29: sidex15's module is simonpunk's SUSFS with a WebUI). It has no releases: the newest CI build of its v1.5.2+ branch that
still has its artifact (found by kernel/resolve.py, in the run's snapshot) is taken as sidex15 built it.
The artifact is the module itself (module.prop at the top); it is checked, then named
5-SUSFS-MODULE-SIDEX15_<version>.zip. It installs sidex15's ksu_susfs tool in /data/adb/ksu/bin.

Usage: susfs_sidex.py --snapshots DIR --out DIR   (GH_TOKEN for the artifact; exit 1 when there is none)
Writes OUT/5-SUSFS-MODULE-SIDEX15_<version>.zip and OUT/susfs-sidex15.env.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path


def download(repo, artifact, dest):
    with open(dest, "wb") as out:
        subprocess.run(["gh", "api", f"repos/{repo}/actions/artifacts/{artifact}/zip"], stdout=out, check=True)


def module_info(snapshots):
    """The sidex15 build of the run's snapshots, or {"wait": ...} when none was found."""
    found = [json.loads(path.read_text()).get("susfs_sidex") for path in sorted(Path(snapshots).glob("*.json"))]
    found = [entry for entry in found if entry]
    return next((entry for entry in found if "wait" not in entry), found[0] if found else
                {"wait": {"id": "Snapshot run ini tidak mencatat modul sidex15.", "en": "This run's snapshot holds no sidex15 module."}})


def check(path):
    """version of a sidex15 module ZIP; SystemExit when it is not one."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if archive.testzip():
            raise SystemExit("::error::sidex15 module: corrupt ZIP")
        unsafe = [n for n in names if n.startswith("/") or ".." in n.split("/")]
        if unsafe:
            raise SystemExit(f"::error::sidex15 module: unsafe paths {unsafe[:3]}")
        missing = {"module.prop", "customize.sh"} - set(names)
        if missing:
            raise SystemExit(f"::error::sidex15 module: missing {sorted(missing)}")
        prop = dict(line.split("=", 1) for line in archive.read("module.prop").decode().splitlines() if "=" in line)
    if prop.get("id") != "susfs4ksu":
        raise SystemExit(f"::error::sidex15 module: id {prop.get('id')!r}, expected susfs4ksu")
    version = prop.get("version", "").strip()
    if not re.fullmatch(r"v[0-9][0-9A-Za-z.+-]*", version):
        raise SystemExit(f"::error::sidex15 module: version {version!r}")
    return version


def main(argv=None, fetch=download):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    info = module_info(args.snapshots)
    if "wait" in info:
        print(f"::error::{info['wait']['en']}")
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    raw = args.out / "sidex15.download.zip"
    fetch(info["repo"], info["artifact"], raw)
    version = check(raw)
    name = f"5-SUSFS-MODULE-SIDEX15_{version}.zip"
    raw.replace(args.out / name)
    lines = {"SUSFS_MODULE": name, "SUSFS_MODULE_SHA256": hashlib.sha256((args.out / name).read_bytes()).hexdigest(),
             "SUSFS_MODULE_VERSION": version, "SUSFS_MODULE_COMMIT": info.get("commit", ""), "SUSFS_MODULE_RUN": info.get("url", "")}
    text = "".join(f"{key}={value}\n" for key, value in lines.items())
    (args.out / "susfs-sidex15.env").write_text(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

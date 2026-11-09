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


# Audit r17 (9 Nov 2026): sidex15's installer downloads ksu_susfs from GitHub, runs it as root without any
# trusted digest (wget fallback even without TLS checks), skips the install entirely when the hashes match,
# and puts Termux's user-writable bin on the root PATH. Cogan Kernel's copy installs the bundled tool only.
TERMUX_PATH = ":/data/data/com.termux/files/usr/bin"
CLOUD_START = "# Check connectivity first\n"
CLOUD_END = "# cleanup\n"
LOCAL_INSTALL = """# Cogan Kernel: only the ksu_susfs inside this ZIP is installed; nothing is downloaded and run as root.
ui_print "[-] Installing the bundled susfs binary"
cp -f ${TMPDIR}/susfs/tools/ksu_susfs_arm64 ${DEST_BIN_DIR}/ksu_susfs && chmod 755 ${DEST_BIN_DIR}/ksu_susfs \\
\t|| abort "[!] ksu_susfs could not be installed"

"""
NO_ONLINE_UPDATE = """#!/bin/sh
# Cogan Kernel: online update of ksu_susfs is off (it ran an unverified download as root).
echo "[!] Update online ksu_susfs dimatikan di Cogan Kernel; pasang ZIP modul yang lebih baru."
echo "[!] Online ksu_susfs update is off in Cogan Kernel; install a newer module ZIP instead."
exit 1
"""
UPDATERS = ("action.sh", "susfs-bin-update.sh")
# Only reads a hash to show "update available"; it never runs or installs what it downloads.
HASH_ONLY = "susfs-bin-check.sh"


def harden(path):
    """Rewrite the module ZIP so installing or updating never runs a download; SystemExit when sidex15's
    scripts no longer look as expected (check them again, never ship them unpatched)."""
    with zipfile.ZipFile(path) as archive:
        entries = [(info, archive.read(info)) for info in archive.infolist()]
    files = {info.filename: data for info, data in entries}
    text = files["customize.sh"].decode()
    start, end = text.find(CLOUD_START), text.find(CLOUD_END)
    if (text.count(TERMUX_PATH) != 1 or text.count(CLOUD_START) != 1 or text.count(CLOUD_END) != 1
            or not start < end or "raw.githubusercontent.com" not in text[start:end]):
        raise SystemExit("::error::sidex15 module: customize.sh changed, its download step was not found; check it again")
    files["customize.sh"] = (text[:start] + LOCAL_INSTALL + text[end:]).replace(TERMUX_PATH, "").encode()
    for name in UPDATERS:
        if name in files:
            files[name] = NO_ONLINE_UPDATE.encode()
    for name, data in files.items():
        # The download helpers may stay defined; without a web address nothing is fetched.
        if name.endswith(".sh") and name != HASH_ONLY and re.search(rb"https?://", data):
            raise SystemExit(f"::error::sidex15 module: {name} still has a web address; check it again")
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for info, _ in entries:
            out.writestr(info, files[info.filename], compress_type=zipfile.ZIP_DEFLATED)
    tmp.replace(path)


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
    harden(raw)
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

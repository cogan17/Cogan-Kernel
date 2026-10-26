#!/usr/bin/env bash
# The SUSFS module of a Builder run (owner 2026-10-26: "Tambahkan juga untuk SusFS di artifact"):
# simonpunk's own ksu_module_susfs from the very SUSFS commit the kernels of the run were built with,
# made the way his scripts make it: build_ksu_susfs_tool.sh compiles the ksu_susfs tool with the
# Android NDK, build_ksu_module.sh zips the module folder ("zip -r9 ... *", so dotfiles stay out).
# The tool must be a 64-bit ARM program: rothko runs no 32-bit code.
#
# Usage: susfs_module.sh SUSFS_DIR OUT
#   SUSFS_DIR  a checkout of simonpunk/susfs4ksu at the snapshot's commit
#   NDK_BUILD  ndk-build to use (default: the runner's newest NDK, else ndk-build on PATH)
# Writes OUT/5-SUSFS-MODULE_<version>_<commit8>.zip and OUT/susfs-<commit8>.env.
set -euo pipefail

src="$(realpath "$1")"
out="$(mkdir -p "$2" && realpath "$2")"
ndk="${NDK_BUILD:-${ANDROID_NDK_LATEST_HOME:+$ANDROID_NDK_LATEST_HOME/ndk-build}}"
ndk="${ndk:-ndk-build}"
command -v "$ndk" > /dev/null || { echo "::error::ndk-build not found (Android NDK)"; exit 1; }

commit="$(git -C "$src" rev-parse HEAD)"
version="$(sed -n 's/^version=//p' "$src/ksu_module_susfs/module.prop" | tr -d '\r')"
[[ "$version" =~ ^v[0-9][0-9A-Za-z.+-]*$ ]] || { echo "::error::SUSFS module.prop version '$version'"; exit 1; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cp -R "$src/ksu_susfs" "$src/ksu_module_susfs" "$work/"
(cd "$work/ksu_susfs" && rm -rf libs obj && "$ndk")
tool="$work/ksu_susfs/libs/arm64-v8a/ksu_susfs"
python3 - "$tool" <<'PY'
import sys
head = open(sys.argv[1], "rb").read(20)
# ELF, 64-bit, little endian, e_machine 183 (AArch64)
if head[:6] != b"\x7fELF\x02\x01" or int.from_bytes(head[18:20], "little") != 183:
    raise SystemExit("::error::ksu_susfs is not a 64-bit ARM program")
PY
mkdir -p "$work/ksu_module_susfs/tools"
cp "$tool" "$work/ksu_module_susfs/tools/ksu_susfs_arm64"

name="5-SUSFS-MODULE_${version}_${commit:0:8}.zip"
(cd "$work/ksu_module_susfs" && zip -qr9 "$out/$name" -- *)
python3 - "$out/$name" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as archive:
    names = set(archive.namelist())
    need = {"module.prop", "customize.sh", "META-INF/com/google/android/update-binary", "tools/ksu_susfs_arm64"}
    if archive.testzip() or not need <= names:
        raise SystemExit(f"::error::invalid SUSFS module: missing {sorted(need - names)}")
PY
{
  echo "SUSFS_MODULE=$name"
  echo "SUSFS_MODULE_SHA256=$(sha256sum "$out/$name" | cut -d' ' -f1)"
  echo "SUSFS_MODULE_VERSION=$version"
  echo "SUSFS_MODULE_COMMIT=$commit"
} > "$out/susfs-${commit:0:8}.env"
cat "$out/susfs-${commit:0:8}.env"

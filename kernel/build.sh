#!/usr/bin/env bash
# Cogan Kernel for the Xiaomi 14T Pro (rothko): one build from the official ACK android14-6.1 source.
#
# No lock, pin or frozen tree (owner 2026-10-23): every component comes from the run's snapshot of
# the newest versions (kernel/resolve.py). When the newest version does not fit, the build stops
# with OUT/wait.json naming whom to wait for (exit 2); a fault of this repository exits 1. The KMI
# gate against the phone's own stock kernel (6.1.138) and the Xiaomi BSP always runs and fails closed.
#
# Environment:
#   SNAPSHOT     resolve.py JSON of the root (KSUN or BSU)
#   ACK_TAG ACK_COMMIT SUBLEVEL   the ACK release of this job
#   BRAND REVISION RUN_NUMBER LTO(full|thin|none) BUILD_TIME(N or a date)
#   NOMOUNT BBG NETWORKING UNICODE (true|false)   OUT (results)   GH_TOKEN
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SNAPSHOT="$(realpath "$SNAPSHOT")"
WORK="${WORK:-$PWD/work}"
OUT="${OUT:-$PWD/out}"
KSRC="$WORK/kernel"
KOUT="$WORK/kernel-out"
mkdir -p "$WORK" "$OUT"

log() { echo "[+] $*"; }
# The run summary (kernel/run_summary.py) reads where a failed build stopped and why.
group() { echo "::group::$*"; printf '%s\n' "$*" > "$OUT/stage.txt"; }
fail() { echo "::error::$*"; printf '%s\n' "$*" > "$OUT/error.txt"; exit 1; }
# A newer upstream version that does not fit yet: the summary names whom to wait for.
wait_for() {
  python3 -c 'import json, sys; json.dump({"id": sys.argv[1], "en": sys.argv[2]}, open(sys.argv[3], "w"))' \
    "$1" "$2" "$OUT/wait.json"
  echo "::warning::$2"
  exit 2
}
snap() { python3 -c 'import json, sys; d = json.load(open(sys.argv[1]))
for key in sys.argv[2].split("."): d = d[key]
print(d)' "$SNAPSHOT" "$1"; }
apply() {  # strict: the patch applies as it is, or the build stops
  git -C "$KSRC" apply --whitespace=nowarn "$1"
}

ROOT="$(snap root)"
case "$ROOT" in
  KSUN) VARIANT="KernelSU-Next+SuSFS"; ROOT_NAME="KernelSU Next" ;;
  BSU) VARIANT="BakaSU+SuSFS"; ROOT_NAME="BakaSU" ;;
  *) fail "Unknown root $ROOT" ;;
esac
[[ "${BRAND:-Cogan}" =~ ^[A-Za-z0-9_-]{1,12}$ ]] || fail "Kernel Branding: up to 12 letters, digits, _ or -"
REVISION="${REVISION:-r${RUN_NUMBER:-0}}"
[[ "$REVISION" =~ ^r[0-9]+$ ]] || fail "Build Revision: r followed by digits (e.g. r10)"
RELEASE="v$(date -u +%y.%m.%d)-$REVISION"
NAME="${BRAND:-Cogan}-Rothko-ACK"
ROOT_REPO="$(snap root_source.repo)"
ROOT_COMMIT="$(snap root_source.commit)"

group "Toolchain (Neutron clang $(snap neutron.tag))"
mkdir -p "$WORK/clang"
curl -fsSL --retry 3 "$(snap neutron.url)" | tar -I zstd -x -C "$WORK/clang"
export PATH="$WORK/clang/bin:$HOME/.local/bin:$PATH"
# The workflow caches ~/.ccache; newer ccache defaults to ~/.cache/ccache.
export CCACHE_DIR="${CCACHE_DIR:-$HOME/.ccache}"
clang --version | head -n 1
# pahole from its own repository (BTF of the GKI defconfig), as the device-tested builds used.
if [ ! -x "$HOME/.local/bin/pahole" ]; then
  git clone -q --depth=1 https://git.kernel.org/pub/scm/devel/pahole/pahole.git "$WORK/pahole"
  cmake -S "$WORK/pahole" -B "$WORK/pahole/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$HOME/.local" \
    -DCMAKE_INSTALL_RPATH="$HOME/.local/lib" -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON -D__LIB=lib >/dev/null
  make -s -C "$WORK/pahole/build" -j"$(nproc)" install >/dev/null
fi
pahole --version
echo "::endgroup::"

group "Kernel source: ACK $ACK_TAG (6.1.$SUBLEVEL)"
git init -q "$KSRC"
git -C "$KSRC" fetch -q --depth=1 https://android.googlesource.com/kernel/common "$ACK_COMMIT"
git -C "$KSRC" checkout -q FETCH_HEAD
LINUX_VERSION="$(make -s -C "$KSRC" kernelversion)"
[ "$LINUX_VERSION" = "6.1.$SUBLEVEL" ] || fail "$ACK_TAG is $LINUX_VERSION, expected 6.1.$SUBLEVEL"
git -C "$KSRC" -c user.name=Cogan -c user.email=builder@localhost commit -q --allow-empty -m "ACK $ACK_TAG"
echo "::endgroup::"

group "Stock kernel reference of the phone (KMI gate)"
python3 "$HERE/scripts/stock_reference.py" --device rothko "$WORK/stock"
echo "::endgroup::"

group "Vendor module compatibility: module force-load, no protected exports"
apply "$HERE/patches/force-load-modules.patch"
rm -f "$KSRC"/android/*protected_exports*
echo "::endgroup::"

if [ "${NETWORKING:-true}" = "true" ]; then
  group "BBRv3 (default TCP, also bbr3) with the stock KMI layout"
  # The patch set of this sublevel, or of the newest sublevel below it.
  BBR_SUB=""
  for dir in "$HERE"/patches/bbrv3/[0-9]*; do
    sub="$(basename "$dir")"
    if (( sub <= SUBLEVEL )) && { [ -z "$BBR_SUB" ] || (( sub > BBR_SUB )); }; then BBR_SUB="$sub"; fi
  done
  [ -n "$BBR_SUB" ] || fail "No BBRv3 patch for 6.1.$SUBLEVEL"
  BBR_DIR="$HERE/patches/bbrv3/$BBR_SUB"
  log "BBRv3 patches of 6.1.$(basename "$BBR_DIR")"
  apply "$BBR_DIR/bbrv3.patch" || fail "BBRv3 does not fit ACK 6.1.$SUBLEVEL yet: the patch must be adapted in this repository (or untick Networking)"
  apply "$HERE/patches/bbrv3/bbr3-alias.patch" || fail "bbr3 name patch does not fit on top of BBRv3"
  apply "$BBR_DIR/bbrv3-kabi.patch" || fail "BBRv3 stock-KMI patch does not fit ACK 6.1.$SUBLEVEL yet"
  echo "::endgroup::"
fi

if [ "${UNICODE:-false}" = "true" ]; then
  group "Unicode fix (WildKernel) $(snap unicode.commit | cut -c1-12)"
  # Names with ignorable code points (zero-width characters) no longer fold to the same name on
  # casefolded storage. The newest patch of WildKernel's kernel_patches, applied strictly.
  RAW="$(snap unicode.repo | sed 's#^https://github.com/#https://raw.githubusercontent.com/#')"
  curl -fsSL --retry 3 "$RAW/$(snap unicode.commit)/$(snap unicode.path | sed 's/+/%2B/g')" -o "$WORK/unicode-fix.patch"
  apply "$WORK/unicode-fix.patch" \
    || wait_for "Tunggu WildKernel: patch Unicode fix terbaru tidak cocok dengan ACK 6.1.$SUBLEVEL (atau lepas centang Unicode fix)." \
                "Wait for WildKernel: the newest Unicode fix patch does not fit ACK 6.1.$SUBLEVEL (or untick Unicode fix)."
  echo "::endgroup::"
fi

cd "$KSRC"
if [ "${BBG:-true}" = "true" ]; then
  group "Baseband Guard $(snap bbg.commit | cut -c1-12)"
  git clone -q "$(snap bbg.repo)" Baseband-guard
  git -C Baseband-guard checkout -q --detach "$(snap bbg.commit)"
  bash Baseband-guard/setup.sh "$(snap bbg.commit)" || log "BBG setup.sh exited non-zero; checking its results"
  [ -L security/baseband-guard ] && grep -q 'baseband-guard/' security/Makefile \
    || wait_for "Tunggu vc-teahouse: setup Baseband Guard terbaru tidak terpasang di ACK 6.1.$SUBLEVEL." \
                "Wait for vc-teahouse: the newest Baseband Guard setup does not install on ACK 6.1.$SUBLEVEL."
  # Reviewed allow-cache locking fix, unless upstream already carries it.
  if ! git -C Baseband-guard apply -p3 --reverse --check "$HERE/patches/bbg-allow-cache-spinlock.patch" 2>/dev/null; then
    git -C Baseband-guard apply -p3 "$HERE/patches/bbg-allow-cache-spinlock.patch" \
      || wait_for "Tunggu vc-teahouse: perbaikan penguncian Baseband Guard tidak cocok dengan versi terbaru." \
                  "Wait for vc-teahouse: the Baseband Guard locking fix does not fit its newest version."
  fi
  sed -i '/^config LSM$/,/^help$/{ /^[[:space:]]*default/ { /baseband_guard/! s/selinux/selinux,baseband_guard/ } }' security/Kconfig
  echo "::endgroup::"
fi

group "$ROOT_NAME $ROOT_COMMIT"
if [ "$ROOT" = "KSUN" ]; then
  BRANCH="$(snap root_source.branch)"
  curl -fsSL "https://raw.githubusercontent.com/pershoot/KernelSU-Next/$ROOT_COMMIT/kernel/setup.sh" -o "$WORK/root-setup.sh"
  bash "$WORK/root-setup.sh" "$BRANCH"
  # The branch name stays (Kbuild counts KSU_VERSION from its merge-base with origin/dev).
  git -C KernelSU-Next checkout -q -B "$BRANCH" "$ROOT_COMMIT"
  [ "$(git -C KernelSU-Next rev-parse HEAD)" = "$ROOT_COMMIT" ] || fail "KernelSU Next checkout is not $ROOT_COMMIT"
  KSU_VERSION="$(snap root_source.ksu_version)"
else
  curl -fsSL "https://raw.githubusercontent.com/Baka-SU/BakaSU/$ROOT_COMMIT/kernel/setup.sh" -o "$WORK/root-setup.sh"
  bash "$WORK/root-setup.sh" "$(snap root_source.tag)"
  [ "$(git -C KernelSU rev-parse HEAD)" = "$ROOT_COMMIT" ] || fail "BakaSU checkout is not $ROOT_COMMIT"
  KSU_VERSION=""
fi
echo "::endgroup::"

group "SUSFS $(snap susfs.commit | cut -c1-12)"
git clone -q --filter=blob:none -b "$(snap susfs.branch)" "$(snap susfs.repo)" "$WORK/susfs"
git -C "$WORK/susfs" checkout -q "$(snap susfs.commit)"
cp -R "$WORK/susfs/kernel_patches/fs/." fs/
cp -R "$WORK/susfs/kernel_patches/include/linux/." include/linux/
patch -p1 --fuzz=3 --no-backup-if-mismatch < "$WORK/susfs/kernel_patches/50_add_susfs_in_gki-android14-6.1.patch" \
  || wait_for "Tunggu simonpunk memperbarui SUSFS: patch kernel terbaru tidak cocok dengan ACK 6.1.$SUBLEVEL." \
              "Wait for simonpunk to update SUSFS: its newest kernel patch does not fit ACK 6.1.$SUBLEVEL."
SUSFS_VERSION="$(sed -n 's/^#define SUSFS_VERSION "\(.*\)"/\1/p' include/linux/susfs.h)"
echo "::endgroup::"

if [ "${NOMOUNT:-true}" = "true" ]; then
  group "NoMount $(snap nomount.tag)"
  curl -fsSL "https://raw.githubusercontent.com/maxsteeel/nomount/$(snap nomount.commit)/kernel/setup.sh" -o "$WORK/nomount-setup.sh"
  bash "$WORK/nomount-setup.sh" "$(snap nomount.tag)" \
    || wait_for "Tunggu maxsteeel: NoMount $(snap nomount.tag) tidak terpasang di ACK 6.1.$SUBLEVEL." \
                "Wait for maxsteeel: NoMount $(snap nomount.tag) does not install on ACK 6.1.$SUBLEVEL."
  echo "::endgroup::"
fi

group "Cogan Bridge and configuration"
python3 "$HERE/scripts/install_cogan_bridge.py" "$KSRC" --device rothko
DEFCONFIG=arch/arm64/configs/gki_defconfig
{
  echo "CONFIG_KSU=y"
  [ "${BBG:-true}" = "true" ] && echo "CONFIG_BBG=y"
  [ "${NOMOUNT:-true}" = "true" ] && echo "CONFIG_NOMOUNT=y"
  cat "$HERE/configs/susfs.config" "$HERE/configs/compat.config"
  if [ "${NETWORKING:-true}" = "true" ]; then cat "$HERE/configs/custom.config"
  else sed '/^# Networking extras$/,$d' "$HERE/configs/custom.config"; fi
  case "${LTO:-full}" in
    full) printf 'CONFIG_LTO_NONE=n\nCONFIG_LTO_CLANG_FULL=y\n' ;;
    thin) printf 'CONFIG_LTO_NONE=n\nCONFIG_LTO_CLANG_THIN=y\n' ;;
  esac
  echo "CONFIG_RCU_TRACE=n"
  # Last, so it wins: what the phone's vendor modules were built against (IPV6_SUBTREES off, HZ 250).
  cat "$HERE/configs/stock-kmi.config"
} >> "$DEFCONFIG"
scripts/config --file "$DEFCONFIG" --set-str CONFIG_LOCALVERSION "-$NAME-$REVISION-$(git rev-parse --short=9 HEAD)" \
  --disable CONFIG_LOCALVERSION_AUTO
sed -i 's/echo "+"/# echo "+"/g' scripts/setlocalversion
export KBUILD_BUILD_USER=cogan17 KBUILD_BUILD_HOST=github-actions KCFLAGS="-w"
if [ "${BUILD_TIME:-N}" = "N" ]; then
  KBUILD_BUILD_TIMESTAMP="$(LC_ALL=C date -u '+%a %b %d %H:%M:%S UTC %Y')"
else
  KBUILD_BUILD_TIMESTAMP="$(LC_ALL=C date -u -d "$BUILD_TIME" '+%a %b %d %H:%M:%S UTC %Y')" || fail "Invalid Build Time"
fi
export KBUILD_BUILD_TIMESTAMP
MAKE=(make -j"$(nproc)" O="$KOUT" ARCH=arm64 LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu-
      CROSS_COMPILE_COMPAT=arm-linux-gnueabi- CC="ccache clang")
"${MAKE[@]}" gki_defconfig
for line in CONFIG_KSU=y CONFIG_KSU_SUSFS=y CONFIG_KSU_SUSFS_SUS_MAP=y CONFIG_COGAN_BRIDGE=y CONFIG_HZ=250; do
  grep -qx "$line" "$KOUT/.config" || fail "$line missing from the resolved config"
done
! grep -qx 'CONFIG_IPV6_SUBTREES=y' "$KOUT/.config" || fail "CONFIG_IPV6_SUBTREES must stay off (vendor KMI)"
echo "::endgroup::"

group "Building kernel"
"${MAKE[@]}"
echo "::endgroup::"

group "KMI gate: Xiaomi 14T Pro vendor modules"
python3 "$HERE/scripts/kmi_compat.py" --device rothko "$KSRC" "$KOUT" --reference "$HERE/bsp" \
  --stock-reference "$WORK/stock" --json "$OUT/kmi-compat.json" --github-env "$WORK/kmi.env"
KMI_COMPAT="$(sed -n 's/^KMI_COMPAT=//p' "$WORK/kmi.env")"
FEATURES="$(python3 "$HERE/scripts/kernel_features.py" "$KOUT/.config" "$KSRC")"
echo "::endgroup::"

group "AnyKernel3 package"
cd "$WORK"
git clone -q "$(snap anykernel.repo)" anykernel
git -C anykernel checkout -q --detach "$(snap anykernel.commit)"
git -C anykernel fetch -q origin "$(snap anykernel.arm64_tools)"
for tool in $(git -C anykernel ls-tree --name-only FETCH_HEAD); do
  git -C anykernel show "FETCH_HEAD:$tool" > "anykernel/tools/$tool"
  chmod 755 "anykernel/tools/$tool"
done
rm -rf anykernel/.git anykernel/.github anykernel/README.md anykernel/LICENSE anykernel/modules anykernel/patch anykernel/ramdisk
sed -e "s|KERNEL_STRING|$NAME $RELEASE $LINUX_VERSION $VARIANT by Cogan (cogan17)|" -e "s|FEATURES_LINE|$FEATURES|" \
  "$HERE/anykernel/anykernel.sh" > anykernel/anykernel.sh
cp "$KOUT/arch/arm64/boot/Image" anykernel/
ZIP="1-KERNEL_${NAME}-${LINUX_VERSION}_${VARIANT}_${RELEASE}.zip"
(cd anykernel && zip -qr9 "$OUT/$ZIP" . -x '*.zip')
python3 - "$OUT/$ZIP" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as archive:
    names = set(archive.namelist())
    if archive.testzip() or not {"anykernel.sh", "Image", "tools/ak3-core.sh", "tools/magiskboot"} <= names:
        raise SystemExit("invalid AnyKernel3 ZIP")
    # rothko cannot run 32-bit code: every tool must be a 64-bit ARM ELF (e_machine 183).
    for name in sorted(n for n in names if n.startswith("tools/") and not n.endswith((".sh", "/"))):
        head = archive.read(name)[:20]
        if head[:5] != b"\x7fELF\x02" or int.from_bytes(head[18:20], "little") != 183:
            raise SystemExit(f"{name} is not an arm64 binary: rothko runs no 32-bit code")
PY
echo "::endgroup::"

group "Manager and NoMount module"
download_digest() {  # url, file, sha256:digest (from the release API)
  curl -fsSL --retry 3 "$1" -o "$2"
  [ -z "$3" ] || [ "sha256:$(sha256sum "$2" | cut -d' ' -f1)" = "$3" ] || fail "$(basename "$2"): SHA256 differs from its release"
}
if [ "$ROOT" = "KSUN" ]; then
  for kind in manager spoofed; do
    id="$(snap "manager.$kind" 2>/dev/null)" || continue
    curl -fsSL -H "Authorization: Bearer $GH_TOKEN" \
      "https://api.github.com/repos/KernelSU-Next/KernelSU-Next/actions/artifacts/$id/zip" -o "$WORK/$kind.zip"
    apk="$(unzip -Z1 "$WORK/$kind.zip" | grep '\.apk$' | head -n 1)"
    [ -n "$apk" ] || fail "KernelSU Next CI artifact $id has no APK"
    unzip -p "$WORK/$kind.zip" "$apk" > "$WORK/$kind.apk"
    label="$(echo "$apk" | sed -E 's/^KernelSU_Next_//; s/-spoofed//; s/-release\.apk$//; s/\.apk$//')"
    prefix=$([ "$kind" = manager ] && echo 2-MANAGER || echo 3-MANAGER-SPOOFED)
    mv "$WORK/$kind.apk" "$OUT/${prefix}_KernelSU-Next_${label}.apk"
  done
else
  download_digest "$(snap manager.url)" "$OUT/2-MANAGER_BakaSU_$(snap root_source.tag).apk" "$(snap manager.digest)"
fi
if [ "${NOMOUNT:-true}" = "true" ]; then
  download_digest "$(snap nomount.url)" "$OUT/4-NOMOUNT-MODULE_$(snap nomount.tag).zip" "$(snap nomount.digest)"
fi
echo "::endgroup::"

{
  echo "RELEASE=$RELEASE"
  echo "RELEASE_NAME=$NAME $RELEASE"
  echo "LINUX_VERSION=$LINUX_VERSION"
  echo "ACK_TAG=$ACK_TAG"
  echo "VARIANT=$VARIANT"
  echo "ROOT_NAME=$ROOT_NAME"
  echo "ROOT_REPO=$ROOT_REPO"
  echo "ROOT_COMMIT=$ROOT_COMMIT"
  echo "ROOT_TAG=$(snap root_source.tag 2>/dev/null || snap root_source.branch)"
  echo "KSU_VERSION=$KSU_VERSION"
  echo "SUSFS_VERSION=$SUSFS_VERSION"
  echo "SUSFS_COMMIT=$(snap susfs.commit)"
  echo "NOMOUNT=$([ "${NOMOUNT:-true}" = "true" ] && snap nomount.tag || echo -)"
  echo "BBG_COMMIT=$([ "${BBG:-true}" = "true" ] && snap bbg.commit || echo -)"
  echo "UNICODE_FIX=$([ "${UNICODE:-false}" = "true" ] && snap unicode.commit || echo -)"
  echo "ZIP=$ZIP"
  echo "ZIP_SHA256=$(sha256sum "$OUT/$ZIP" | cut -d' ' -f1)"
  echo "NEUTRON=$(snap neutron.tag)"
  echo "FEATURES=$FEATURES"
  echo "KMI_COMPAT=$KMI_COMPAT"
} > "$OUT/build.env"
cat "$OUT/build.env"

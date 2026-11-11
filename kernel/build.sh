#!/usr/bin/env bash
# Cogan Kernel for the Xiaomi 14T Pro (rothko): one build from the official ACK android14-6.1 source.
#
# No lock, pin or frozen tree (owner 2026-10-23): every component comes from the run's snapshot of
# the newest versions (kernel/resolve.py). When the newest version does not fit, the build stops
# with OUT/wait.json naming whom to wait for (exit 2); a fault of this repository exits 1. The KMI
# gate against the phone's own stock kernel (6.1.138) and the Xiaomi BSP always runs and fails closed.
#
# Environment:
#   SNAPSHOT     resolve.py JSON of the root (KSUN, BSU, KSU, SUKI or CSU)
#   ACK_TAG ACK_COMMIT SUBLEVEL   the ACK release of this job
#   BRAND REVISION RUN_NUMBER BUILD_TIME(N or a date)
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
# A transient 5xx on an external git transfer must not kill a whole matrix run (owner 2026-11-11: run
# 42945957032, git.kernel.org 502'd across ~25 parallel jobs). Retry network git like curl's --retry,
# with backoff. git clone removes its partial target on failure, so a retried clone starts clean.
retry() {
  local n=1
  until "$@"; do
    [ "$n" -ge 4 ] && return 1
    log "percobaan git gagal, ulang $n/3 setelah $((n * 5))s: $*"
    sleep $((n * 5))
    n=$((n + 1))
  done
}

ROOT="$(snap root)"
# The SUSFS box (owner 2026-11-02, ticked by default): unticked builds the plain root manager.
SUSFS_ON=true; snap susfs.commit >/dev/null 2>&1 || SUSFS_ON=false
case "$ROOT" in
  KSUN) VARIANT="KernelSU-Next"; ROOT_NAME="KernelSU Next" ;;
  BSU) VARIANT="BakaSU"; ROOT_NAME="BakaSU" ;;
  KSU) VARIANT="KernelSU"; ROOT_NAME="KernelSU" ;;   # official KernelSU (tiann), owner 2026-11-02
  SUKI) VARIANT="SukiSU"; ROOT_NAME="SukiSU" ;;       # SukiSU Ultra, owner 2026-11-02
  CSU) VARIANT="CoganSU"; ROOT_NAME="CoganSU" ;;      # cogan17/CoganSU, owner 2026-11-04
  *) fail "Unknown root $ROOT" ;;
esac
[ "$SUSFS_ON" = true ] && VARIANT="$VARIANT+SuSFS"
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
  retry git clone -q --depth=1 https://git.kernel.org/pub/scm/devel/pahole/pahole.git "$WORK/pahole"
  cmake -S "$WORK/pahole" -B "$WORK/pahole/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$HOME/.local" \
    -DCMAKE_INSTALL_RPATH="$HOME/.local/lib" -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON -D__LIB=lib >/dev/null
  make -s -C "$WORK/pahole/build" -j"$(nproc)" install >/dev/null
fi
pahole --version
echo "::endgroup::"

group "Kernel source: ACK $ACK_TAG (6.1.$SUBLEVEL)"
git init -q "$KSRC"
retry git -C "$KSRC" fetch -q --depth=1 https://android.googlesource.com/kernel/common "$ACK_COMMIT"
git -C "$KSRC" checkout -q FETCH_HEAD
LINUX_VERSION="$(make -s -C "$KSRC" kernelversion)"
[ "$LINUX_VERSION" = "6.1.$SUBLEVEL" ] || fail "$ACK_TAG is $LINUX_VERSION, expected 6.1.$SUBLEVEL"
git -C "$KSRC" -c user.name=Cogan -c user.email=builder@localhost commit -q --allow-empty -m "ACK $ACK_TAG"
echo "::endgroup::"

# CVE-2026-53163 (owner 1 Nov 2026: automatic in every build). The CVE-2026-43499 fix (Linux 6.1.175,
# "rtmutex: Use waiter::task instead of current in remove_waiter()") made remove_waiter() fatal for a
# waiter that was never enqueued: an app can crash the kernel through FUTEX_CMP_REQUEUE_PI. Linux 6.1.177
# fixes it with upstream commit 40a25d59e85b (stable 4afda3a1da02), applied here as it is. Older ACK
# releases lack the CVE-2026-43499 fix and so this bug; a newer one already has the follow-up.
group "CVE-2026-53163: rtmutex remove_waiter (Linux 6.1.177)"
RTMUTEX="$KSRC/kernel/locking/rtmutex.c"
if grep -q 'if (!waiter_task) /\* never enqueued \*/' "$RTMUTEX"; then
  CVE_2026_53163="present"
  log "Already in ACK $ACK_TAG: nothing to apply"
elif grep -q 'struct task_struct \*waiter_task = waiter->task;' "$RTMUTEX"; then
  apply "$HERE/patches/cve-2026-53163-rtmutex.patch" || fail "CVE-2026-53163 fix does not fit ACK 6.1.$SUBLEVEL"
  CVE_2026_53163="applied"
  log "Applied: upstream 40a25d59e85b (Linux 6.1.177)"
else
  CVE_2026_53163="not-needed"
  log "ACK $ACK_TAG has no CVE-2026-43499 fix, so not its remove_waiter() regression: nothing to apply"
fi
echo "::endgroup::"

# Stock vendor hooks (Issue #105). The phone's stock kernel (ACK 2025-06_r11) has two ACK commits that
# add scheduler vendor hooks the vendor modules use; the 2025-06 and 2025-09 release branches got them in
# September 2025, the 2025-07 branch (6.1.141) never did. Applied as they are when missing, strictly;
# a release with only part of them stops the build. The KMI gate below still checks every hook.
group "Stock vendor hooks: cpu_cgroup and reweight_entity (ACK 8148058f689d, 9667c70358a5)"
SCHED_HOOKS="$KSRC/include/trace/hooks/sched.h"
if grep -q 'android_vh_reweight_entity' "$SCHED_HOOKS" && grep -q 'android_vh_sched_move_task' "$SCHED_HOOKS"; then
  STOCK_VENDOR_HOOKS="present"
  log "Already in ACK $ACK_TAG: nothing to apply"
elif grep -q 'android_vh_reweight_entity\|android_vh_sched_move_task\|android_vh_cpu_cgroup_css' "$SCHED_HOOKS"; then
  fail "ACK $ACK_TAG has only part of the stock scheduler vendor hooks"
else
  apply "$HERE/patches/stock-vendor-hooks-sched.patch" || fail "Stock vendor hooks do not fit ACK 6.1.$SUBLEVEL"
  STOCK_VENDOR_HOOKS="applied"
  log "Applied: ACK 8148058f689d and 9667c70358a5 (as in the stock kernel)"
fi
echo "::endgroup::"

# HyperOS OS3.0.302 (owner 2026-11-06: every sublevel for both HyperOS versions). Its stock kernel
# (ACK 0baf70f2581d, 6.1.157) adds vendor hooks, exports and the dynamic task_struct size its vendor
# modules use. 157, 172 and 176 have them; the official ACK commits are cherry-picked for older releases
# in kernel/patches/hyperos302/6.1.N.patch (commit list in each header), applied as they are when all
# are missing. A release with only part of them, or without a patch for its sublevel, stops the build.
group "HyperOS 302 vendor hooks and exports (ACK android14-6.1-2025-12)"
HOS302=0
grep -q 'android_vh_mm_direct_reclaim_start' "$KSRC/include/trace/hooks/mm.h" && HOS302=$((HOS302 + 1))
grep -q 'vendor_data_pad' "$KSRC/init/init_task.c" && HOS302=$((HOS302 + 1))
grep -q 'EXPORT_SYMBOL(__filemap_remove_folio);' "$KSRC/mm/filemap.c" && HOS302=$((HOS302 + 1))
if [ "$HOS302" = 3 ]; then
  HYPEROS302="present"
  log "Already in ACK $ACK_TAG: nothing to apply"
elif [ "$HOS302" != 0 ]; then
  fail "ACK $ACK_TAG has only part of the HyperOS 302 vendor hooks and exports"
else
  [ -f "$HERE/patches/hyperos302/6.1.$SUBLEVEL.patch" ] || fail "No HyperOS 302 patch for 6.1.$SUBLEVEL"
  apply "$HERE/patches/hyperos302/6.1.$SUBLEVEL.patch" || fail "HyperOS 302 patch does not fit ACK $ACK_TAG"
  HYPEROS302="applied"
  log "Applied: kernel/patches/hyperos302/6.1.$SUBLEVEL.patch ($(grep -c '^  [0-9a-f]\{12\} ' "$HERE/patches/hyperos302/6.1.$SUBLEVEL.patch") ACK commits)"
fi
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
  retry git clone -q "$(snap bbg.repo)" Baseband-guard
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
elif [ "$ROOT" = "KSU" ]; then
  # Official KernelSU: a main commit its CI built a manager for (resolve.py); full clone, so its Kbuild
  # counts KSU_VERSION from git like the official manager of that commit.
  curl -fsSL "https://raw.githubusercontent.com/tiann/KernelSU/$ROOT_COMMIT/kernel/setup.sh" -o "$WORK/root-setup.sh"
  bash "$WORK/root-setup.sh" "$ROOT_COMMIT"
  [ "$(git -C KernelSU rev-parse HEAD)" = "$ROOT_COMMIT" ] || fail "KernelSU checkout is not $ROOT_COMMIT"
  KSU_VERSION=""
elif [ "$ROOT" = "CSU" ]; then
  # CoganSU: KernelSU with Cogan's own manager identity (its kernel/cogansu.mk, read by its Kbuild), the
  # commit of the newest CoganSU release, the same as its manager (resolve.py). Folder KernelSU/, so the
  # SUSFS patch for KernelSU applies as it is.
  curl -fsSL "https://raw.githubusercontent.com/cogan17/CoganSU/$ROOT_COMMIT/kernel/setup.sh" -o "$WORK/root-setup.sh"
  bash "$WORK/root-setup.sh" "$ROOT_COMMIT"
  [ "$(git -C KernelSU rev-parse HEAD)" = "$ROOT_COMMIT" ] || fail "CoganSU checkout is not $ROOT_COMMIT"
  KSU_VERSION=""
elif [ "$ROOT" = "SUKI" ]; then
  # SukiSU Ultra: with SUSFS its builtin branch (SUSFS built into the root driver), without SUSFS the
  # newest release's commit (resolve.py). Its setup.sh clones the whole repository, so both are there;
  # its checkout falls back silently, hence the check. KPM stays off (owner 2026-11-02).
  curl -fsSL "https://raw.githubusercontent.com/SukiSU-Ultra/SukiSU-Ultra/$ROOT_COMMIT/kernel/setup.sh" -o "$WORK/root-setup.sh"
  bash "$WORK/root-setup.sh" "$ROOT_COMMIT"
  [ "$(git -C KernelSU rev-parse HEAD)" = "$ROOT_COMMIT" ] || fail "SukiSU checkout is not $ROOT_COMMIT"
  KSU_VERSION=""
else
  curl -fsSL "https://raw.githubusercontent.com/Baka-SU/BakaSU/$ROOT_COMMIT/kernel/setup.sh" -o "$WORK/root-setup.sh"
  bash "$WORK/root-setup.sh" "$ROOT_COMMIT"   # a release tag's commit, or a main commit (resolve.py)
  [ "$(git -C KernelSU rev-parse HEAD)" = "$ROOT_COMMIT" ] || fail "BakaSU checkout is not $ROOT_COMMIT"
  KSU_VERSION=""
fi
echo "::endgroup::"

SUSFS_VERSION="-"
if [ "$SUSFS_ON" = true ]; then
group "SUSFS $(snap susfs.commit | cut -c1-12)"
retry git clone -q --filter=blob:none -b "$(snap susfs.branch)" "$(snap susfs.repo)" "$WORK/susfs"
git -C "$WORK/susfs" checkout -q "$(snap susfs.commit)"
cp -R "$WORK/susfs/kernel_patches/fs/." fs/
cp -R "$WORK/susfs/kernel_patches/include/linux/." include/linux/
# Older ACK releases lack a few lines the patch only uses as context (kernel/scripts/susfs_context.py,
# owner 2026-10-24); what SUSFS adds stays as simonpunk wrote it.
notes="$(python3 "$HERE/scripts/susfs_context.py" "$WORK/susfs/kernel_patches/50_add_susfs_in_gki-android14-6.1.patch" . \
  2>&1 > "$WORK/susfs.patch")" || fail "kernel/scripts/susfs_context.py: $notes"
[ -z "$notes" ] || echo "::notice::$notes"
patch -p1 --fuzz=3 --no-backup-if-mismatch < "$WORK/susfs.patch" \
  || wait_for "Tunggu simonpunk memperbarui SUSFS: patch kernel terbaru tidak cocok dengan ACK 6.1.$SUBLEVEL." \
              "Wait for simonpunk to update SUSFS: its newest kernel patch does not fit ACK 6.1.$SUBLEVEL."
if [ "$ROOT" = "KSU" ] || [ "$ROOT" = "CSU" ]; then
  # Official KernelSU (and CoganSU, built on it) takes SUSFS through simonpunk's own patch for it, as it is.
  git -C KernelSU apply --whitespace=nowarn "$WORK/susfs/kernel_patches/KernelSU/10_enable_susfs_for_ksu.patch" \
    || wait_for "Tunggu simonpunk menyesuaikan SUSFS dengan $ROOT_NAME $(echo "$ROOT_COMMIT" | cut -c1-12)." \
                "Wait for simonpunk to adapt SUSFS to $ROOT_NAME $(echo "$ROOT_COMMIT" | cut -c1-12)."
fi
SUSFS_VERSION="$(sed -n 's/^#define SUSFS_VERSION "\(.*\)"/\1/p' include/linux/susfs.h)"
echo "::endgroup::"
fi

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
  [ "$ROOT" = "SUKI" ] && echo "# CONFIG_KPM is not set"
  [ "${BBG:-true}" = "true" ] && echo "CONFIG_BBG=y"
  [ "${NOMOUNT:-true}" = "true" ] && echo "CONFIG_NOMOUNT=y"
  # SUSFS box unticked: KernelSU Next's Kconfig defaults KSU_SUSFS to y, so turn it off explicitly; its
  # Kbuild then builds the plain (kprobes) hooks instead of the SUSFS ones.
  if [ "$SUSFS_ON" = true ]; then cat "$HERE/configs/susfs.config"; else echo "# CONFIG_KSU_SUSFS is not set"; fi
  cat "$HERE/configs/compat.config"
  if [ "${NETWORKING:-true}" = "true" ]; then cat "$HERE/configs/custom.config"
  else sed '/^# Networking extras$/,$d' "$HERE/configs/custom.config"; fi
  # No LTO, like the phone's stock kernel (HyperOS 302 IKCONFIG: CONFIG_LTO_NONE=y, CFI and SCS on).
  # Thin and Full LTO were removed from the Builder (owner 2026-11-07).
  echo "CONFIG_LTO_NONE=y"
  echo "CONFIG_RCU_TRACE=n"
  cat "$HERE/configs/hardening.config"
  # Last, so it wins: what the phone's vendor modules were built against (IPV6_SUBTREES off, HZ 250).
  cat "$HERE/configs/stock-kmi.config"
} >> "$DEFCONFIG"
# Kernel identity (owner 2026-11-01). Disguise off: the Cogan name. Disguise on: what the phone's own
# stock kernel shows (configs/stock-identity.env, read from the owner's stock boot.img): the GKI release
# format 6.1.N-android14-<gen>-g<ACK commit>-ab<num>, build-user@build-host and Google's Android clang/LLD
# text. Display only: the compiled code does not change, so the KMI gate is unaffected. The version
# stays the real 6.1.N, so Cogan Bridge and the Cogan Smart module keep working; the Cogan brand and
# revision stay in the ZIP name and build.env. Behaviour-based detectors are unaffected.
CC_TEXT=""
if [ "${DISGUISE:-false}" = "true" ]; then
  . "$HERE/configs/stock-identity.env"
  GEN="$(sed -n 's/^KMI_GENERATION=//p' build.config.common 2>/dev/null || true)"; GEN="${GEN:-11}"
  ACK_ID="${ACK_COMMIT:-$(git rev-parse HEAD^)}"  # the real ACK commit, as in a Google GKI build
  LOCALVERSION="-android14-$GEN-g${ACK_ID:0:12}-ab$(printf '%08d' "$(( 0x${ACK_ID:0:7} % 100000000 ))")"
  BUILD_USER="$STOCK_BUILD_USER"; BUILD_HOST="$STOCK_BUILD_HOST"; CC_TEXT="$STOCK_CC_TEXT"
  # The ", LLD x" part of /proc/version comes from scripts/mkcompile_h running "$LD -v": let it take
  # the stock text instead; strict, the build stops if mkcompile_h is not the expected 6.1 script.
  grep -q '^LD_VERSION=$(LC_ALL=C $LD -v' scripts/mkcompile_h || fail "Disguise: unexpected scripts/mkcompile_h"
  sed -i '/^cat <<EOF$/i [ -z "$KBUILD_LD_VERSION_TEXT" ] || LD_VERSION=$KBUILD_LD_VERSION_TEXT' scripts/mkcompile_h
  grep -q '^\[ -z "$KBUILD_LD_VERSION_TEXT" \] || LD_VERSION=$KBUILD_LD_VERSION_TEXT$' scripts/mkcompile_h \
    || fail "Disguise: LLD text hook not added to scripts/mkcompile_h"
  export KBUILD_LD_VERSION_TEXT="$STOCK_LD_TEXT"
  log "Disguised identity: 6.1.$SUBLEVEL$LOCALVERSION ($BUILD_USER@$BUILD_HOST)"
else
  LOCALVERSION="-$NAME-$REVISION-$(git rev-parse --short=9 HEAD)"
  BUILD_USER="cogan17"; BUILD_HOST="github-actions"
fi
scripts/config --file "$DEFCONFIG" --set-str CONFIG_LOCALVERSION "$LOCALVERSION" \
  --disable CONFIG_LOCALVERSION_AUTO
sed -i 's/echo "+"/# echo "+"/g' scripts/setlocalversion
export KBUILD_BUILD_USER="$BUILD_USER" KBUILD_BUILD_HOST="$BUILD_HOST" KCFLAGS="-w"
if [ "${BUILD_TIME:-N}" = "N" ]; then
  KBUILD_BUILD_TIMESTAMP="$(LC_ALL=C date -u '+%a %b %d %H:%M:%S UTC %Y')"
else
  KBUILD_BUILD_TIMESTAMP="$(LC_ALL=C date -u -d "$BUILD_TIME" '+%a %b %d %H:%M:%S UTC %Y')" || fail "Invalid Build Time"
fi
export KBUILD_BUILD_TIMESTAMP
MAKE=(make -j"$(nproc)" O="$KOUT" ARCH=arm64 LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu-
      CROSS_COMPILE_COMPAT=arm-linux-gnueabi- CC="ccache clang")
# Disguise: the /proc/version compiler string (CONFIG_CC_VERSION_TEXT). Overriding the make variable
# wins over its Kconfig default, so olddefconfig does not reset it back to the real clang.
[ -z "$CC_TEXT" ] || MAKE+=(CC_VERSION_TEXT="$CC_TEXT")
"${MAKE[@]}" gki_defconfig
required=(CONFIG_KSU=y CONFIG_COGAN_BRIDGE=y CONFIG_HZ=250 CONFIG_SECURITY_DMESG_RESTRICT=y CONFIG_LTO_NONE=y CONFIG_CFI_CLANG=y)
[ "$SUSFS_ON" = true ] && required+=(CONFIG_KSU_SUSFS=y CONFIG_KSU_SUSFS_SUS_MAP=y)
for line in "${required[@]}"; do
  grep -qx "$line" "$KOUT/.config" || fail "$line missing from the resolved config"
done
[ "$SUSFS_ON" = true ] || ! grep -qx 'CONFIG_KSU_SUSFS=y' "$KOUT/.config" || fail "SUSFS unticked but CONFIG_KSU_SUSFS=y"
! grep -q '^CONFIG_LTO_CLANG' "$KOUT/.config" || fail "LTO must stay off, like the stock kernel (owner 2026-11-07)"
! grep -qx 'CONFIG_KPM=y' "$KOUT/.config" || fail "CONFIG_KPM must stay off (owner 2026-11-02)"
! grep -qx 'CONFIG_IPV6_SUBTREES=y' "$KOUT/.config" || fail "CONFIG_IPV6_SUBTREES must stay off (vendor KMI)"
echo "::endgroup::"

group "Building kernel"
"${MAKE[@]}"
echo "::endgroup::"

group "KMI gate: Xiaomi 14T Pro vendor modules"
STOCK_REFS=()
for stock in "$WORK"/stock/*/; do STOCK_REFS+=(--stock-reference "$stock"); done
python3 "$HERE/scripts/kmi_compat.py" --device rothko "$KSRC" "$KOUT" --reference "$HERE/bsp" \
  "${STOCK_REFS[@]}" --json "$OUT/kmi-compat.json" --github-env "$WORK/kmi.env"
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
if [ "$ROOT" = "SUKI" ]; then
  # The newest SukiSU release's manager (with SUSFS the kernel is its builtin branch, which has none).
  download_digest "$(snap manager.url)" "$OUT/2-MANAGER_SukiSU_$(snap manager.tag).apk" "$(snap manager.digest)"
elif [ "$ROOT" = "CSU" ]; then
  # The CoganSU release the kernel comes from: same commit, same manager identity.
  download_digest "$(snap manager.url)" "$OUT/2-MANAGER_CoganSU_$(snap manager.tag).apk" "$(snap manager.digest)"
elif [ "$(snap manager.kind)" = "release" ]; then
  download_digest "$(snap manager.url)" "$OUT/2-MANAGER_BakaSU_$(snap root_source.tag).apk" "$(snap manager.digest)"
else
  # The official CI build of the kernel's own commit: KernelSU Next, BakaSU main or KernelSU main.
  for kind in manager spoofed; do
    id="$(snap "manager.$kind" 2>/dev/null)" || continue
    curl -fsSL -H "Authorization: Bearer $GH_TOKEN" \
      "https://api.github.com/repos/$(snap manager.repo)/actions/artifacts/$id/zip" -o "$WORK/$kind.zip"
    apk="$(unzip -Z1 "$WORK/$kind.zip" | grep '\.apk$' | head -n 1)"
    [ -n "$apk" ] || fail "$ROOT_NAME CI artifact $id has no APK"
    unzip -p "$WORK/$kind.zip" "$apk" > "$WORK/$kind.apk"
    prefix=$([ "$kind" = manager ] && echo 2-MANAGER || echo 3-MANAGER-SPOOFED)
    if [ "$ROOT" = "KSUN" ]; then
      label="$(echo "$apk" | sed -E 's/^KernelSU_Next_//; s/-spoofed//; s/-release\.apk$//; s/\.apk$//')"
      mv "$WORK/$kind.apk" "$OUT/${prefix}_KernelSU-Next_${label}.apk"
    elif [ "$ROOT" = "KSU" ]; then
      mv "$WORK/$kind.apk" "$OUT/${prefix}_KernelSU_main-$(echo "$ROOT_COMMIT" | cut -c1-8).apk"
    else
      mv "$WORK/$kind.apk" "$OUT/${prefix}_BakaSU_main-$(echo "$ROOT_COMMIT" | cut -c1-8).apk"
    fi
  done
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
  echo "SUSFS_COMMIT=$([ "$SUSFS_ON" = true ] && snap susfs.commit || echo -)"
  echo "NOMOUNT=$([ "${NOMOUNT:-true}" = "true" ] && snap nomount.tag || echo -)"
  echo "BBG_COMMIT=$([ "${BBG:-true}" = "true" ] && snap bbg.commit || echo -)"
  echo "CVE_2026_53163=$CVE_2026_53163"
  echo "STOCK_VENDOR_HOOKS=$STOCK_VENDOR_HOOKS"
  echo "HYPEROS302=$HYPEROS302"
  # Pilih sumber (owner 2026-11-06): newest, or stable = the components of the last good build #SOURCE_RUN.
  echo "SOURCE=$(snap source.kind 2>/dev/null || echo newest)"
  echo "SOURCE_RUN=$(snap source.run 2>/dev/null || echo -)"
  echo "DISGUISE=$([ "${DISGUISE:-false}" = "true" ] && echo on || echo off)"
  echo "UNICODE_FIX=$([ "${UNICODE:-false}" = "true" ] && snap unicode.commit || echo -)"
  echo "ZIP=$ZIP"
  echo "ZIP_SHA256=$(sha256sum "$OUT/$ZIP" | cut -d' ' -f1)"
  echo "NEUTRON=$(snap neutron.tag)"
  echo "FEATURES=$FEATURES"
  echo "KMI_COMPAT=$KMI_COMPAT"
} > "$OUT/build.env"
cat "$OUT/build.env"

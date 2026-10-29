#!/system/bin/sh
# Cogan Smart · Aplikasi: what user apps do, a whitelist, removal down to the roots, and the APK block
# for chat and social apps (owner 2026-10-29). Output is JSON. Risk marks are guesses from where an app
# came from and what it may do; the WebUI shows the reasons.
#
#   report.sh scan              user apps of the current Android user with source, rights, access, data, battery
#   report.sh trust PKG | untrust PKG
#   report.sh remove PKG        device admin off, force stop, uninstall for every user, leftovers and the APK copies
#   report.sh block on|off      chat and social apps may (not) install APKs
#   report.sh boot              (service.sh) start the block loop once Android has booted
#   report.sh stop              (uninstall.sh) stop the block loop
if [ "$1" = --lang ]; then shift 2; fi
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
. "$MODDIR/common.sh"
export LC_ALL=C

fail() { printf '{"ok":0,"error":'; json_string "$1"; printf '}\n'; exit 0; }
valid_pkg() { printf '%s\n' "$1" | grep -Eq '^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$' && [ ${#1} -le 200 ]; }
is_trusted() { grep -q -s -x -F "$1" "$CA_DATA/trusted"; }
drop_line() { [ -f "$1" ] || return 0; grep -v -x -F "$2" "$1" > "$1.tmp"; mv -f "$1.tmp" "$1"; }
user_id() {
  CA_USER=$(am get-current-user 2>/dev/null)
  uint "$CA_USER" && [ "$CA_USER" -le 99999 ] || fail 'Pengguna Android tidak dapat dibaca.'
}
user_app() { pm list packages -3 --user "$CA_USER" 2>/dev/null | grep -Fxq "package:$1"; }
# The root manager app that opened this WebUI runs our shell, so it is an ancestor; its package may be
# renamed (owner 2026-10-24: a spoofed manager), so it is found by uid, not by name.
host_uid() {
  ca_pid=$$
  while uint "$ca_pid" && [ "$ca_pid" -gt 1 ]; do
    ca_uid=$(awk '/^Uid:/ {print $2; exit}' "${CB_PID_PROC:-/proc}/$ca_pid/status" 2>/dev/null)
    uint "$ca_uid" && [ "$ca_uid" -ge 10000 ] && { echo "$ca_uid"; return; }
    ca_pid=$(awk '/^PPid:/ {print $2; exit}' "${CB_PID_PROC:-/proc}/$ca_pid/status" 2>/dev/null)
  done
  echo 0
}
ROOT_MANAGERS=' me.weishu.kernelsu com.rifsxd.ksunext com.sukisu.ultra com.topjohnwu.magisk io.github.vvb2060.magisk io.github.huskydg.magisk me.bmax.apatch '
app_id() { dumpsys package "$1" 2>/dev/null | sed -n -E 's/^ *(appId|userId)=([0-9]+).*/\2/p' | head -n 1; }
protected() {   # protected PKG: refuse with a reason when it must stay
  case $ROOT_MANAGERS in *" $1 "*) fail 'Aplikasi root manager tidak dihapus dari sini.' ;; esac
  ca_host=$(host_uid)
  [ "$ca_host" -gt 0 ] && [ "$(app_id "$1")" = $((ca_host % 100000)) ] && fail 'Ini aplikasi root manager yang membuka WebUI; tidak dihapus.'
  is_trusted "$1" && fail 'Aplikasi ada di whitelist; lepaskan dulu.'
}

PROBLEM="DUMP TIMEOUT|^[[:space:]]*(Permission Denial|Permission denied|Security exception|java[.]lang[.]SecurityException|Can't find service|Error dumping service)"
scan_fail() {
  ca_detail=$(head -c 240 "$ca_tmp/error"); [ -n "$ca_detail" ] || ca_detail=$(head -c 240 "$ca_tmp/$1")
  [ -n "$ca_detail" ] || ca_detail='respons kosong'
  fail "Pemindaian gagal pada $2: $(printf '%s' "$ca_detail" | tr '\r\n' '  ')"
}
read_must() {   # FILE LABEL LIMIT CMD...: no partial dump is ever parsed
  ca_f=$1; ca_l=$2; ca_t=$3; shift 3
  timeout "$ca_t" "$@" > "$ca_tmp/$ca_f" 2> "$ca_tmp/error" || scan_fail "$ca_f" "$ca_l"
  grep -Eiq -m 1 "$PROBLEM" "$ca_tmp/$ca_f" "$ca_tmp/error" && scan_fail "$ca_f" "$ca_l"
  [ -s "$ca_tmp/$ca_f" ] || scan_fail "$ca_f" "$ca_l"
}
read_may() {    # the same, but a failed read only leaves that column empty and named in "missing"
  ca_f=$1; ca_l=$2; ca_t=$3; shift 3
  if timeout "$ca_t" "$@" > "$ca_tmp/$ca_f" 2> "$ca_tmp/error" && [ -s "$ca_tmp/$ca_f" ] &&
     ! grep -Eiq -m 1 "$PROBLEM" "$ca_tmp/$ca_f" "$ca_tmp/error"; then return 0; fi
  : > "$ca_tmp/$ca_f"; ca_missing="$ca_missing $ca_l"
}

scan() {
  user_id
  command -v timeout > /dev/null 2>&1 || fail 'Pemindaian memerlukan perintah timeout.'
  mkdir -p "$CA_DATA" && ca_tmp=$(mktemp -d "$CA_DATA/scan.XXXXXX") || fail 'Gagal menyiapkan pemindaian.'
  trap 'rm -rf "$ca_tmp"; lock_drop "$CA_DATA/api.lock"' EXIT
  ca_missing=''
  read_must list 'daftar aplikasi' 15 pm list packages -3 --user "$CA_USER"
  read_must packages 'data paket' 25 dumpsys -t 20 package packages
  read_may usage pemakaian 25 dumpsys -t 20 usagestats -c
  read_may appops akses 25 dumpsys -t 20 appops
  read_may admins admin 15 dumpsys -t 10 device_policy
  read_may launcher ikon 15 cmd package query-activities --components --user "$CA_USER" -a android.intent.action.MAIN -c android.intent.category.LAUNCHER
  read_may battery baterai 30 dumpsys -t 25 batterystats --usage
  read_may net internet 30 dumpsys -t 25 netstats --uid --full
  ca_ps=ps; [ ! -x /system/bin/ps ] || ca_ps=/system/bin/ps
  read_may running proses 10 "$ca_ps" -A -w -o args
  { settings --user "$CA_USER" get secure enabled_accessibility_services; } > "$ca_tmp/a11y" 2> /dev/null || : > "$ca_tmp/a11y"
  { settings --user "$CA_USER" get secure enabled_notification_listeners; } > "$ca_tmp/notif" 2> /dev/null || : > "$ca_tmp/notif"
  cp "$CA_DATA/trusted" "$ca_tmp/trusted" 2> /dev/null || : > "$ca_tmp/trusted"
  cp "$CA_DATA/blocked.log" "$ca_tmp/events" 2> /dev/null || : > "$ca_tmp/events"
  # PackageManager dates use Android's timezone; standalone BusyBox must use the same one.
  ca_tz=$(getprop persist.sys.timezone 2> /dev/null)
  case "$ca_tz" in ''|*[!A-Za-z0-9_+./-]*) ;; *) TZ=$ca_tz; export TZ ;; esac
  load_config
  ca_running=0; block_pid > /dev/null && ca_running=1
  cd "$ca_tmp" && awk -v user="$CA_USER" -v now="$(date +%s)" -v host="$(host_uid)" -v managers="$ROOT_MANAGERS" \
    -v sources="$CA_SOURCES" -v missing="$ca_missing" -v block="$BLOCK" -v block_running="$ca_running" \
    -f "$MODDIR/apps.awk" list packages usage appops admins launcher battery net running a11y notif trusted events
}

remove_app() {
  user_id
  valid_pkg "$1" || fail 'Nama aplikasi tidak valid.'
  user_app "$1" || fail 'Aplikasi user tidak ditemukan.'
  protected "$1"
  # The APK as installed, to find the same file where it was downloaded or received.
  ca_apk=$(pm path --user "$CA_USER" "$1" 2> /dev/null | sed -n 's/^package://p' | grep '/base[.]apk$' | head -n 1)
  ca_size=$(wc -c < "$CA_ROOT$ca_apk" 2> /dev/null | tr -d ' '); ca_sum=''
  uint "$ca_size" && [ "$ca_size" -gt 0 ] && ca_sum=$(sha256sum "$CA_ROOT$ca_apk" 2> /dev/null | cut -c1-64)
  # A device admin cannot be uninstalled, and "dpm remove-active-admin" only removes test admins.
  # Disabling its receiver makes Android drop the admin itself (DevicePolicyManagerService.handlePackagesChanged).
  ca_admins=$(dumpsys device_policy 2> /dev/null | awk -v p="$1/" '
    /Enabled Device Admins \(User [0-9]+/ { u = $0; sub(/.*\(User /, "", u); sub(/[^0-9].*/, "", u) }
    { s = $0; sub(/^ +/, "", s) } index(s, p) == 1 && s ~ /:$/ && u != "" { sub(/:$/, "", s); print u " " s }')
  ca_n_admin=0
  if [ -n "$ca_admins" ]; then
    printf '%s\n' "$ca_admins" | while read -r ca_u ca_c; do pm disable --user "$ca_u" "$ca_c" > /dev/null 2>&1; done
    ca_n_admin=$(printf '%s\n' "$ca_admins" | wc -l | tr -d ' ')
    ca_i=0
    while dumpsys device_policy 2> /dev/null | grep -Fq " $1/"; do
      ca_i=$((ca_i + 1)); [ "$ca_i" -le 15 ] || fail 'Admin perangkat aplikasi ini belum terlepas; aplikasi belum dihapus.'
      sleep 1
    done
  fi
  am force-stop --user all "$1" > /dev/null 2>&1
  ca_out=$(pm uninstall "$1" 2>&1)
  case $ca_out in *Success*) ;; *) fail "Android menolak menghapus: $(printf '%s' "$ca_out" | head -c 200 | tr '\r\n' '  ')" ;; esac
  pm list packages 2> /dev/null | grep -Fxq "package:$1" && fail 'Aplikasi masih terpasang di pengguna lain.'
  # Leftovers Android may keep, only now that the package is gone for every user.
  ca_left=0
  for ca_d in "$CA_ROOT"/data/data/"$1" "$CA_ROOT"/data/user/*/"$1" "$CA_ROOT"/data/user_de/*/"$1" \
      "$CA_ROOT"/data/media/*/Android/data/"$1" "$CA_ROOT"/data/media/*/Android/obb/"$1" "$CA_ROOT"/data/media/*/Android/media/"$1" \
      "$CA_ROOT"/data/misc/profiles/cur/*/"$1" "$CA_ROOT"/data/misc/profiles/ref/"$1" "$CA_ROOT"/data/app/*/"$1"-* "$CA_ROOT"/data/app/"$1"-*; do
    [ -e "$ca_d" ] || [ -L "$ca_d" ] || continue
    rm -rf "$ca_d" && ca_left=$((ca_left + 1))
  done
  # Copies of the same APK (byte for byte) in shared storage: WhatsApp and Telegram downloads, Download, ...
  ca_apks=''
  if [ -n "$ca_sum" ]; then
    find "$CA_ROOT"/data/media -xdev -type f -iname '*.apk' -size "${ca_size}c" > "$CA_RUN/apks" 2> /dev/null
    while IFS= read -r ca_f; do
      [ "$(sha256sum "$ca_f" 2> /dev/null | cut -c1-64)" = "$ca_sum" ] || continue
      rm -f "$ca_f" && { ca_apks="$ca_apks${ca_apks:+,}"; ca_apks="$ca_apks$(json_string "${ca_f#"$CA_ROOT"/data/media/}")"; }
    done < "$CA_RUN/apks"
    rm -f "$CA_RUN/apks"
  fi
  # Accessibility and notification access entries Android may leave behind.
  ca_set=0
  for ca_u in $(users); do
    for ca_k in enabled_accessibility_services enabled_notification_listeners; do
      ca_v=$(settings --user "$ca_u" get secure "$ca_k" 2> /dev/null)
      case ":$ca_v" in *":$1/"*) ;; *) continue ;; esac
      ca_new=$(printf '%s' "$ca_v" | awk -v p="$1/" 'BEGIN { RS = ":" } index($0, p) != 1 && $0 != "" { printf "%s%s", n++ ? ":" : "", $0 }')
      settings --user "$ca_u" put secure "$ca_k" "$ca_new" > /dev/null 2>&1 && ca_set=$((ca_set + 1))
    done
  done
  printf '{"ok":1,"admins":%d,"leftovers":%d,"settings":%d,"apks":[%s]}\n' "$ca_n_admin" "$ca_left" "$ca_set" "$ca_apks"
}

start_block() {
  block_pid > /dev/null && return 0
  if command -v setsid > /dev/null 2>&1; then setsid sh "$MODDIR/block.sh" < /dev/null > /dev/null 2>&1 &
  else nohup sh "$MODDIR/block.sh" < /dev/null > /dev/null 2>&1 & fi
}
stop_block() { ca_p=$(block_pid) && kill "$ca_p" 2> /dev/null; rm -f "$CA_RUN/block.pid"; }

case $1 in
  boot)
    until [ "$(getprop sys.boot_completed)" = 1 ]; do sleep 5; done
    load_config
    if [ "$BLOCK" = 1 ]; then block_pass; start_block; fi
    exit 0 ;;
  stop) stop_block; exit 0 ;;
esac
umask 077
mkdir -p "$CA_RUN" || fail 'Gagal menyiapkan tab Aplikasi.'
lock_take "$CA_DATA/api.lock" || fail 'Perintah lain sedang berjalan'
trap 'lock_drop "$CA_DATA/api.lock"' EXIT
case $1 in
  scan) scan ;;
  trust)
    valid_pkg "$2" || fail 'Nama aplikasi tidak valid.'
    is_trusted "$2" || echo "$2" >> "$CA_DATA/trusted" || fail 'Gagal menyimpan whitelist.'
    printf '{"ok":1}\n' ;;
  untrust)
    valid_pkg "$2" || fail 'Nama aplikasi tidak valid.'
    drop_line "$CA_DATA/trusted" "$2"; printf '{"ok":1}\n' ;;
  remove) remove_app "$2" ;;
  block)
    case $2 in on) ca_b=1 ;; off) ca_b=0 ;; *) fail 'Pilihan tidak valid.' ;; esac
    printf 'BLOCK=%s\n' "$ca_b" > "$CA_DATA/config.tmp" && mv -f "$CA_DATA/config.tmp" "$CA_DATA/config" || fail 'Gagal menyimpan setelan.'
    if [ "$ca_b" = 1 ]; then block_pass; start_block; else stop_block; fi
    printf '{"ok":1,"block":%s}\n' "$ca_b" ;;
  *) fail 'Perintah tidak dikenal' ;;
esac

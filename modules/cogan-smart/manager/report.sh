#!/system/bin/sh
# On-demand Manager controls. No extra worker, swapoff, ZRAM reset or thermal override.
CS_LANG=id
if [ "$1" = --lang ]; then [ "$2" = en ] && CS_LANG=en; shift 2; fi
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
MODROOT=$(cd "$MODDIR/.." && pwd)
CM_SYS=${CM_SYS:-${CP_SYS:-/sys}}
CM_PROC=${CM_PROC:-${CP_PROC:-/proc}}
CM_DATA=${CM_DATA:-${CS_ADB:-/data/adb}/cogan_smart/manager}
CB_SYS=$CM_SYS; CB_PROC=$CM_PROC
. "$MODROOT/bridge.sh"
CPU=default; RAM=default; BOOT=0; BW=default
if [ -f "$CM_DATA/config" ]; then
  while IFS='=' read -r k v; do
    case "$k:$v" in CPU:default|CPU:sugov_ext|CPU:schedutil) CPU=$v ;;
      RAM:default|RAM:snappy|RAM:heavy) RAM=$v ;; BOOT:0|BOOT:1) BOOT=$v ;;
      BW:default|BW:bw_hwmon) BW=$v ;; esac
  done < "$CM_DATA/config"
fi
fail() { printf '{"ok":0,"error":'; json_string "$1"; printf '}\n'; exit 0; }
valid_settings() {
  [ $# = 3 ] || [ $# = 4 ] || return 1
  case "$1" in default|sugov_ext|schedutil) ;; *) return 1 ;; esac
  case "$2" in default|snappy|heavy) ;; *) return 1 ;; esac
  case "$3" in 0|1) ;; *) return 1 ;; esac
  [ $# = 3 ] || case "$4" in default|bw_hwmon) ;; *) return 1 ;; esac
}
save_config() {
  (umask 077; printf 'CPU=%s\nRAM=%s\nBOOT=%s\nBW=%s\n' "$CPU" "$RAM" "$BOOT" "$BW" > "$CM_DATA/config.tmp" &&
    mv "$CM_DATA/config.tmp" "$CM_DATA/config")
}
contains() { case " $1 " in *" $2 "*) return 0 ;; *) return 1 ;; esac; }
compressor() { case "$RAM" in snappy) echo lz4 ;; heavy) echo zstd ;; esac; }
. "$MODDIR/init.sh"
selected() {
  cm_val=$(read_node "$1")
  case "$cm_val" in *'['*']'*) cm_val=${cm_val#*[}; cm_val=${cm_val%%]*} ;; esac
  printf '%s' "$cm_val"
}
gate() {
  # Cogan Bridge exports the DT compatible string, e.g. "mediatek,MT6989".
  cm_soc=$(read_node "$CB_ROOT/soc" | tr 'A-Z' 'a-z')
  case "$cm_soc" in mt6989|mediatek,mt6989) ;; *) return 1 ;; esac
  [ "$(getprop ro.product.device 2>/dev/null)" = rothko ] &&
  [ "$(getprop ro.board.platform 2>/dev/null)" = mt6989 ] &&
  bridge_available && [ "$(read_node "$CB_ROOT/device")" = rothko ]
}
boot_session() {
  cm_boot=$(read_node "$CM_PROC/sys/kernel/random/boot_id")
  [ -n "$cm_boot" ] || return 1
  mkdir -p "$CM_DATA/run"
  if [ "$(read_node "$CM_DATA/run/boot")" != "$cm_boot" ]; then
    rm -f "$CM_DATA/run/owned.tsv" "$CM_DATA/run/restore_pending" "$CM_DATA/run/ram_boot_attempted"
    printf '%s\n' "$cm_boot" > "$CM_DATA/run/boot"
  fi
}
# available_governors is a global list on devfreq, not proof of a DRAM target.
# Identify the rothko memory driver first; UFS and GPU must never be RAM targets.
dram_nodes() {
  for cm_d in "$CM_SYS"/class/devfreq/*; do
    [ "$(readlink -f "$cm_d/device/driver" 2>/dev/null)" = "$CM_SYS/bus/platform/drivers/mtk-dvfsrc-devfreq" ] &&
      printf '%s\n' "$cm_d"
  done
}
bw_nodes() {
  for cm_d in $(dram_nodes); do
    contains "$(read_node "$cm_d/available_governors")" bw_hwmon &&
      [ -w "$cm_d/governor" ] && printf '%s\n' "$cm_d/governor"
  done
}
safe_node() {
  case "$1" in *..*|/*|*[!A-Za-z0-9_/:.,@-]*) return 1 ;; esac
  case "$1" in devices/system/cpu/cpufreq/policy*/scaling_governor|class/devfreq/*/governor|block/zram*/comp_algorithm) ;;
    *) return 1 ;; esac
  case "$(readlink -f "$CM_SYS/$1" 2>/dev/null)" in "$CM_SYS"/*) return 0 ;; esac
  return 1
}
# Journal original, last accepted and pending values BEFORE writing, so an interrupted write
# can still be restored. A value changed by another app is left with that app.
put_node() {
  cm_rel=${1#"$CM_SYS/"}; cm_want=$2
  safe_node "$cm_rel" || return 1
  cm_now=$(selected "$1"); [ -n "$cm_now" ] || return 1
  [ "$cm_now" = "$cm_want" ] && return 0
  cm_old=$(awk -F '\t' -v p="$cm_rel" '$1==p {print $2; exit}' "$CM_DATA/run/owned.tsv" 2>/dev/null)
  cm_old=${cm_old:-$cm_now}
  awk -F '\t' -v p="$cm_rel" '$1!=p' "$CM_DATA/run/owned.tsv" 2>/dev/null > "$CM_DATA/run/owned.tmp"
  printf '%s\t%s\t%s\t%s\n' "$cm_rel" "$cm_old" "$cm_now" "$cm_want" >> "$CM_DATA/run/owned.tmp"
  mv "$CM_DATA/run/owned.tmp" "$CM_DATA/run/owned.tsv" || return 1
  { printf '%s\n' "$cm_want" > "$1"; } 2>/dev/null || return 1
  [ "$(selected "$1")" = "$cm_want" ]
}
restore_nodes() {
  cm_failed=0; cm_restore_error=0
  : > "$CM_DATA/run/keep.tsv"
  while IFS='	' read -r cm_rel cm_old cm_last cm_want; do
    safe_node "$cm_rel" || { cm_failed=1; cm_restore_error=1; continue; }
    cm_actual=$(selected "$CM_SYS/$cm_rel")
    [ "$cm_actual" = "$cm_old" ] && continue
    # A competing controller owns a different value now.
    [ "$cm_actual" = "$cm_last" ] || [ "$cm_actual" = "$cm_want" ] || continue
    cm_busy=0
    case "$cm_rel" in block/zram*/comp_algorithm)
      [ "$(read_node "$CM_SYS/${cm_rel%/*}/initstate" 1)" = 0 ] || cm_busy=1 ;;
    esac
    if [ "$cm_busy" = 0 ] && { printf '%s\n' "$cm_old" > "$CM_SYS/$cm_rel"; } 2>/dev/null &&
       [ "$(selected "$CM_SYS/$cm_rel")" = "$cm_old" ]; then continue; fi
    printf '%s\t%s\t%s\t%s\n' "$cm_rel" "$cm_old" "$cm_last" "$cm_want" >> "$CM_DATA/run/keep.tsv"
    cm_failed=1
    [ "$cm_busy" = 1 ] || cm_restore_error=1
  done 2>/dev/null < "$CM_DATA/run/owned.tsv"
  mv "$CM_DATA/run/keep.tsv" "$CM_DATA/run/owned.tsv"
  if [ "$cm_failed" = 1 ]; then : > "$CM_DATA/run/restore_pending"; else rm -f "$CM_DATA/run/restore_pending"; fi
  [ "$cm_failed" = 0 ]
}
validate_hardware() {
  gate || fail 'Kontrol Manager memerlukan Xiaomi 14T Pro dan Cogan Bridge yang cocok.'
  cm_n=0
  for cm_p in "$CM_SYS"/devices/system/cpu/cpufreq/policy*; do
    [ -r "$cm_p/scaling_governor" ] || continue
    cm_n=$((cm_n + 1))
    [ "$CPU" = default ] || { contains "$(read_node "$cm_p/scaling_available_governors")" "$CPU" &&
      [ -w "$cm_p/scaling_governor" ]; } || fail 'Governor CPU tidak didukung di semua policy.'
  done
  [ "$CPU" = default ] || [ "$cm_n" -gt 0 ] || fail 'Policy CPU tidak ditemukan.'
  [ "$BW" = default ] || [ -n "$(bw_nodes)" ] || fail 'bw_hwmon tidak tersedia pada driver perangkat ini. Pilih DRAM Sistem.'
  [ "$RAM" = default ] && return
  cm_n=0; cm_algo=$(compressor)
  for cm_z in "$CM_SYS"/block/zram*; do
    [ -r "$cm_z/comp_algorithm" ] || continue
    cm_n=$((cm_n + 1))
    cm_algos=$(read_node "$cm_z/comp_algorithm" | tr -d '[]')
    contains "$cm_algos" "$cm_algo" && [ -w "$cm_z/comp_algorithm" ] ||
      fail 'Kompresor RAM tidak didukung di semua perangkat ZRAM.'
  done
  [ "$cm_n" -gt 0 ] || fail 'ZRAM tidak ditemukan.'
}
apply_controls() {
  validate_hardware
  boot_session || fail 'Identitas boot tidak dapat dibaca.'
  # Restore only nodes no longer selected, preserving the original baseline for other nodes.
  if [ "$CPU" = default ] || [ "$RAM" = default ] || [ "$BW" = default ]; then
    cp "$CM_DATA/run/owned.tsv" "$CM_DATA/run/all.tsv" 2>/dev/null || : > "$CM_DATA/run/all.tsv"
    awk -F '\t' -v c="$CPU" -v r="$RAM" -v b="$BW" '(c=="default" && $1~/scaling_governor$/) || (r=="default" && $1~/comp_algorithm$/) || (b=="default" && $1~/\/governor$/)' "$CM_DATA/run/all.tsv" > "$CM_DATA/run/owned.tsv"
    restore_nodes || : # An initialized ZRAM compressor can only return at the next boot.
    awk -F '\t' -v c="$CPU" -v r="$RAM" -v b="$BW" '!((c=="default" && $1~/scaling_governor$/) || (r=="default" && $1~/comp_algorithm$/) || (b=="default" && $1~/\/governor$/))' "$CM_DATA/run/all.tsv" >> "$CM_DATA/run/owned.tsv"
  fi
  if [ "$CPU" != default ]; then
    for cm_p in "$CM_SYS"/devices/system/cpu/cpufreq/policy*; do
      [ -r "$cm_p/scaling_governor" ] || continue
      put_node "$cm_p/scaling_governor" "$CPU" || { restore_nodes; fail 'Governor ditolak; periksa nilai terbaca.'; }
    done
  fi
  if [ "$BW" != default ]; then
    for cm_bw in $(bw_nodes); do
      put_node "$cm_bw" bw_hwmon || { restore_nodes; fail 'bw_hwmon ditolak; periksa nilai terbaca.'; }
    done
  fi
  if [ "$RAM" != default ]; then
    cm_algo=$(compressor)
    for cm_z in "$CM_SYS"/block/zram*; do
      [ -r "$cm_z/comp_algorithm" ] || continue
      [ "$(selected "$cm_z/comp_algorithm")" = "$cm_algo" ] && continue
      if [ "$(read_node "$cm_z/initstate" 1)" != 0 ]; then continue; fi
      put_node "$cm_z/comp_algorithm" "$cm_algo" || { restore_nodes; fail 'Kompresor RAM ditolak; periksa nilai terbaca.'; }
    done
  fi
}
status_json() {
  printf '{"ok":1,"config":{"cpu":"%s","ram":"%s","boot":%s,"bw":"%s"},"writable":' "$CPU" "$RAM" "$BOOT" "$BW"
  if gate; then printf '1'; else printf '0'; fi
  printf ',"kernel":'; kernel_json; printf ',"device":'; device_json
  printf ',"version":'; json_string "$(sed -n 's/^version=//p' "$MODROOT/module.prop")"
  printf ',"cpu":['; cm_sep=
  for cm_p in "$CM_SYS"/devices/system/cpu/cpufreq/policy*; do
    [ -r "$cm_p/scaling_governor" ] || continue
    printf '%s{"name":' "$cm_sep"; json_string "${cm_p##*/}"
    printf ',"current":'; json_string "$(selected "$cm_p/scaling_governor")"
    printf ',"available":'; json_string "$(read_node "$cm_p/scaling_available_governors")"
    printf '}'; cm_sep=,
  done
  printf '],"dram":['; cm_sep=
  for cm_d in $(dram_nodes); do
    printf '%s{"name":' "$cm_sep"; json_string "${cm_d##*/}"
    printf ',"driver":"mtk-dvfsrc-devfreq","current":'; json_string "$(selected "$cm_d/governor")"
    printf ',"available":'; json_string "$(read_node "$cm_d/available_governors")"
    printf '}'; cm_sep=,
  done
  printf '],"bw_hwmon":['; cm_sep=
  for cm_bw in $(bw_nodes); do
    printf '%s{"name":' "$cm_sep"; json_string "${cm_bw#"$CM_SYS/"}"
    printf ',"current":'; json_string "$(selected "$cm_bw")"; printf '}'; cm_sep=,
  done
  printf '],"zram":['; cm_sep=
  cm_z_count=0; cm_z_diff=0; cm_z_busy=0; cm_z_unsupported=0; cm_algo=$(compressor)
  for cm_z in "$CM_SYS"/block/zram*; do
    [ -r "$cm_z/comp_algorithm" ] || continue
    cm_z_count=$((cm_z_count + 1))
    cm_current=$(selected "$cm_z/comp_algorithm")
    cm_available=$(read_node "$cm_z/comp_algorithm" | tr -d '[]')
    cm_initialized=$(read_node "$cm_z/initstate" 1)
    if [ -n "$cm_algo" ] && [ "$cm_current" != "$cm_algo" ]; then
      cm_z_diff=1
      [ "$cm_initialized" = 0 ] || cm_z_busy=1
      contains "$cm_available" "$cm_algo" || cm_z_unsupported=1
    fi
    printf '%s{"name":' "$cm_sep"; json_string "${cm_z##*/}"
    printf ',"current":'; json_string "$cm_current"
    printf ',"available":'; json_string "$cm_available"
    printf ',"initialized":'; json_string "$cm_initialized"
    cm_swap=-1
    if [ -r "$CM_PROC/swaps" ]; then
      cm_swap=$(awk -v n="${cm_z##*/}" 'NR==1 {valid=($1=="Filename")} NR>1 {p=$1; sub(/^.*\//,"",p); if(p==n) found=1} END {print valid?found+0:-1}' "$CM_PROC/swaps") || cm_swap=-1
    fi
    printf ',"swap_active":%d' "$cm_swap"
    printf '}'; cm_sep=,
  done
  cm_ram_state=system
  if [ -n "$cm_algo" ]; then
    cm_ram_state=matching
    if [ "$cm_z_count" = 0 ]; then cm_ram_state=unavailable
    elif [ "$cm_z_unsupported" = 1 ]; then cm_ram_state=unsupported
    elif [ "$cm_z_diff" = 1 ]; then
      cm_ram_state=ready
      if [ "$cm_z_busy" = 1 ]; then
        cm_ram_state=needs_boot
        if [ "$BOOT" = 1 ]; then
          cm_ram_state=pending_boot
          if [ "$(read_node "$CM_DATA/run/boot")" = "$(read_node "$CM_PROC/sys/kernel/random/boot_id")" ] &&
             [ "$(read_node "$CM_DATA/run/ram_boot_attempted")" = "$cm_algo" ]; then cm_ram_state=blocked; fi
        fi
      fi
    fi
  fi
  printf '],"ram_state":"%s","restore_pending":%d' "$cm_ram_state" "$([ -f "$CM_DATA/run/restore_pending" ] && echo 1 || echo 0)"
  printf ',"init_state":'; json_string "$(read_node "$CM_DATA/init.state" unknown)"
  printf ',"init_seen":'; json_string "$(read_node "$CM_DEV/.cogan_smart_zram_init")"
  printf ',"init_error":'; json_string "$(head -c 200 "$CM_DATA/init.error" 2>/dev/null)"
  printf '}\n'
}
case "$1" in status) status_json; exit 0 ;; esac
# Every mutation is serialized, including the short boot hook.
umask 077
mkdir -p "$CM_DATA/run" || fail 'Gagal menyiapkan Manager.'
lock_take "$CM_DATA/api.lock" || fail 'Perintah lain sedang berjalan'
trap 'lock_drop "$CM_DATA/api.lock"' EXIT
case "$1" in
  set|apply)
    cm_cmd=$1; shift
    valid_settings "$@" || fail 'Nilai tidak valid; tidak ada perubahan'
    if init_update_pending; then
      printf '%s\n' error > "$CM_DATA/init.state"
      printf '%s\n' 'Pembaruan modul menunggu reboot. Selesaikan reboot pembaruan sebelum menyimpan pilihan boot.' > "$CM_DATA/init.error"
      fail 'Pembaruan modul menunggu reboot. Selesaikan reboot pembaruan sebelum menyimpan pilihan boot.'
    fi
    CPU=$1; RAM=$2; BOOT=$3; [ $# = 3 ] || BW=$4
    validate_hardware
    if [ "$cm_cmd" = apply ]; then apply_controls; fi
    save_config || fail 'Gagal menyimpan setelan'
    sync_init || { printf '%s\n' error > "$CM_DATA/init.state"; fail 'Setelan tersimpan, tetapi integrasi init gagal disinkronkan. Periksa status Manager.'; }
    status_json ;;
  reset)
    gate || fail 'Kontrol Manager memerlukan Xiaomi 14T Pro dan Cogan Bridge yang cocok.'
    boot_session || fail 'Identitas boot tidak dapat dibaca.'
    CPU=default; RAM=default; BOOT=0; BW=default
    save_config || fail 'Gagal menyimpan setelan'
    restore_nodes || :
    sync_init || { printf '%s\n' error > "$CM_DATA/init.state"; fail 'Setelan tersimpan, tetapi integrasi init gagal disinkronkan. Periksa status Manager.'; }
    [ "$cm_restore_error" = 0 ] || fail 'Sebagian governor belum pulih; periksa kontrol Manager.'
    status_json ;;
  early)
    sync_init boot || printf '%s\n' error > "$CM_DATA/init.state"
    [ "$BOOT" = 1 ] && [ "$RAM" != default ] || exit 0
    gate || exit 0
    boot_session || exit 0
    cm_algo=$(compressor)
    for cm_z in "$CM_SYS"/block/zram*; do
      [ "$(read_node "$cm_z/initstate" 1)" = 0 ] || continue
      contains "$(read_node "$cm_z/comp_algorithm" | tr -d '[]')" "$cm_algo" || continue
      put_node "$cm_z/comp_algorithm" "$cm_algo" || :
    done ;;
  prepare) sync_init prepare ;;
  clear-init) BOOT=0; RAM=default; sync_init ;;
  boot)
    [ "$BOOT" = 1 ] || exit 0
    apply_controls
    [ "$RAM" = default ] || compressor > "$CM_DATA/run/ram_boot_attempted" ;;
  *) fail 'Perintah tidak dikenal' ;;
esac

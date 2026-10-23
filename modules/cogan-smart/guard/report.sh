#!/system/bin/sh
# Cogan Smart · Modul: what the other root modules do, a whitelist, and removal down to the roots.
# Output is JSON. Flags are guesses from the modules' own text; the WebUI shows the lines behind them.
#
#   report.sh scan                 modules, boot scripts outside modules, /data/adb and the root manager
#   report.sh trust ID | untrust ID
#   report.sh disable ID | enable ID   takes effect at the next boot, as in the root manager
#   report.sh remove ID [data]     stop its processes now; the root manager deletes the folder at reboot
#                                  (after its uninstall.sh). A pending update and the boot scripts outside
#                                  modules that use it go now; with "data", /data/adb/ID after the reboot.
#   report.sh keep ID              undo remove before the reboot
#   report.sh rmscript DIR NAME    delete /data/adb/DIR/NAME (a boot script outside modules)
#   report.sh rmentry NAME         delete /data/adb/NAME that no module and no root manager uses
#   report.sh boot                 (service.sh) finish "remove ID data" once the folder is gone

if [ "$1" = --lang ]; then shift 2; fi
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
export LC_ALL=C
ADB=${CS_ADB:-/data/adb}
KILL=${CG_KILL:-kill}   # the offline tests record kills instead
DATA=$ADB/cogan_smart/guard
SELF=cogan_smart
BOOT_DIRS='post-fs-data.d post-mount.d service.d boot-completed.d'
# Names in /data/adb that belong to a root manager or to this module, never to another module.
CORE=" ksu ksud ap apd magisk magisk.db modules modules_update metamodule $BOOT_DIRS $SELF "

fail() { printf '{"ok":0,"error":"%s"}\n' "$1"; exit 0; }
done_ok() { printf '{"ok":1%s}\n' "$1"; }
valid_id() {   # the root managers' module id rule; never "..", never a path
  case $1 in [A-Za-z]*) ;; *) return 1 ;; esac
  case $1 in *[!A-Za-z0-9._-]*) return 1 ;; esac
  [ ${#1} -le 64 ]
}
is_core_name() { case $CORE in *" $1 "*) return 0 ;; esac; return 1; }
meta_id() {   # the metamodule mounts every other module
  link=$(readlink "$ADB/metamodule" 2>/dev/null); link=${link%/}
  [ -n "$link" ] && { echo "${link##*/}"; return; }
  for p in "$ADB"/modules/*/module.prop; do
    grep -q -s -E '^metamodule=(1|true)[[:space:]]*$' "$p" && { p=${p%/module.prop}; echo "${p##*/}"; return; }
  done
}
is_core() { [ "$1" = "$SELF" ] || [ "$1" = "$(meta_id)" ]; }
is_trusted() { grep -q -s -x -F "$1" "$DATA/trusted"; }
drop_line() {   # drop_line FILE LINE
  [ -f "$1" ] || return 0
  grep -v -x -F "$2" "$1" > "$1.tmp"; mv -f "$1.tmp" "$1"
}
refers() {   # refers FILE ID: the file names /data/adb/modules/ID, not a longer id
  awk -v id="$2" '{
    s = $0
    while ((i = index(s, "/adb/modules/" id)) > 0) {
      if (substr(s, i + 13 + length(id), 1) !~ /[A-Za-z0-9._-]/) { found = 1; exit }
      s = substr(s, i + 1)
    }
  } END { exit !found }' "$1" 2>/dev/null
}
# "PID ARGS" of every process, -w so long command lines are not cut. Toybox ps needs -A;
# BusyBox ps lists all and rejects -A. (grep over /proc/*/cmdline would miss: BusyBox grep
# stops at the NUL between arguments.)
procs() { { ps -A -w -o pid,args 2>/dev/null || ps -w -o pid,args 2>/dev/null || ps -o pid,args; } | awk 'NR > 1 && $1 ~ /^[0-9]+$/'; }
stop_running() {   # stop_running TEXT: kill processes whose command line contains TEXT
  n=0
  for pid in $(procs | T=$1 awk 'index($0, ENVIRON["T"]) { print $1 }'); do
    [ "$pid" = $$ ] && continue
    $KILL -9 "$pid" 2>/dev/null && n=$((n + 1))
  done
  echo $n
}

manager() {
  if [ -f "$ADB/ksud" ]; then name='KernelSU / Next'; ver=$("$ADB/ksud" -V 2>/dev/null)
  elif [ -f "$ADB/apd" ]; then name=APatch; ver=$("$ADB/apd" -V 2>/dev/null)
  elif [ -d "$ADB/magisk" ]; then name=Magisk; ver=$(magisk -v 2>/dev/null)
  else return 0; fi
  printf 'manager\t%s\t%s\n' "$name" "$(echo "$ver" | head -n 1)"
}

module_files() {   # module_files ID DIR: one record per file; text files are read later by guard.awk
  big=$(find "$2" -type f -size +512k 2>/dev/null)
  find "$2" \( -type f -o -type l \) 2>/dev/null | while IFS= read -r f; do
    rel=${f#"$2"/}
    if [ -L "$f" ]; then kind=link   # never read through a link (it may point at a device)
    else
      case $rel in
        *.sh|*.rc|system.prop|sepolicy.rule) kind=text ;;
        *.so|bin/*|*/bin/*|*/xbin/*) kind=probe ;;
        *.*|system/*|vendor/*|product/*|system_ext/*|odm/*|webroot/*|META-INF/*) kind=other ;;
        *) kind=probe ;;
      esac
      [ "$kind" = probe ] && case $(head -c 4 "$f" 2>/dev/null) in ?ELF) kind=elf ;; *) kind=text ;; esac
      [ "$kind" = text ] && case "
$big
" in *"
$f
"*) kind=other ;; esac
    fi
    printf 'file\t%s\t%s\t%s\t%s\n' "$1" "$rel" "$kind" "$f"
  done
}

records() {
  printf 'self\t%s\nmeta\t%s\n' "$SELF" "$(meta_id)"
  manager
  [ -f "$DATA/trusted" ] && while IFS= read -r id; do printf 'trust\t%s\n' "$id"; done < "$DATA/trusted"
  for dir in "$ADB"/modules/* "$ADB"/modules_update/*; do
    [ -d "$dir" ] && [ ! -L "$dir" ] || continue
    id=${dir##*/}; parent=${dir%/*}; parent=${parent##*/}
    if [ "$parent" = modules_update ]; then
      printf 'pending\t%s\n' "$id"
      [ -d "$ADB/modules/$id" ] && continue   # the installed copy is what runs until the reboot
    fi
    printf 'module\t%s\t%s\n' "$id" "$dir"
    for flag in disable remove; do [ -e "$dir/$flag" ] && printf 'flag\t%s\t%s\n' "$id" "$flag"; done
    [ "$parent" = modules_update ] && printf 'flag\t%s\tinstall\n' "$id"
    printf 'size\t%s\t%s\n' "$id" "$(du -sk "$dir" 2>/dev/null | { read -r kb _; echo "${kb:-0}"; })"
    module_files "$id" "$dir"
  done
  for d in $BOOT_DIRS; do
    for f in "$ADB/$d"/*; do [ -f "$f" ] && printf 'boot\t%s\t%s\t%s\n' "$d" "${f##*/}" "$f"; done
  done
  for e in "$ADB"/* "$ADB"/.[!.]*; do
    [ -e "$e" ] || [ -L "$e" ] || continue
    t=file; [ -d "$e" ] && t=dir; [ -L "$e" ] && t=link
    printf 'entry\t%s\t%s\n' "${e##*/}" "$t"
  done
  # The path goes through the environment so this awk's own command line does not match.
  procs | T="$ADB/" awk 'index($0, ENVIRON["T"]) && !index($0, "/cogan_smart/guard/") {   # not this scan
    pid = $1; sub(/^[ \t]*[0-9]+[ \t]+/, ""); printf "proc\t%s\t%s\n", pid, $0 }'
}

module_dir() { [ -d "$ADB/modules/$1" ] && [ ! -L "$ADB/modules/$1" ]; }
need_module() {
  valid_id "$1" || fail 'Nama modul tidak valid'
  module_dir "$1" || [ -d "$ADB/modules_update/$1" ] || fail 'Modul tidak ditemukan'
}

remove_module() {   # remove_module ID [data]
  need_module "$1"
  is_core "$1" && fail 'Inti root manager dan Cogan Smart tidak dihapus dari sini'
  is_trusted "$1" && fail 'Modul ada di whitelist; lepaskan dulu'
  stopped=$(stop_running "$ADB/modules/$1/")
  if module_dir "$1"; then
    touch "$ADB/modules/$1/disable" "$ADB/modules/$1/remove" || fail 'Gagal menandai modul untuk dihapus'
  fi
  rm -rf "$ADB/modules_update/$1"   # a pending update would install it again at the reboot
  scripts=''
  for d in $BOOT_DIRS; do
    for f in "$ADB/$d"/*; do
      [ -f "$f" ] && refers "$f" "$1" || continue
      stop_running "$f" > /dev/null
      rm -f "$f" && scripts="$scripts${scripts:+,}\"$d/${f##*/}\""
    done
  done
  data=0
  if [ "$2" = data ] && [ -d "$ADB/$1" ] && [ ! -L "$ADB/$1" ] && ! is_core_name "$1"; then
    mkdir -p "$DATA" && { grep -q -s -x -F "$1" "$DATA/purge" || echo "$1" >> "$DATA/purge"; } && data=1
  fi
  done_ok ",\"stopped\":$stopped,\"scripts\":[$scripts],\"data\":$data,\"reboot\":$(module_dir "$1" && echo 1 || echo 0)"
}

# Data of a removed module goes only after the root manager has run its uninstall.sh and deleted it.
finish_removals() {
  [ -f "$DATA/purge" ] || return 0
  : > "$DATA/purge.next"
  while IFS= read -r id; do
    valid_id "$id" && ! is_core_name "$id" || continue
    if module_dir "$id"; then
      [ -e "$ADB/modules/$id/remove" ] && echo "$id" >> "$DATA/purge.next"   # restored: keep its data
      continue
    fi
    [ -L "$ADB/$id" ] || rm -rf "$ADB/$id"
  done < "$DATA/purge"
  mv -f "$DATA/purge.next" "$DATA/purge"
  [ -s "$DATA/purge" ] || rm -f "$DATA/purge"
}

case $1 in
  scan)
    # Device ⇄ kernel ⇄ module (D-023): the same identity the other tabs show goes into the report.
    MODROOT=$MODDIR/..; . "$MODROOT/bridge.sh"
    CG_KERNEL=$(kernel_json); CG_DEVICE=$(device_json); export CG_KERNEL CG_DEVICE
    records | awk -v ADB="$ADB" -f "$MODDIR/guard.awk" ;;
  trust)
    need_module "$2"; mkdir -p "$DATA" || fail 'Gagal menyimpan whitelist'
    is_trusted "$2" || echo "$2" >> "$DATA/trusted" || fail 'Gagal menyimpan whitelist'
    done_ok ;;
  untrust)
    valid_id "$2" || fail 'Nama modul tidak valid'
    is_core "$2" && fail 'Root manager, metamodule dan Cogan Smart selalu dipercaya'
    drop_line "$DATA/trusted" "$2"; done_ok ;;
  disable|enable)
    need_module "$2"; module_dir "$2" || fail 'Modul baru dipasang setelah reboot'
    is_core "$2" && fail 'Inti root manager dan Cogan Smart tidak dinonaktifkan dari sini'
    if [ "$1" = disable ]; then touch "$ADB/modules/$2/disable"; else rm -f "$ADB/modules/$2/disable"; fi || fail 'Gagal mengubah modul'
    done_ok ;;
  remove) remove_module "$2" "$3" ;;
  keep)
    need_module "$2"; module_dir "$2" || fail 'Update modul sudah dibuang; pasang ulang dari root manager'
    rm -f "$ADB/modules/$2/remove" "$ADB/modules/$2/disable"; drop_line "$DATA/purge" "$2"; done_ok ;;
  rmscript)
    case " $BOOT_DIRS " in *" $2 "*) ;; *) fail 'Folder skrip tidak valid' ;; esac
    case $3 in ''|.|..|*/*) fail 'Nama skrip tidak valid' ;; esac
    [ -f "$ADB/$2/$3" ] || fail 'Skrip tidak ditemukan'
    stop_running "$ADB/$2/$3" > /dev/null
    rm -f "$ADB/$2/$3" || fail 'Gagal menghapus skrip'
    done_ok ;;
  rmentry)
    case $2 in ''|.|..|*/*) fail 'Nama tidak valid' ;; esac
    is_core_name "$2" && fail 'Milik root manager; tidak dihapus'
    [ -e "$ADB/$2" ] || [ -L "$ADB/$2" ] || fail 'Tidak ditemukan'
    [ -d "$ADB/modules/$2" ] && fail 'Data modul terpasang; hapus modulnya'
    grep -l -s -r -F "/data/adb/$2" "$ADB/modules" > /dev/null && fail 'Masih dipakai modul terpasang'
    rm -rf "$ADB/$2" || fail 'Gagal menghapus'
    done_ok ;;
  boot) finish_removals; done_ok ;;
  *) fail 'Perintah tidak dikenal' ;;
esac

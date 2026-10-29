# Cogan Bridge companion ABI 1, shared by the power and thermal parts of Cogan Smart Kernel.
# Never infer an original kernel identity from uname alone.
CB_SYS=${CB_SYS:-${CP_SYS:-${CT_SYS:-/sys}}}
CB_PROC=${CB_PROC:-${CP_PROC:-${CT_PROC:-/proc}}}
CB_ROOT=$CB_SYS/kernel/cogan

json_string() {
  printf '%s' "$1" | awk 'BEGIN { printf "\"" } {
    if (NR > 1) printf "\\n";
    gsub(/\\/, "\\\\"); gsub(/\"/, "\\\""); gsub(/\t/, "\\t"); gsub(/\r/, "\\r");
    printf "%s", $0
  } END { printf "\"" }'
}

uint() {
  case "$1" in ''|*[!0-9]*) return 1 ;; esac
  case "$1" in 0|[1-9]*) ;; *) return 1 ;; esac
  [ "${#1}" -le 10 ]
}

read_node() {
  cb_value=""
  IFS= read -r cb_value 2>/dev/null < "$1" || :
  printf '%s' "${cb_value:-$2}"
}

# read_into VAR FILE: the first line of FILE into VAR (empty when unreadable). No subshell, no process:
# the background workers call it dozens of times per check (v2.9.1, owner's log: 4.8% CPU before).
read_into() { eval "$1=''"; IFS= read -r "$1" 2>/dev/null < "$2" || :; }

# Detect the exported ABI, independently of branding or a spoofed uname.
# Virtual files may report size zero even when their read callback returns data.
bridge_available() { read_into cb_abi "$CB_ROOT/abi"; read_into cb_rel "$CB_ROOT/release"; [ "$cb_abi" = 1 ] && [ -n "$cb_rel" ]; }

kernel_release() {
  if bridge_available; then cat "$CB_ROOT/release"; return; fi
  candidate=$(cat "$CB_PROC/sys/kernel/osrelease" 2>/dev/null)
  [ -n "$candidate" ] || candidate=$(uname -r)
  printf '%s\n' "$candidate"
}

kernel_json() {
  shown=$(uname -r)
  if bridge_available; then
    candidate=$(read_node "$CB_ROOT/release")
    source=cogan_bridge; verified=1; original=$(json_string "$candidate")
    banner=$(cat "$CB_ROOT/banner" 2>/dev/null)
    features=$(cat "$CB_ROOT/features" 2>/dev/null)
  else
    candidate=$(read_node "$CB_PROC/sys/kernel/osrelease")
    [ -n "$candidate" ] || candidate=$shown
    source=proc_candidate; verified=0; original=null
    [ -r "$CB_PROC/sys/kernel/osrelease" ] || source=uname_only
    banner=$(cat "$CB_PROC/version" 2>/dev/null); features=""
  fi
  compat=0; case "$candidate" in 6.1.[0-9]*) compat=1 ;; esac
  if [ "$verified" = 1 ]; then cb_mode=native
  elif [ "$compat" = 1 ]; then cb_mode=sysfs_compat
  else cb_mode=sysfs; fi
  printf '{"bridge":%d,"abi":%d,"verified":%d,"compat_61":%d,"mode":"%s","source":"%s","original":%s,"release":' "$verified" "$verified" "$verified" "$compat" "$cb_mode" "$source" "$original"
  json_string "$candidate"
  printf ',"uname":'; json_string "$shown"
  printf ',"different":%d,"banner":' "$([ "$candidate" != "$shown" ] && echo 1 || echo 0)"
  json_string "$banner"
  printf ',"features":'; json_string "$features"
  printf ',"limits":'; json_string "$(cat "$CB_ROOT/limits" 2>/dev/null)"
  printf ',"power_client":'; json_string "$(cat "$CB_ROOT/power_client" 2>/dev/null)"
  printf ',"thermal_client":'; json_string "$(cat "$CB_ROOT/thermal_client" 2>/dev/null)"
  printf '}'
}

CB_DEVICES=${CB_DEVICES:-rothko}   # codenames this module is built and tested for

# Device ⇄ kernel: what the phone says it is, and whether the kernel was built for it. A target
# from the bridge (optional ABI 1 attributes device/soc) is compiled into the kernel and verified;
# one found in the release or banner name is only a candidate. match: 1 yes, 0 no, -1 unknown.
device_json() {
  cb_code=$(getprop ro.product.device 2>/dev/null)
  cb_name=$(getprop ro.product.marketname 2>/dev/null)
  [ -n "$cb_name" ] || cb_name=$(getprop ro.product.model 2>/dev/null)
  cb_soc=$(getprop ro.board.platform 2>/dev/null)
  cb_supported=0
  for cb_dev in $CB_DEVICES; do [ "$cb_dev" = "$cb_code" ] && cb_supported=1; done
  cb_target=""; cb_ksoc=""; cb_verified=0
  if bridge_available; then cb_target=$(read_node "$CB_ROOT/device"); cb_ksoc=$(read_node "$CB_ROOT/soc"); fi
  if [ -n "$cb_target" ]; then
    cb_verified=1
  else
    cb_names=$(printf '%s %s' "$(kernel_release)" "$(cat "$CB_PROC/version" 2>/dev/null)" | tr 'A-Z' 'a-z')
    for cb_dev in $CB_DEVICES; do case "$cb_names" in *"-$cb_dev-"*|*"-$cb_dev "*) cb_target=$cb_dev ;; esac; done
  fi
  cb_match=-1
  if [ -n "$cb_target" ] && [ -n "$cb_code" ]; then
    if [ "$cb_target" = "$cb_code" ]; then cb_match=1; else cb_match=0; fi
  fi
  printf '{"codename":'; json_string "$cb_code"
  printf ',"name":'; json_string "$cb_name"
  printf ',"platform":'; json_string "$cb_soc"
  printf ',"supported":%d,"kernel_target":' "$cb_supported"; json_string "$cb_target"
  printf ',"kernel_soc":'; json_string "$cb_ksoc"
  printf ',"match":%d,"verified":%d}' "$cb_match" "$cb_verified"
}

bridge_heartbeat() { # power|thermal, versionCode (0 unregisters)
  bridge_available || return 0
  case "$1" in power|thermal) ;; *) return 1 ;; esac
  uint "$2" || return 1
  { printf '%s\n' "$2" > "$CB_ROOT/${1}_client"; } 2>/dev/null
}

module_code() { sed -n 's/^versionCode=//p' "$MODROOT/module.prop"; }
# The workers' heartbeat: versionCode read once per start, so a check costs no process for it.
MODULE_CODE=""
heartbeat() { [ -n "$MODULE_CODE" ] || MODULE_CODE=$(module_code); bridge_heartbeat "$1" "$MODULE_CODE"; }

cooling_json() {
  for cb_dev in "$CB_SYS"/class/thermal/cooling_device*; do
    cb_cur=""; cb_max=""; cb_type=""
    IFS= read -r cb_cur 2>/dev/null < "$cb_dev/cur_state" || :
    IFS= read -r cb_max 2>/dev/null < "$cb_dev/max_state" || :
    uint "$cb_cur" && uint "$cb_max" || continue
    IFS= read -r cb_type 2>/dev/null < "$cb_dev/type" || :
    printf '%s\t%d\t%d\n' "$cb_type" "$cb_cur" "$cb_max"
  done | awk -F '\t' '
    function escape(s) { gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s); gsub(/\r/, "\\r", s); gsub(/\t/, "\\t", s); return s }
    BEGIN { printf "[" }
    NF >= 3 {
      name=$1; for (i=2;i<=NF-2;i++) name=name "\t" $i
      printf "%s{\"name\":\"%s\",\"state\":%d,\"max\":%d}", (n++ ? "," : ""), escape(name), $(NF-1), $NF
    }
    END { printf "]" }'
}

# A worker started from the root manager's WebUI inherits the app's cgroup (0::/uid_N/pid_M). When that app process
# dies, Android SIGKILLs the whole cgroup through cgroup.kill (libprocessgroup sendSignalToProcessGroup), root
# workers included: the owner's Start turned back to stopped (2026-10-29). setsid/nohup do not leave a cgroup, so a
# worker moves itself to the root cgroup. Workers started at boot (service.sh, not an app) are left where they are.
leave_app_cgroup() {
  case "$(cat "${CB_CG_PROC:-/proc}/$$/cgroup" 2>/dev/null)" in
    *::/uid_[0-9]*) echo $$ > "${CB_CGROUP:-/sys/fs/cgroup}/cgroup.procs" 2>/dev/null ;;
  esac
}

safe_pid() { # PID_FILE SCRIPT_PATH: check the full script path, not a generic name.
  read_into cb_pid "$1"
  uint "$cb_pid" && [ "$cb_pid" -gt 1 ] || return 1
  kill -0 "$cb_pid" 2>/dev/null || return 1
  # A worker that keeps running (the controller) checks the same live PID's command line again only
  # every 30 calls; called in $(...), nothing is remembered and every call checks.
  cb_safe_n=$((${cb_safe_n:-0} + 1))
  if [ "${cb_safe_key-}" != "$cb_pid $2" ] || [ "$cb_safe_n" -ge 30 ]; then
    cb_safe_key=""
    (tr '\0' '\n' < "${CB_PID_PROC:-/proc}/$cb_pid/cmdline") 2>/dev/null | grep -Fqx "$2" || return 1
    cb_safe_key="$cb_pid $2"; cb_safe_n=0
  fi
  printf '%s\n' "$cb_pid"
}

# Both workers and both pages use exactly the same sensor decoder and CPU/GPU grouping.
# HyperOS's own board (shell) temperature joins as the zone hyperos_board, in the phone body group:
# it matched quiet_therm on the owner's phone (40.6 vs 40.8 °C, 24 Oct 2026). Read only.
read_thermal_sensors() {
  {
    for cs_zone in "$CB_SYS"/class/thermal/thermal_zone*; do
      [ -r "$cs_zone/temp" ] || continue
      cs_type=""; cs_temp=""
      IFS= read -r cs_type 2>/dev/null < "$cs_zone/type" || :
      IFS= read -r cs_temp 2>/dev/null < "$cs_zone/temp" || :
      printf '%s %s\n' "$cs_type" "$cs_temp"
    done
    cs_temp=""
    IFS= read -r cs_temp 2>/dev/null < "$CB_SYS/class/thermal/thermal_message/board_sensor_temp" || :
    [ -n "$cs_temp" ] && printf 'hyperos_board %s\n' "$cs_temp"
  } | awk -f "$MODROOT/thermal/thermal.awk" -f "$MODROOT/thermal/sensors.awk"
}

# HyperOS's own thermal state (thermal_message), read only: what the phone itself limits right now.
# JSON {"present":0|1,"board":tenths,"sconfig":"…","temp_state":"…","cpu_limits":"…","modem_limit":"…",
#       "wifi_limit":"…","max_brightness":"…","video_mode":"…"}; each value is the node's first line.
# Part of every live status, so it costs one awk: the nodes are read with shell builtins.
hyperos_json() {
  hj_dir=$CB_SYS/class/thermal/thermal_message
  if [ ! -d "$hj_dir" ]; then printf '{"present":0}'; return; fi
  for hj_node in board_sensor_temp sconfig temp_state cpu_limits modem_limit wifi_limit thermal_max_brightness video_mode; do
    read_node "$hj_dir/$hj_node"; echo
  done | awk 'BEGIN { split("board sconfig temp_state cpu_limits modem_limit wifi_limit max_brightness video_mode", K, " ") }
    NR == 1 { board = ($0 ~ /^-?[0-9]+$/) ? int($0 / 100) : -9999; next }
    { v = substr($0, 1, 120); gsub(/\\/, "\\\\", v); gsub(/"/, "\\\"", v); gsub(/\t/, "\\t", v); gsub(/\r/, "", v)
      s = s sprintf(",\"%s\":\"%s\"", K[NR], v) }
    END { printf "{\"present\":1,\"board\":%d%s}", board, s }'
}

# Phone body (skin) temperature of a zone list in tenths of °C, or -9999 without a skin sensor.
body_temp() {
  awk -v mode=body -v zones="$1" -f "$MODROOT/thermal/thermal.awk" -f "$MODROOT/thermal/report.awk"
}

# A very short, boot-scoped snapshot makes a tab switch reuse the same measurement.
# Controllers bypass this cache and always read the hardware. No sysfs writes here.
sensor_snapshot() {
  SS_TS=$(date +%s); SS_MAIN=-9999; SS_ZONES=""
  cs_dir=${CT_DATA:-/data/adb/cogan_smart/thermal}/run
  cs_key="v1|$(read_node "$CB_PROC/sys/kernel/random/boot_id")|$CB_SYS"
  if IFS='	' read -r cs_ts cs_saved_key cs_main cs_zones 2>/dev/null < "$cs_dir/sensors.tsv" &&
     uint "$cs_ts" && [ "$cs_saved_key" = "$cs_key" ] &&
     [ "$SS_TS" -ge "$cs_ts" ] && [ $((SS_TS - cs_ts)) -le 2 ]; then
    SS_TS=$cs_ts; SS_MAIN=$cs_main; SS_ZONES=$cs_zones
    return
  fi
  cs_sample=$(read_thermal_sensors)
  SS_MAIN=${cs_sample%%	*}; SS_ZONES=${cs_sample#*	}; SS_ZONES=${SS_ZONES%%	*}
  if mkdir -p "$cs_dir"; then
    (umask 077; printf '%s\t%s\t%s\t%s\n' "$SS_TS" "$cs_key" "$SS_MAIN" "$SS_ZONES" > "$cs_dir/sensors.tsv.$$" &&
      mv "$cs_dir/sensors.tsv.$$" "$cs_dir/sensors.tsv") 2>/dev/null || :
  fi
}

# A live PID and a fresh sample are separate facts. Never call stale data "stopped".
# This health contract is used by Power's monitor banner and Thermal's recording badge.
thermal_health() {
  cs_data=${CT_DATA:-/data/adb/cogan_smart/thermal}
  cs_mod=${CT_MOD:-$MODROOT}
  CS_INSTALLED=0; CS_RUNNING=0; CS_FRESH=0; CS_STALLED=0
  CS_PID=0; CS_TS=0; CS_AGE=-1; CS_INTERVAL=20; CS_STARTED=0
  [ -f "$cs_mod/module.prop" ] && [ ! -f "$cs_mod/disable" ] && [ ! -f "$cs_mod/remove" ] && CS_INSTALLED=1
  while IFS='=' read -r cs_name cs_value; do
    if [ "$cs_name" = INTERVAL ] && uint "$cs_value" && [ "$cs_value" -ge 10 ] && [ "$cs_value" -le 300 ]; then CS_INTERVAL=$cs_value; fi
  done 2>/dev/null < "$cs_data/config"
  cs_limit=$((CS_INTERVAL * 3)); [ "$cs_limit" -ge 90 ] || cs_limit=90
  cs_now=${CB_NOW:-$(date +%s)}   # a worker that just read the clock passes it in CB_NOW
  read_into cs_last "$cs_data/run/last"
  if uint "$cs_last" && [ "$cs_last" -gt 0 ]; then
    CS_TS=$cs_last; CS_AGE=$((cs_now - CS_TS))
  fi
  cs_pid=0; safe_pid "$cs_data/run/sampler.pid" "$cs_mod/thermal/sampler.sh" > /dev/null && cs_pid=$cb_pid
  if [ "$CS_INSTALLED" = 1 ] && [ "$cs_pid" -gt 0 ]; then
    CS_RUNNING=1; CS_PID=$cs_pid
    read_into cs_started "$cs_data/run/started"
    uint "$cs_started" && CS_STARTED=$cs_started
    if [ "$CS_AGE" -ge 0 ] && [ "$CS_AGE" -le "$cs_limit" ] && [ "$CS_TS" -ge "$CS_STARTED" ]; then
      CS_FRESH=1
    elif [ "$CS_STARTED" -gt 0 ] && [ $((cs_now - CS_STARTED)) -le "$cs_limit" ]; then
      : # The first sample is still being collected.
    else CS_STALLED=1; fi
  fi
}

thermal_health_json() {
  printf '{"installed":%d,"running":%d,"fresh":%d,"stalled":%d,"pid":%d,"ts":%d,"age":%d,"interval":%d}' \
    "$CS_INSTALLED" "$CS_RUNNING" "$CS_FRESH" "$CS_STALLED" "$CS_PID" "$CS_TS" "$CS_AGE" "$CS_INTERVAL"
}

peer_json() { # module directory, pid file, script
  cb_installed=0; cb_running=0
  [ -f "$1/module.prop" ] && [ ! -f "$1/disable" ] && [ ! -f "$1/remove" ] && cb_installed=1
  safe_pid "$2" "$1/$3" >/dev/null && cb_running=1
  printf '{"installed":%d,"running":%d,"version":' "$cb_installed" "$cb_running"
  json_string "$(sed -n 's/^version=//p' "$1/module.prop" 2>/dev/null)"
  printf '}'
}

# A PID-owned mkdir lock works with Android sh; no flock dependency or kill -9.
lock_take() { # directory; caller releases explicitly or through its EXIT trap.
  [ -d "${1%/*}" ] || mkdir -p "${1%/*}"
  read_into cb_boot /proc/sys/kernel/random/boot_id
  cb_try=0
  while ! mkdir "$1" 2>/dev/null; do
    cb_owner=$(cat "$1/pid" 2>/dev/null)
    cb_old_boot=$(cat "$1/boot_id" 2>/dev/null)
    cb_stale=0
    [ -n "$cb_old_boot" ] && [ -n "$cb_boot" ] && [ "$cb_old_boot" != "$cb_boot" ] && cb_stale=1
    if uint "$cb_owner" && [ "$cb_owner" -gt 1 ]; then
      if ! kill -0 "$cb_owner" 2>/dev/null; then cb_stale=1
      elif ! safe_pid "$1/pid" "$MODDIR/report.sh" >/dev/null &&
           ! safe_pid "$1/pid" "$MODDIR/controller.sh" >/dev/null &&
           ! safe_pid "$1/pid" "$MODDIR/sampler.sh" >/dev/null; then cb_stale=1; fi
    elif [ "$cb_try" -ge 10 ]; then
      cb_stale=1
    fi
    if [ "$cb_stale" = 1 ]; then
      rm -f "$1/pid" "$1/boot_id"; rmdir "$1" 2>/dev/null || return 1
      continue
    fi
    [ "$cb_try" -ge 50 ] && return 1
    sleep 0.1; cb_try=$((cb_try + 1))
  done
  printf '%s\n' "$cb_boot" > "$1/boot_id"
  printf '%s\n' "$$" > "$1/pid"
}

lock_drop() {
  read_into cb_lock_pid "$1/pid"
  [ "$cb_lock_pid" = "$$" ] || return 0
  rm -f "$1/pid" "$1/boot_id"; rmdir "$1" 2>/dev/null
}

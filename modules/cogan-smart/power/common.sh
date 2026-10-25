# Cogan Smart Kernel, power part: shared paths, settings and the few system knobs it touches.
# POSIX sh (Android mksh, KernelSU busybox sh). It only writes CPU frequency limits, the top-app
# uclamp boost and the charging switch, and puts all of them back when it stops.
# The CP_* / CT_* paths can be overridden, which the offline tests use with a fake /sys.

MODDIR=${MODDIR:-${0%/*}}
MODROOT=${MODROOT:-$(cd "$MODDIR/.." && pwd)}   # the Cogan Smart Kernel module folder
CP_DATA=${CP_DATA:-/data/adb/cogan_smart/power}
CP_SYS=${CP_SYS:-/sys}
CP_PROC=${CP_PROC:-/proc}
CP_CPUCTL=${CP_CPUCTL:-/dev/cpuctl}
CT_DATA=${CT_DATA:-/data/adb/cogan_smart/thermal}      # the thermal part's data
CT_MOD=${CT_MOD:-$MODROOT}                          # and its module folder (this module)
CP_RUN=$CP_DATA/run
CONFIG=$CP_DATA/config
EVENTS=$CP_DATA/events.tsv
BATTERY=$CP_SYS/class/power_supply/battery

# Settings (the WebUI writes $CONFIG; only these keys and values within range are accepted).
KEYS="MODE TARGET_TEMP GAME_LIMIT SAVER_CAP GAME_BOOST CHARGE_CTRL CHARGE_STOP CHARGE_RESUME CHARGE_THERMAL BATT_TEMP_STOP HEAT_PAUSE_CHARGE INTERVAL FORCE AUTOSTART CTRL_VER"
MODE=seimbang          # hemat (Hemat) | seimbang (Kernel Default) | game (Performa)
# The modes read the phone body (Badan HP), what a hand feels (owner 2026-10-24); the processor
# sits around 50 °C at rest, so a 42 °C processor target capped the CPU almost all the time.
TARGET_TEMP=41         # Kernel Default keeps the phone body at or below this (°C); Hemat 2 °C lower
GAME_LIMIT=44          # Performa only steps in at this phone body temperature (°C)
                       # Owner 24 Oct 2026: 41 °C already feels "warm, getting hot" (HyperOS board 40.6 °C)
SAVER_CAP=60           # Hemat: top speed of the big cores (% of their maximum)
GAME_BOOST=1           # Performa: give the app on screen a minimum CPU share (uclamp)
CHARGE_CTRL=1          # auto cut charging on/off
CHARGE_STOP=95         # owner default, retained settings are not silently changed
CHARGE_RESUME=90
CHARGE_THERMAL=0       # 0 = HyperCharge and the phone manage charging heat (owner 2026-10-24); 1 = module pauses too
BATT_TEMP_STOP=42      # optional module pause threshold, only when CHARGE_THERMAL=1
HEAT_PAUSE_CHARGE=1    # Kernel Default: pause while charging heats the phone body, gated by CHARGE_THERMAL
INTERVAL=10            # seconds between checks
FORCE=0               # 1 = reapply supported controls on every check
AUTOSTART=1
CTRL_VER=3             # 3 = phone body thresholds of 24 Oct 2026; older configs keep their other settings
CPU_BRAKE=95           # every mode: emergency brake when the processor reaches this (°C), not a setting
CPU_WORK=60            # the CPU is lowered only while the processor works this hot (°C): an idle CPU, or heat
                       # from charging or the room, is not what a lower CPU cap cools (owner 2026-10-24)
. "$MODROOT/bridge.sh"

defaults() {
  MODE=seimbang; TARGET_TEMP=41; GAME_LIMIT=44; SAVER_CAP=60; GAME_BOOST=1
  CHARGE_CTRL=1; CHARGE_STOP=95; CHARGE_RESUME=90; CHARGE_THERMAL=0; BATT_TEMP_STOP=42
  HEAT_PAUSE_CHARGE=1; INTERVAL=10; FORCE=0; AUTOSTART=1; CTRL_VER=3
}

limits_of() {   # limits_of KEY -> LIM_LO and LIM_HI of a numeric setting, no subshell
  case "$1" in
    TARGET_TEMP) LIM_LO=38; LIM_HI=46 ;;
    GAME_LIMIT) LIM_LO=40; LIM_HI=50 ;;
    CTRL_VER) LIM_LO=3; LIM_HI=3 ;;
    SAVER_CAP) LIM_LO=30; LIM_HI=90 ;;
    GAME_BOOST|CHARGE_CTRL|CHARGE_THERMAL|HEAT_PAUSE_CHARGE|FORCE|AUTOSTART) LIM_LO=0; LIM_HI=1 ;;
    CHARGE_STOP) LIM_LO=50; LIM_HI=100 ;;
    CHARGE_RESUME) LIM_LO=40; LIM_HI=99 ;;
    BATT_TEMP_STOP) LIM_LO=35; LIM_HI=50 ;;
    INTERVAL) LIM_LO=5; LIM_HI=60 ;;
    *) return 1 ;;
  esac
}
limits() { limits_of "$1" && echo "$LIM_LO $LIM_HI"; }   # limits KEY -> "min max"

valid() {   # valid KEY VALUE
  if [ "$1" = MODE ]; then
    case "$2" in hemat|seimbang|game) return 0 ;; *) return 1 ;; esac
  fi
  uint "$2" || return 1
  case "$2" in 0|[1-9]*) ;; *) return 1 ;; esac
  limits_of "$1" && [ "$2" -ge "$LIM_LO" ] && [ "$2" -le "$LIM_HI" ]
}

load_config() {
  defaults
  [ -f "$CONFIG" ] || return 0
  CTRL_VER=0
  while IFS='=' read -r key value; do
    valid "$key" "$value" && eval "$key=\$value"   # key is one of the settings above
  done < "$CONFIG"
  [ "$CHARGE_RESUME" -lt "$CHARGE_STOP" ] || CHARGE_RESUME=$((CHARGE_STOP - 5))
  # Older temperatures do not carry over: v2.8 meant the processor, early v2.9.0 test builds used
  # 42/45 °C. Everything else (mode, charging, interval) stays as the user saved it.
  if [ "$CTRL_VER" != 3 ]; then TARGET_TEMP=41; GAME_LIMIT=44; CTRL_VER=3; fi
}

write_config() {
  mkdir -p "$CP_DATA" || return 1
  [ ! -d "$CONFIG" ] && [ ! -L "$CONFIG" ] || return 1
  for key in $KEYS; do eval "echo \"$key=\$$key\""; done > "$CONFIG.tmp.$$" && mv "$CONFIG.tmp.$$" "$CONFIG" || return 1
  chmod 600 "$CONFIG"
}

event() {   # one line in the WebUI's activity log
  mkdir -p "$CP_DATA"
  printf '%s\t%s\n' "$(date +%s)" "$*" >> "$EVENTS"
}

deg() { echo "$(($1 / 10)).$(( ($1 < 0 ? -$1 : $1) % 10 ))"; }

# One sensor read for the controller, in tenths of °C: MAIN_T, the hottest CPU/GPU sensor, and
# BODY_T, the phone body (skin) sensor, or -9999 when the phone has none.
read_temps() {
  rt_sample=$(read_thermal_sensors)
  MAIN_T=${rt_sample%%	*}; BODY_T=${rt_sample##*	}
  case "$MAIN_T" in ''|*[!0-9-]*) MAIN_T=-9999 ;; esac
  case "$BODY_T" in ''|*[!0-9-]*) BODY_T=-9999 ;; esac
}

# Battery: sets level, status (charging, full, discharging or idle), temp (tenths of °C) and current
# (mA) with shell builtins; read_battery prints them as "level status temp current".
battery_now() {
  read_into level "$BATTERY/capacity"
  read_into status "$BATTERY/status"
  read_into temp "$BATTERY/temp"
  read_into current "$BATTERY/current_now"
  read_into design "$BATTERY/charge_full_design"
  case "$level" in ''|*[!0-9]*) level=-1 ;; esac
  case "$temp" in ''|*[!0-9-]*) temp=-999 ;; esac
  case "$current" in ''|*[!0-9-]*) current=0 ;; esac
  case "$design" in ''|*[!0-9]*) design=0 ;; esac
  current=${current#-}
  if [ "$current" -ge 20000 ] || [ "$design" -ge 100000 ]; then current=$((current / 1000)); fi   # microamps
  case "$status" in Charging) status=charging ;; Full) status=full ;; Discharging) status=discharging ;; *) status=idle ;; esac
}
read_battery() { battery_now; echo "$level $status $temp $current"; }

monitor_installed() { [ -f "$CT_MOD/module.prop" ] && [ ! -f "$CT_MOD/disable" ]; }

# Latest report of the thermal part, while its PID and interval-based freshness agree.
# sets M_MAIN, M_APP and M_CAUSE.
read_monitor() {
  M_MAIN=""; M_APP=""; M_CAUSE=""
  thermal_health
  [ "$CS_RUNNING" = 1 ] && [ "$CS_FRESH" = 1 ] || return 1
  IFS='	' read -r m_ts m_main _ _ m_app m_cause < "$CT_DATA/run/latest" 2>/dev/null || return 1
  case "$m_ts" in ''|*[!0-9]*) return 1 ;; esac
  m_age=$((${CB_NOW:-$(date +%s)} - m_ts))
  [ "$m_age" -ge 0 ] && [ "$m_age" -le "$cs_limit" ] && [ "$m_ts" -ge "$CS_STARTED" ] || return 1
  M_MAIN=$m_main; M_APP=$m_app; M_CAUSE=$m_cause
}

# Tell the thermal part which mode is active from now on; its summaries report per mode.
log_mode() {
  [ -d "$CT_DATA" ] || return 0
  last=$(tail -n 1 "$CT_DATA/modes.tsv" 2>/dev/null | cut -f 2)
  [ "$last" = "$1" ] || printf '%s\t%s\n' "$(date +%s)" "$1" >> "$CT_DATA/modes.tsv"
}

# Charging switches known from many phones, as "node|on|off" (proc/... is under /proc, the rest
# under /sys). The first one that really stops and restarts charging is kept in $CP_DATA/switch.
SWITCHES="class/power_supply/battery/input_suspend|0|1
class/power_supply/battery/charging_enabled|1|0
class/power_supply/battery/battery_charging_enabled|1|0
class/power_supply/battery/charge_disable|0|1
class/qcom-battery/input_suspend|0|1
class/power_supply/usb/input_suspend|0|1
class/power_supply/main/input_suspend|0|1
class/power_supply/battery/batt_slate_mode|0|1
class/power_supply/battery/op_disable_charge|0|1
class/power_supply/battery/mmi_charging_enable|1|0"

switch_node() {
  case "$1" in proc/*) echo "$CP_PROC/${1#proc/}" ;; *) echo "$CP_SYS/$1" ;; esac
}

is_charging() { [ "$(cat "$BATTERY/status" 2>/dev/null)" = Charging ]; }

wait_charging() {   # wait_charging yes|no SECONDS
  i=0
  while :; do
    [ "${stop:-0}" = 1 ] && return 1
    cp_charge_status=$(cat "$BATTERY/status" 2>/dev/null)
    case "$cp_charge_status:$1" in Charging:yes|Not\ charging:no|Discharging:no) return 0 ;; esac
    [ "$i" -ge "$2" ] && return 1
    sleep 1
    i=$((i + 1))
  done
}

# Try each switch while the phone charges; print one "node result" line per switch tried.
detect_switch() {
  is_charging || return 2
  found=1
  while IFS='|' read -r rel on off; do
    node=$(switch_node "$rel")
    [ -f "$node" ] || continue
    [ "${stop:-0}" = 1 ] && break
    cp_probe_before=$(cat "$node" 2>/dev/null)
    if [ "$cp_probe_before" != "$on" ]; then echo "$rel sudah_dikontrol"; continue; fi
    printf '%s|%s|%s\n' "$rel" "$on" "$off" > "$CP_RUN/probe"
    if ! (echo "$off" > "$node") 2>/dev/null; then echo "$rel tidak_bisa_ditulis"; restore_probe; continue; fi
    if wait_charging no 6; then
      restore_probe || return 1
      if wait_charging yes 15; then
        echo "$rel|$on|$off" > "$CP_DATA/switch"
        echo "$rel ok"
        found=0
        break
      fi
      echo "$rel tidak_lanjut"
    else
      echo "$rel tidak_berpengaruh"
    fi
    restore_probe || return 1
    wait_charging yes 10
  done <<EOF
$SWITCHES
EOF
  return $found
}

# Only restore controls this module actually owns. Other controllers retain their limits.
restore() {
  restore_failed=0
  if bridge_available; then (echo '0 0 0' > "$CB_ROOT/limits") 2>/dev/null || restore_failed=1; fi
  restore_probe || restore_failed=1
  restore_cpu || restore_failed=1
  set_boost 0 || restore_failed=1
  restore_charge || restore_failed=1
  bridge_heartbeat power 0
  rm -f "$CP_RUN/charge_off" "$CP_RUN/level" "$CP_RUN/cool" "$CP_RUN/hold" "$CP_RUN/prev" "$CP_RUN/state.json" "$CP_RUN/apply.tsv" "$CP_RUN/apply.tsv.tmp" "$CP_RUN/backend"
  if [ "$restore_failed" = 1 ]; then
    : > "$CP_RUN/restore_pending"; event 'Ada kontrol yang belum pulih; periksa izin node lalu Henti lagi'; return 1
  fi
  rm -f "$CP_RUN/restore_pending"
}

# Discard snapshots from a previous boot; never replay stale sysfs values after reboot.
boot_session() {
  mkdir -p "$CP_RUN"
  cp_boot=$(cat "$CP_PROC/sys/kernel/random/boot_id" 2>/dev/null)
  [ -n "$cp_boot" ] || cp_boot=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null)
  if [ "$(cat "$CP_RUN/boot_id" 2>/dev/null)" != "$cp_boot" ]; then
    rm -rf "$CP_RUN/original" "$CP_RUN/written"
    rm -f "$CP_RUN/charge.owned" "$CP_RUN/uclamp.orig" "$CP_RUN/uclamp.written" "$CP_RUN/charge_off" "$CP_RUN/state.json" "$CP_RUN/probe" "$CP_RUN/restore_pending"
    printf '%s\n' "$cp_boot" > "$CP_RUN/boot_id"
  fi
}

record_control() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> "$CP_RUN/apply.tsv.tmp"; }

controls_json() {
  [ -f "$CP_RUN/apply.tsv" ] || { printf '[]'; return; }
  awk -F '\t' 'BEGIN { printf "[" } NF == 4 {
    # Escape the regex delimiter even inside a character class (Android/BusyBox awk).
    for (i=1;i<=4;i++) gsub(/[^A-Za-z0-9_.:\/ -]/,"_",$i)
    printf "%s{\"node\":\"%s\",\"requested\":\"%s\",\"actual\":\"%s\",\"result\":\"%s\"}", (n++ ? "," : ""),$1,$2,$3,$4
  } END { printf "]" }' "$CP_RUN/apply.tsv" 2>/dev/null
}

restore_cpu() {
  cp_restore_failed=0
  for cp_orig in "$CP_RUN"/original/policy*; do
    [ -f "$cp_orig" ] || continue
    cp_name=${cp_orig##*/}; cp_node=$CP_SYS/devices/system/cpu/cpufreq/$cp_name/scaling_max_freq
    read_into cp_old "$cp_orig"; read_into cp_last "$CP_RUN/written/$cp_name"
    read_into cp_now "$cp_node"
    if [ "$cp_now" = "$cp_last" ] && uint "$cp_old"; then
      if ! (echo "$cp_old" > "$cp_node") 2>/dev/null; then
        event "Pemulihan CPU gagal: $cp_name"; cp_restore_failed=1; continue
      fi
      read_into cp_now "$cp_node"; [ "$cp_now" = "$cp_old" ] || { cp_restore_failed=1; continue; }
    fi
    rm -f "$cp_orig" "$CP_RUN/written/$cp_name"
  done
  [ "$cp_restore_failed" = 0 ]
}

# Override the original unverified sysfs writer. The bridge owns an independent
# CPU QoS request; fallback snapshots and readback are needed on older kernels.
set_cpu_cap() {
  cp_big=$1; cp_little=$2
  if bridge_available; then
    # Restore our old sysfs request before adding QoS, otherwise the aggregate
    # QoS cap can hide that request and prevent its correct restoration later.
    restore_cpu || { record_control cpu restore unknown write_failed; return 1; }
    cp_expected=0
    for cp_dir in "$CP_SYS"/devices/system/cpu/cpufreq/policy*; do
      [ -r "$cp_dir/cpuinfo_max_freq" ] && cp_expected=$((cp_expected + 1))
    done
    cp_ttl=$((INTERVAL * 3)); [ "$cp_ttl" -lt 30 ] && cp_ttl=30
    if (echo "$cp_big $cp_little $cp_ttl" > "$CB_ROOT/limits") 2>/dev/null; then
      read -r cp_rb cp_rl cp_rt cp_rn cp_re < "$CB_ROOT/limits"
      if [ "$cp_rb" = "$cp_big" ] && [ "$cp_rl" = "$cp_little" ] && uint "$cp_rt" && [ "$cp_rt" -gt 0 ] &&
          uint "$cp_rn" && [ "$cp_rn" -gt 0 ] && [ "$cp_rn" -ge "$cp_expected" ] && [ "$cp_re" = 0 ]; then
        record_control kernel/cogan/limits "$cp_big/$cp_little" "$cp_rb/$cp_rl" applied
        echo kernel_qos > "$CP_RUN/backend"
        return 0
      fi
    fi
    record_control kernel/cogan/limits "$cp_big/$cp_little" unknown write_failed
    (echo '0 0 0' > "$CB_ROOT/limits") 2>/dev/null
  fi
  echo sysfs > "$CP_RUN/backend"
  [ -d "$CP_RUN/original" ] && [ -d "$CP_RUN/written" ] || mkdir -p "$CP_RUN/original" "$CP_RUN/written"
  cp_lowest=""; cp_highest=""   # the slowest and fastest cluster, by their top frequency
  for cp_policy in "$CP_SYS"/devices/system/cpu/cpufreq/policy*; do
    read_into cp_max "$cp_policy/cpuinfo_max_freq"; uint "$cp_max" || continue
    { [ -z "$cp_lowest" ] || [ "$cp_max" -lt "$cp_lowest" ]; } && cp_lowest=$cp_max
    { [ -z "$cp_highest" ] || [ "$cp_max" -gt "$cp_highest" ]; } && cp_highest=$cp_max
  done
  cp_count=0
  for cp_policy in "$CP_SYS"/devices/system/cpu/cpufreq/policy*; do
    read_into cp_max "$cp_policy/cpuinfo_max_freq"
    read_into cp_min "$cp_policy/cpuinfo_min_freq"
    uint "$cp_max" && uint "$cp_min" || continue
    cp_count=$((cp_count + 1)); cp_pct=$cp_big; cp_name=${cp_policy##*/}
    [ "$cp_max" = "$cp_lowest" ] && [ "$cp_lowest" != "$cp_highest" ] && cp_pct=$cp_little
    cp_want=$((cp_max * cp_pct / 100)); [ "$cp_want" -lt "$cp_min" ] && cp_want=$cp_min
    cp_node=$cp_policy/scaling_max_freq
    read_into cp_now "$cp_node"
    if ! uint "$cp_now"; then record_control "$cp_name" "$cp_want" unknown unsupported; continue; fi
    cp_orig=$CP_RUN/original/$cp_name; cp_written=$CP_RUN/written/$cp_name
    [ -f "$cp_orig" ] || echo "$cp_now" > "$cp_orig"
    read_into cp_ceiling "$cp_orig"; read_into cp_last "$cp_written"
    # Preserve a stricter external limit observed between our own writes.
    if [ -n "$cp_last" ] && [ "$cp_now" != "$cp_last" ] && [ "$cp_now" -lt "$cp_ceiling" ]; then
      cp_ceiling=$cp_now; echo "$cp_ceiling" > "$cp_orig"
    fi
    [ "$cp_want" -gt "$cp_ceiling" ] && cp_want=$cp_ceiling
    # The highest available step at or under the wanted speed; the steps do not change, so a running
    # controller looks each one up once.
    cp_key=CP_STEP_${cp_name}_$cp_want; eval "cp_freq=\${$cp_key-}"
    if [ -z "$cp_freq" ]; then
      cp_freq=$(awk -v want="$cp_want" '{for(i=1;i<=NF;i++) if($i+0<=want && $i+0>best)best=$i+0} END{print best+0}' "$cp_policy/scaling_available_frequencies" 2>/dev/null)
      eval "$cp_key=\$cp_freq"
    fi
    [ "${cp_freq:-0}" -gt 0 ] || cp_freq=$cp_want
    cp_result=applied
    if [ "$cp_now" != "$cp_freq" ]; then
      if [ "$FORCE" = 0 ] && [ "$cp_last" = "$cp_freq" ]; then cp_result=conflict
      elif (echo "$cp_freq" > "$cp_node") 2>/dev/null; then
        read_into cp_actual "$cp_node"
        uint "$cp_actual" && echo "$cp_actual" > "$cp_written"
      else cp_result=write_failed; fi
    fi
    read_into cp_actual "$cp_node"
    if [ "$cp_result" = applied ] && [ "$cp_actual" != "$cp_freq" ]; then
      if uint "$cp_actual" && [ "$cp_actual" -lt "$cp_freq" ]; then cp_result=limited; else cp_result=conflict; fi
    fi
    record_control "$cp_name" "$cp_freq" "${cp_actual:-unknown}" "$cp_result"
  done
  [ "$cp_count" -gt 0 ] || record_control cpu 0 unknown unsupported
}

# GPU frequency controls this phone offers, read only (owner 2026-10-24: a GPU limit for games comes
# once these nodes are proven on the phone). Nothing here is written. JSON:
#   {"devfreq":[{"name","cur","max","min","steps","writable"}],"ged":{"cur","upbound","levels"},"gpufreqv2":0|1}
gpu_num() {   # first number on the first line of a node, or the fallback
  gn_value=$(read_node "$1" | sed -n 's/^[^0-9-]*\(-\{0,1\}[0-9][0-9]*\).*/\1/p')
  printf '%s' "${gn_value:-$2}"
}
gpu_json() {
  printf '{"devfreq":['
  gj_sep=""
  for gj_dev in "$CP_SYS"/class/devfreq/*; do
    [ -r "$gj_dev/max_freq" ] || continue
    case "${gj_dev##*/}" in *mali*|*gpu*|*GPU*|*13000000*) ;; *) continue ;; esac
    gj_steps=$(wc -w < "$gj_dev/available_frequencies" 2>/dev/null)
    printf '%s{"name":"%s","cur":%d,"max":%d,"min":%d,"steps":%d,"writable":%d}' "$gj_sep" "${gj_dev##*/}" \
      "$(gpu_num "$gj_dev/cur_freq" 0)" "$(gpu_num "$gj_dev/max_freq" 0)" "$(gpu_num "$gj_dev/min_freq" 0)" \
      "${gj_steps:-0}" "$([ -w "$gj_dev/max_freq" ] && echo 1 || echo 0)"
    gj_sep=","
  done
  gj_ged=$CP_SYS/kernel/ged/hal
  printf '],"ged":{"cur":%d,"upbound":%d,"levels":%d},"gpufreqv2":%d}' "$(gpu_num "$gj_ged/current_freqency" -1)" \
    "$(gpu_num "$gj_ged/custom_upbound_gpu_freq" -1)" "$(gpu_num "$gj_ged/total_gpu_freq_level_count" -1)" \
    "$([ -d "$CP_PROC/gpufreqv2" ] && echo 1 || echo 0)"
}

native_cpu_cooling() {
  for cp_dev in "$CP_SYS"/class/thermal/cooling_device*; do
    [ -r "$cp_dev/type" ] && [ -r "$cp_dev/cur_state" ] || continue
    read -r cp_kind < "$cp_dev/type"
    case "$cp_kind" in *cpu*|*CPU*) ;; *) continue ;; esac
    read -r cp_cstate < "$cp_dev/cur_state"
    uint "$cp_cstate" && [ "$cp_cstate" -gt 0 ] && return 0
  done
  return 1
}

set_boost() {
  cp_node=$CP_CPUCTL/top-app/cpu.uclamp.min
  [ -f "$cp_node" ] || { [ "$1" = 1 ] && record_control uclamp 20 unknown unsupported; return 0; }
  [ "$1" = 1 ] || [ -f "$CP_RUN/uclamp.orig" ] || return 0   # off and never written: nothing to do
  read_into cp_current "$cp_node"
  if [ "$1" = 1 ]; then
    if ! printf '%s\n' "$cp_current" | grep -Eq '^[0-9]+([.][0-9]+)?$'; then
      record_control uclamp 20 unknown unsupported; return 0
    fi
    if awk -v n="$cp_current" 'BEGIN {exit !(n > 20)}'; then
      record_control uclamp 20 "$cp_current" applied; return 0
    fi
    [ -f "$CP_RUN/uclamp.orig" ] || printf '%s\n' "$cp_current" > "$CP_RUN/uclamp.orig"
    cp_result=applied
    if [ "$cp_current" != 20 ] && [ "$cp_current" != 20.00 ]; then
      if [ -f "$CP_RUN/uclamp.written" ] && [ "$FORCE" = 0 ]; then cp_result=conflict
      elif (echo 20 > "$cp_node") 2>/dev/null; then : > "$CP_RUN/uclamp.written"
      else cp_result=write_failed; fi
    fi
    cp_actual=$(cat "$cp_node" 2>/dev/null)
    case "$cp_actual" in 20|20.00) ;; *) [ "$cp_result" = applied ] && cp_result=conflict ;; esac
    record_control uclamp 20 "${cp_actual:-unknown}" "$cp_result"
  elif [ -f "$CP_RUN/uclamp.orig" ]; then
    case "$cp_current" in
      20|20.00) (cat "$CP_RUN/uclamp.orig" > "$cp_node") 2>/dev/null || return 1 ;;
    esac
    rm -f "$CP_RUN/uclamp.orig" "$CP_RUN/uclamp.written"
  fi
}

# Refuse arbitrary paths from a damaged/edited switch file. No bypass/power-path nodes.
read_switch() {
  IFS='|' read -r sw_rel SW_ON SW_OFF < "$CP_DATA/switch" 2>/dev/null || return 1
  printf '%s\n' "$SWITCHES" | grep -Fxq "$sw_rel|$SW_ON|$SW_OFF" || return 1
  case "$sw_rel" in ''|*..*|/*|proc/*|*bypass*|*power_path*) return 1 ;; esac
  SW_NODE=$(switch_node "$sw_rel")
  [ -f "$SW_NODE" ]
}

charge_set() {
  read_switch || return 1
  if [ "$1" = on ]; then cp_value=$SW_ON; else cp_value=$SW_OFF; fi
  cp_before=$(cat "$SW_NODE" 2>/dev/null)
  if [ "$1" = off ] && [ ! -f "$CP_RUN/charge.owned" ]; then
    [ "$cp_before" = "$SW_ON" ] || return 1
    printf '%s|%s|%s\n' "$sw_rel" "$cp_before" "$SW_OFF" > "$CP_RUN/charge.owned"
  fi
  if ! (printf '%s\n' "$cp_value" > "$SW_NODE") 2>/dev/null; then
    [ -f "$CP_RUN/apply.tsv.tmp" ] && record_control charging "$cp_value" "$cp_before" write_failed
    return 1
  fi
  cp_after=$(cat "$SW_NODE" 2>/dev/null)
  if [ "$cp_after" != "$cp_value" ]; then
    [ -f "$CP_RUN/apply.tsv.tmp" ] && record_control charging "$cp_value" "$cp_after" conflict
    return 1
  fi
  [ -f "$CP_RUN/apply.tsv.tmp" ] && record_control charging "$cp_value" "$cp_after" applied
  [ "$1" = on ] && rm -f "$CP_RUN/charge.owned"
  return 0
}

restore_charge() {
  [ -f "$CP_RUN/charge.owned" ] || return 0
  IFS='|' read -r cp_rel cp_orig cp_off < "$CP_RUN/charge.owned"
  read_switch || return 1
  [ "$cp_rel" = "$sw_rel" ] || return 1
  if [ "$(cat "$SW_NODE" 2>/dev/null)" = "$cp_off" ]; then
    (printf '%s\n' "$cp_orig" > "$SW_NODE") 2>/dev/null || { event 'Pemulihan saklar cas gagal'; return 1; }
    [ "$(cat "$SW_NODE" 2>/dev/null)" = "$cp_orig" ] || return 1
  fi
  rm -f "$CP_RUN/charge.owned"
}

restore_probe() {
  [ -f "$CP_RUN/probe" ] || return 0
  IFS='|' read -r cp_pr cp_on cp_off < "$CP_RUN/probe"
  printf '%s\n' "$SWITCHES" | grep -Fxq "$cp_pr|$cp_on|$cp_off" || return 1
  cp_pnode=$(switch_node "$cp_pr")
  if [ "$(cat "$cp_pnode" 2>/dev/null)" = "$cp_off" ]; then
    (echo "$cp_on" > "$cp_pnode") 2>/dev/null || return 1
    [ "$(cat "$cp_pnode" 2>/dev/null)" = "$cp_on" ] || return 1
  fi
  rm -f "$CP_RUN/probe"
}

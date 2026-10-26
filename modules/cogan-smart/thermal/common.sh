# Cogan Smart Kernel, thermal part: shared paths, settings and sensor readers.
# POSIX sh (Android mksh, KernelSU busybox sh). Only reads the system; never writes to /sys.
# The CT_* paths can be overridden, which the offline tests use with a fake /sys and /proc.

MODDIR=${MODDIR:-${0%/*}}
MODROOT=${MODROOT:-$(cd "$MODDIR/.." && pwd)}   # the Cogan Smart Kernel module folder
CT_DATA=${CT_DATA:-/data/adb/cogan_smart/thermal}
CT_SYS=${CT_SYS:-/sys}
CT_PROC=${CT_PROC:-/proc}
CT_OUT=${CT_OUT:-/sdcard/Download/CoganThermal}
CT_CPUSET=${CT_CPUSET:-/dev/cpuset}
CP_DATA=${CP_DATA:-/data/adb/cogan_smart/power}
CP_MOD=${CP_MOD:-$MODROOT}   # the power part lives in the same module
CT_RUN=$CT_DATA/run
CONFIG=$CT_DATA/config

# Settings (WebUI writes $CONFIG; only these keys and plain numbers are accepted).
INTERVAL=20
RETENTION_DAYS=7
HOT_TEMP=41       # "hot" = phone body (Badan HP) at or above this (°C), owner 2026-10-24
NOTIFY=0
NOTIFY_TEMP=45    # optional notification, also on the phone body
AUTOSTART=1
CFG_VER=2         # 2 = HOT_TEMP of 24 Oct 2026; an older saved HOT_TEMP (processor, or 42) is replaced
. "$MODROOT/bridge.sh"

defaults() { INTERVAL=20; RETENTION_DAYS=7; HOT_TEMP=41; NOTIFY=0; NOTIFY_TEMP=45; AUTOSTART=1; CFG_VER=2; }

load_config() {
  defaults
  [ -f "$CONFIG" ] || return 0
  CFG_VER=0
  while IFS='=' read -r key value; do
    uint "$value" || continue
    case "$key" in
      INTERVAL) [ "$value" -ge 10 ] && [ "$value" -le 300 ] && INTERVAL=$value ;;
      RETENTION_DAYS) [ "$value" -ge 1 ] && [ "$value" -le 30 ] && RETENTION_DAYS=$value ;;
      HOT_TEMP) [ "$value" -ge 35 ] && [ "$value" -le 50 ] && HOT_TEMP=$value ;;
      NOTIFY) [ "$value" -le 1 ] && NOTIFY=$value ;;
      NOTIFY_TEMP) [ "$value" -ge 38 ] && [ "$value" -le 55 ] && NOTIFY_TEMP=$value ;;
      AUTOSTART) [ "$value" -le 1 ] && AUTOSTART=$value ;;
      CFG_VER) CFG_VER=$value ;;
    esac
  done < "$CONFIG"
  if [ "$CFG_VER" != 2 ]; then HOT_TEMP=41; CFG_VER=2; fi
}

write_config() {
  mkdir -p "$CT_DATA" || return 1
  [ ! -d "$CONFIG" ] && [ ! -L "$CONFIG" ] || return 1
  {
    echo "INTERVAL=$INTERVAL"
    echo "RETENTION_DAYS=$RETENTION_DAYS"
    echo "HOT_TEMP=$HOT_TEMP"
    echo "NOTIFY=$NOTIFY"
    echo "NOTIFY_TEMP=$NOTIFY_TEMP"
    echo "AUTOSTART=$AUTOSTART"
    echo "CFG_VER=$CFG_VER"
  } > "$CONFIG.tmp.$$" && mv "$CONFIG.tmp.$$" "$CONFIG" || return 1
  chmod 600 "$CONFIG"
}

# The readers below set variables with shell builtins instead of printing: the sampler runs every
# 20 seconds, and on the owner's phone its processes (cat for every network interface, awk, sed...)
# cost more CPU than most apps (v2.9.1 log, 4.8% of the phone together with the controller).

# Every thermal zone as "type=tenths_of_degC", comma separated, one value per type (the highest): zones;
# and the phone body (Badan HP, tenths of °C, -9999 without a sensor): body_t.
read_zones() {
  zones=$(read_thermal_sensors); body_t=${zones##*	}; zones=${zones#*	}; zones=${zones%%	*}
}

# Battery: charging (1/0), current (mA, a positive number) and battery (tenths of °C).
read_battery() {
  bat=$CT_SYS/class/power_supply/battery
  read_into status "$bat/status"; read_into current "$bat/current_now"; read_into battery "$bat/temp"
  case "$status" in Charging) charging=1 ;; *) charging=0 ;; esac
  case "$current" in ''|*[!0-9-]*) current=0 ;; esac
  case "$battery" in ''|*[!0-9-]*) battery=-999 ;; esac
  current=${current#-}
  # The kernel ABI says microamps (most phones); a few report milliamps. A design capacity in
  # microamp-hours (e.g. 5000000) means microamps too, so a small charging current stays right.
  read_into design "$bat/charge_full_design"
  case "$design" in ''|*[!0-9]*) design=0 ;; esac
  if [ "$current" -ge 20000 ] || [ "$design" -ge 100000 ]; then current=$((current / 1000)); fi
}

# GPU load in percent, or -1 when the kernel does not expose it: gpu.
read_gpu() {
  gpu=-1
  for node in "$CT_SYS/kernel/ged/hal/gpu_utilization" "$CT_SYS/class/kgsl/kgsl-3d0/gpu_busy_percentage" \
              "$CT_SYS/class/misc/mali0/device/utilization" "$CT_SYS/kernel/gpu/gpu_busy"; do
    [ -r "$node" ] || continue
    value=""; read -r value _ 2>/dev/null < "$node" || :           # the first number, e.g. "65 0 0" or "65%"
    value=${value#"${value%%[0-9]*}"}; value=${value%%[!0-9]*}
    uint "$value" || continue
    [ "$value" -le 100 ] && { gpu=$value; return; }
  done
}

# Screen: 1 on, 0 off, -1 unknown. The panel backlight needs no dumpsys call; Android's own
# screen state is the fallback.
bounded_dumpsys() {
  if command -v timeout >/dev/null 2>&1; then timeout 2 dumpsys "$@"
  else dumpsys "$@"; fi
}

read_screen() {   # sets screen
  for node in "$CT_SYS"/class/leds/lcd-backlight/brightness "$CT_SYS"/class/backlight/*/brightness; do
    [ -r "$node" ] || continue
    read_into value "$node"
    uint "$value" || continue
    if [ "$value" -gt 0 ]; then screen=1; else screen=0; fi
    return
  done
  case "$(bounded_dumpsys deviceidle get screen 2>/dev/null)" in
    true*) screen=1 ;;
    false*) screen=0 ;;
    *) screen=-1 ;;
  esac
}

# Foreground app package from the focused window or app ("-" when unknown). The short
# "displays" section is enough on Android 10+; the full dump is the fallback.
focus_pkg() {
  sed -n -e 's#.*mCurrentFocus=.* u[0-9]* \([A-Za-z0-9_.]*\)/.*#\1#p' \
         -e 's#.*mFocusedApp=.* u[0-9]* \([A-Za-z0-9_.]*\)/.*#\1#p' | head -n 1
}
# The focused app only changes when the processes in Android's top-app cpuset change, so dumpsys
# (which also costs system_server work) runs only then, after the screen was off, and at least every
# 6th sample; the cpuset is read with shell builtins. Without that cpuset, dumpsys runs every sample.
read_foreground() {   # sets app
  fg_set=""
  while IFS= read -r fg_pid; do fg_set="$fg_set $fg_pid"; done 2>/dev/null < "$CT_CPUSET/top-app/cgroup.procs"
  fg_age=$((${fg_age:-0} + 1))
  if [ -n "$fg_set" ] && [ "$fg_set" = "${FG_SET-}" ] && [ "$fg_age" -lt 6 ]; then app=$FG_APP; return; fi
  pkg=$(bounded_dumpsys window displays 2>/dev/null | focus_pkg)
  [ -n "$pkg" ] || pkg=$(bounded_dumpsys window 2>/dev/null | focus_pkg)
  app=${pkg:--}
  FG_SET=$fg_set; FG_APP=$app; fg_age=0
  [ -n "$pkg" ] || FG_SET=""   # unknown: ask again next time
}

# CPU frequency per policy in MHz: freqs = "p0:1800,p4:2850".
read_freqs() {
  freqs=""
  for policy in "$CT_SYS"/devices/system/cpu/cpufreq/policy*; do
    read_into khz "$policy/scaling_cur_freq"
    case "$khz" in ''|*[!0-9]*) continue ;; esac
    freqs="$freqs${freqs:+,}p${policy##*policy}:$((khz / 1000))"
  done
  freqs=${freqs:--}
}

# Bytes moved on Wi-Fi and cellular interfaces: wifi and cell. Other interfaces are not read at all
# (a MediaTek phone has 20+ of them, mostly idle ccmni and tunnel devices).
read_net_bytes() {
  wifi=0; cell=0
  for dev in "$CT_SYS"/class/net/*; do
    name=${dev##*/}
    case "$name" in wlan*|ccmni*|rmnet*|seth*|ccemni*|ccinet*) ;; *) continue ;; esac
    read_into rx "$dev/statistics/rx_bytes"; read_into tx "$dev/statistics/tx_bytes"
    case "$rx" in ''|*[!0-9]*) continue ;; esac
    case "$tx" in ''|*[!0-9]*) continue ;; esac
    case "$name" in wlan*) wifi=$((wifi + rx + tx)) ;; *) cell=$((cell + rx + tx)) ;; esac
  done
}

# Process name for a pid: the first word of its command line, e.g. "com.instagram.android".
# The sampler remembers names by pid and start time, so this runs only for a process new in its top 5.
proc_name() {
  name=$(tr '\0' '\n' < "$CT_PROC/$1/cmdline" 2>/dev/null | head -n 1)
  name=${name##*/}; name=${name%%:*}
  [ -n "$name" ] || name=$2
  echo "$name" | sed 's/[^A-Za-z0-9_.+-]/_/g'
}

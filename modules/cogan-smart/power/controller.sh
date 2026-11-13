#!/system/bin/sh
# Cogan Smart · Power: the control loop. Every INTERVAL seconds it reads the phone body (Badan HP)
# and processor temperatures, the battery and the latest report of Cogan Smart · Thermal (what heats
# the phone), then:
#
#   CPU     Hemat caps the big cores at SAVER_CAP %; Kernel Default (seimbang, TARGET_TEMP) and Hemat
#           (2 °C lower) lower the CPU top speed in small steps while the phone body is too warm and give
#           it back when it is cool again; Performa (game) runs free and only steps in at GAME_LIMIT.
#           Kernel Default and Performa keep the big cores at 60 % or more and touch the little cores
#           last (level_caps). The CPU only steps down while the processor works (CPU_WORK); with an
#           idle processor the steps are given back. Every mode brakes when the processor reaches CPU_BRAKE.
#           While a social or video app is on screen (not in Performa) the big cores stay at SOCIAL_CAP %
#           or lower from the first check.
#   Charge  stops at CHARGE_STOP % and resumes at CHARGE_RESUME %. Charging heat is managed by the
#           phone (HyperCharge) by default; CHARGE_THERMAL=1 adds the module's own heat pauses.
#
# Usage: controller.sh [--once]

MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.   # started as "sh controller.sh"
. "$MODDIR/common.sh"
leave_app_cgroup

# state VAR NAME DEFAULT: a value kept in $CP_RUN between checks into VAR (DEFAULT when missing).
# Shell builtins only: the controller runs every 10 seconds, and each process it starts costs CPU.
state() { if [ -f "$CP_RUN/$2" ]; then read_into "$1" "$CP_RUN/$2"; else eval "$1=\$3"; fi; }

# Big and little core caps (%) of a step level, as LC_BIG and LC_LITTLE. Owner 2026-10-24, "as smooth
# as possible": Kernel Default and Performa lower the big cores (X4 on rothko) 10 % per step down to
# 60 %, then the little cores (A720, which keep the interface fluid) to 90 % and 80 %. Hemat goes on
# down from its own cap, as before.
level_caps() {
  if [ "$MODE" = hemat ]; then
    LC_BIG=$((SAVER_CAP - $1 * 10)); [ "$LC_BIG" -lt 20 ] && LC_BIG=20
    LC_LITTLE=$((LC_BIG + 20)); [ "$LC_LITTLE" -gt 100 ] && LC_LITTLE=100
    return
  fi
  case "$1" in
    0) LC_BIG=100; LC_LITTLE=100 ;; 1) LC_BIG=90; LC_LITTLE=100 ;; 2) LC_BIG=80; LC_LITTLE=100 ;;
    3) LC_BIG=70; LC_LITTLE=100 ;; 4) LC_BIG=60; LC_LITTLE=100 ;; 5) LC_BIG=60; LC_LITTLE=90 ;;
    *) LC_BIG=60; LC_LITTLE=80 ;;
  esac
}

step() {
  lock_take "$CP_RUN/step.lock" || return 1
  : > "$CP_RUN/apply.tsv.tmp"
  read_into step_request "$CP_RUN/apply.request"
  # Paksa (report.sh apply) forces the check that serves its request only; FORCE=1 repeats it every check.
  step_force=$FORCE; read_into step_done "$CP_RUN/applied.request"
  [ -n "$step_request" ] && [ "$step_request" != "$step_done" ] && FORCE=1
  heartbeat power
  now=$(date +%s); CB_NOW=$now
  read_temps; main=$MAIN_T; body=$BODY_T
  battery_now; level_pct=$level; btemp=$temp   # status and current as they are
  # Without a phone body sensor, the battery is the closest to what a hand feels.
  [ "$body" -gt -9999 ] || { [ "$btemp" -gt -999 ] && body=$btemp; }

  # What heats the phone: Cogan Smart · Thermal's report, or a simple guess without it.
  if read_monitor; then
    source=monitor; cause=$M_CAUSE; app=$M_APP
  else
    source=sensor; app=""; cause=""
    [ "$status" = charging ] && [ "$current" -ge 1500 ] && cause="Cas cepat"
  fi

  # A new mode starts from full speed.
  state st_mode mode ""
  if [ "$st_mode" != "$MODE" ]; then
    [ -n "$st_mode" ] && event "Mode: $(mode_label "$MODE")"
    echo "$MODE" > "$CP_RUN/mode"
    log_mode "$MODE"
    rm -f "$CP_RUN/level" "$CP_RUN/cool" "$CP_RUN/hold"
  fi

  # Charging first: when the monitor says charging is the heat source, pausing it may be enough.
  charge_step

  # CPU: the phone body warms and cools slowly, so one step down while it is warm and not cooling, then
  # three checks to see what that step did. From 1 °C under the limit only the first two (gentle) steps
  # are taken, at the limit all of them. Only while the processor works (CPU_WORK): heat from charging,
  # the room or an idle phone is not cooled by a lower CPU cap, and a cap kept from then would only slow
  # the next use. One step back up after three checks at least 1.5 °C under the limit, or with an idle
  # processor once the phone body is under the step zone (1 °C under the limit). The processor brake steps down at every check. While charging was just paused for heat,
  # that pause gets its three checks first.
  case "$MODE" in
    hemat) limit=$((TARGET_TEMP - 2)) ;;
    game) limit=$GAME_LIMIT ;;
    *) limit=$TARGET_TEMP ;;
  esac
  state step_level level 0; state cool cool 0; state hold hold 0; state prev prev "$body"
  old_level=$step_level
  native_cooling=0; native_cpu_cooling && native_cooling=1
  [ "$hold" -gt 0 ] && hold=$((hold - 1))
  [ "$paused_for_heat" = 1 ] && hold=3
  brake=0; [ "$main" -ge $((CPU_BRAKE * 10)) ] && brake=1
  # "busy" is the processor temperature at CPU_WORK or above, not measured CPU use (audit 7 Nov): heat left
  # after a game keeps it 1 for a while, and a load that just started counts once the processor warms.
  busy=0; [ "$main" -ge $((CPU_WORK * 10)) ] && busy=1
  if [ "$brake" = 1 ]; then
    cool=0
    [ "$step_level" -lt 6 ] && { step_level=$((step_level + 1)); hold=3; }
  elif [ "$busy" = 1 ] && [ "$body" -gt -9999 ] && [ "$body" -ge $(((limit - 1) * 10)) ]; then
    cool=0
    room=6; [ "$body" -lt $((limit * 10)) ] && room=2
    if [ "$hold" = 0 ] && [ "$body" -ge $((prev - 2)) ] && [ "$step_level" -lt "$room" ]; then
      step_level=$((step_level + 1)); hold=3
    fi
  # Given back with a cool processor only once the phone body is under the step zone (owner 13 Nov 2026, Instagram
  # at 09.16-09.25: the processor sat at 51-55 °C, so the cap was released and lowered again every half minute while
  # the phone body stayed at 40.5-41.4 °C, over Hemat's 39 °C). Without a body sensor body is -9999: as before.
  elif { { [ "$busy" = 0 ] && [ "$body" -lt $(((limit - 1) * 10)) ]; } || [ "$body" -le $(((limit - 1) * 10 - 5)) ]; } &&
       [ "$main" -lt $(((CPU_BRAKE - 5) * 10)) ] && [ "$step_level" -gt 0 ]; then
    cool=$((cool + 1))
    [ "$cool" -ge 3 ] && { step_level=$((step_level - 1)); cool=0; }
  else
    cool=0
  fi
  echo "$step_level" > "$CP_RUN/level"; echo "$cool" > "$CP_RUN/cool"; echo "$hold" > "$CP_RUN/hold"; echo "$body" > "$CP_RUN/prev"
  level_caps "$step_level"; big=$LC_BIG; little=$LC_LITTLE
  # SosMed (owner 2026-11-13): scrolling a feed or watching video does not need the big cores at top speed,
  # and the heat steps above only start once the phone body is already warm. While a social or video app is
  # on screen, the big cores stay at SOCIAL_CAP % or lower from the first check, whatever the temperature;
  # the little cores, which keep the interface fluid, stay as the heat steps set them. Not in Performa.
  social=0
  if [ "$MODE" != game ] && [ "$SOCIAL_CAP" -gt 0 ] && is_social "$M_PKG"; then
    social=1; [ "$big" -gt "$SOCIAL_CAP" ] && big=$SOCIAL_CAP
  fi
  state was_social social 0
  if [ "$social" != "$was_social" ]; then
    echo "$social" > "$CP_RUN/social"
    if [ "$social" = 1 ]; then event "SosMed di layar (${app:-$M_PKG}): CPU besar maks $SOCIAL_CAP%, CPU kecil $little%"
    else event "Batas SosMed dilepas: CPU besar $big%, kecil $little%"; fi
  fi
  set_cpu_cap "$big" "$little"
  if [ "$step_level" -gt "$old_level" ] && [ "$brake" = 1 ]; then
    event "Rem darurat: prosesor $(deg "$main") °C ≥ $CPU_BRAKE °C: CPU besar $big%, kecil $little%"
  elif [ "$step_level" -gt "$old_level" ]; then
    event "Badan HP $(deg "$body") °C (batas $limit °C)${cause:+ ($cause)}: CPU besar $big%, kecil $little%"
  elif [ "$step_level" -lt "$old_level" ]; then
    # A step is given back when the phone body is well under the limit, or when the processor is under CPU_WORK
    # while the body may still be warm (audit 7 Nov 2026: "turun" was written even when the body had not cooled).
    if [ "$body" -gt -9999 ] && [ "$body" -le $(((limit - 1) * 10 - 5)) ]; then
      event "Badan HP $(deg "$body") °C, di bawah batas $limit °C: CPU besar $big%, kecil $little%"
    else
      event "Prosesor $(deg "$main") °C, di bawah $CPU_WORK °C: batas dilepas, CPU besar $big%, kecil $little%"
    fi
  fi
  if [ "$MODE" = game ] && [ "$GAME_BOOST" = 1 ]; then set_boost 1; else set_boost 0; fi
  FORCE=$step_force
  write_state
  mv "$CP_RUN/apply.tsv.tmp" "$CP_RUN/apply.tsv"
  printf '%s\n' "$step_request" > "$CP_RUN/applied.request"
  lock_drop "$CP_RUN/step.lock"
}

charge_step() {
  paused_for_heat=0
  [ -f "$CP_RUN/detecting" ] && return 0   # the WebUI is testing switches right now
  state was charge_off ""
  reasons=""
  if [ "$CHARGE_CTRL" = 1 ] && [ "$level_pct" -ge 0 ]; then
    case " $was " in
      *" batas "*) [ "$level_pct" -gt "$CHARGE_RESUME" ] && reasons="batas" ;;
      *) [ "$CHARGE_STOP" -lt 100 ] && [ "$level_pct" -ge "$CHARGE_STOP" ] && { [ "$status" = charging ] || [ "$status" = full ]; } && reasons="batas" ;;
    esac
    # Module heat pauses (CHARGE_THERMAL=1, off by default) only switch charging off and on; no thermal
    # driver, OEM charging limit, or charger negotiation setting is changed.
    if [ "$CHARGE_THERMAL" = 1 ]; then
      case " $was " in
        *" baterai "*) [ "$btemp" -gt $(((BATT_TEMP_STOP - 3) * 10)) ] && reasons="$reasons baterai" ;;
        *) [ "$btemp" -ge $((BATT_TEMP_STOP * 10)) ] && [ "$status" = charging ] && reasons="$reasons baterai" ;;
      esac
      if [ "$MODE" = seimbang ] && [ "$HEAT_PAUSE_CHARGE" = 1 ]; then
        case " $was " in
          *" panas "*) [ "$body" -gt $(((TARGET_TEMP - 3) * 10)) ] && reasons="$reasons panas" ;;
          *) [ "$status" = charging ] && [ "$body" -ge $((TARGET_TEMP * 10)) ] && case "$cause" in "Cas cepat"|Mengecas*) reasons="$reasons panas" ;; esac ;;
        esac
      fi
    fi
    [ "$level_pct" -le 15 ] && reasons=""   # a nearly empty battery always charges
  fi
  reasons=${reasons# }

  if [ "$reasons" = "$was" ]; then
    # Some chargers turn charging back on after a replug: switch it off again.
    [ -n "$reasons" ] && [ "$status" = charging ] && charge_set off
    return 0
  fi
  if [ -z "$reasons" ]; then
    restore_charge || { record_control charging on unknown write_failed; return 0; }
    rm -f "$CP_RUN/charge_off"
    event "Cas dilanjutkan (baterai $level_pct%, $(deg "$btemp") °C)"
    return 0
  fi
  if ! read_switch; then
    # Finding the switch needs the phone to be charging right now; try once per start.
    [ -f "$CP_RUN/no_switch" ] || [ "$status" != charging ] && return 0
    event "Mencari saklar cas…"
    if detect_switch > "$CP_RUN/detect.log"; then
      event "Saklar cas ditemukan: $(cut -d '|' -f 1 "$CP_DATA/switch")"
    else
      : > "$CP_RUN/no_switch"
      event "Saklar cas tidak ditemukan di HP ini: auto cut charging tidak bisa dipakai"
      return 0
    fi
  fi
  if ! charge_set off; then
    record_control charging off unknown write_failed
    event 'Saklar cas belum menerima perintah; status jeda tidak diklaim aktif'
    return 0
  fi
  echo "$reasons" > "$CP_RUN/charge_off"
  case " $was " in *" panas "*) ;; *) case " $reasons " in *" panas "*) paused_for_heat=1 ;; esac ;; esac
  case " $reasons " in
    *" panas "*) event "Badan HP $(deg "$body") °C karena cas: cas dijeda sampai $((TARGET_TEMP - 3)) °C" ;;
    *" baterai "*) event "Baterai $(deg "$btemp") °C: cas dijeda sampai $((BATT_TEMP_STOP - 3)) °C" ;;
    *) event "Baterai $level_pct%: cas dihentikan, lanjut di $CHARGE_RESUME%" ;;
  esac
}

# jstr VAR TEXT: TEXT without backslashes and double quotes into VAR (safe inside a JSON string).
jstr() {
  js_in=$2; js_out=""
  while :; do
    case "$js_in" in
      *[\\\"]*) js_head=${js_in%%[\\\"]*}; js_out=$js_out$js_head; js_in=${js_in#"$js_head"?} ;;
      *) break ;;
    esac
  done
  eval "$1=\$js_out\$js_in"
}

write_state() {
  state st_off charge_off ""; jstr st_cause "$cause"; jstr st_app "$app"
  st_boost=0; [ -f "$CP_RUN/uclamp.written" ] && st_boost=1
  printf '{"ts":%d,"mode":"%s","main":%d,"body":%d,"limit":%d,"brake":%d,"busy":%d,"level":%d,"big":%d,"little":%d,"battery":{"level":%d,"status":"%s","temp":%d,"current":%d},"charge_off":"%s","source":"%s","cause":"%s","app":"%s","boost":%d,"force":%d,"native_cooling":%d,"social":%d}\n' \
    "$now" "$MODE" "$main" "$body" "$limit" "$brake" "$busy" "$step_level" "$big" "$little" "$level_pct" "$status" "$btemp" "$current" \
    "$st_off" "$source" "$st_cause" "$st_app" "$st_boost" "$FORCE" "$native_cooling" "$social" \
    > "$CP_RUN/state.json.tmp" && mv "$CP_RUN/state.json.tmp" "$CP_RUN/state.json"
}

load_config
boot_session
if [ "$1" = "--once" ]; then
  trap 'lock_drop "$CP_RUN/step.lock"' EXIT
  step
  exit $?
fi

lock_take "$CP_RUN/daemon.lock" || exit 1
echo $$ > "$CP_RUN/pid"
rm -f "$CP_RUN/mode" "$CP_RUN/no_switch"
event "Cogan Smart · Power mulai: mode $(mode_label "$MODE")"
stop=0; sleeper=""
cleanup() {
  if restore; then event 'Cogan Smart · Power berhenti: kontrol milik modul dipulihkan'
  else event 'Cogan Smart · Power berhenti: ada pemulihan tertunda, periksa status'; fi
  log_mode none
  rm -f "$CP_RUN/pid" "$CP_RUN/mode"
  lock_drop "$CP_RUN/step.lock"
  lock_drop "$CP_RUN/daemon.lock"
}
trap cleanup EXIT
trap 'stop=1; [ -n "$sleeper" ] && kill "$sleeper" 2>/dev/null' TERM INT
trap '[ -n "$sleeper" ] && kill "$sleeper" 2>/dev/null' HUP   # new settings: check right away
count=0
while [ "$stop" = 0 ]; do
  [ -f "$MODROOT/disable" ] || [ -f "$MODROOT/remove" ] && break
  load_config
  step
  count=$((count + 1))
  [ "$stop" = 1 ] && break
  read_into want "$CP_RUN/apply.request"; read_into done_req "$CP_RUN/applied.request"
  [ "$want" != "$done_req" ] && continue
  if [ $((count % 360)) = 0 ] && [ "$(wc -l < "$EVENTS")" -gt 300 ]; then
    tail -n 200 "$EVENTS" > "$EVENTS.tmp" && mv "$EVENTS.tmp" "$EVENTS"
  fi
  sleep "$INTERVAL" &
  sleeper=$!
  wait "$sleeper"
  sleeper=""
done

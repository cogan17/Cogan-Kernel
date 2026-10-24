#!/system/bin/sh
# Cogan Smart · Power: the manager's Action button switches to the next mode (Hemat → Kernel Default → Performa).
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
. "$MODDIR/common.sh"
load_config
case "$MODE" in hemat) next=seimbang ;; seimbang) next=game ;; *) next=hemat ;; esac
sh "$MODDIR/report.sh" start > /dev/null 2>&1
sh "$MODDIR/report.sh" mode "$next" > /dev/null
case "$next" in
  hemat) echo "🌿 Mode Hemat: CPU besar maks $SAVER_CAP%, badan HP dijaga ≤ $((TARGET_TEMP - 2)) °C" ;;
  seimbang) echo "🧠 Mode Kernel Default: badan HP dijaga ≤ $TARGET_TEMP °C" ;;
  game) echo "🎮 Mode Performa: performa penuh, rem di badan HP $GAME_LIMIT °C" ;;
esac
if [ "$CHARGE_CTRL" = 1 ]; then
  echo "🔌 Auto cut charging: berhenti $CHARGE_STOP%, lanjut $CHARGE_RESUME%, jeda bila baterai ≥ $BATT_TEMP_STOP °C"
else
  echo "🔌 Auto cut charging: mati"
fi
echo "🛑 Semua mode: rem darurat bila prosesor ≥ $CPU_BRAKE °C"
echo
echo "Tekan Action lagi untuk mode berikutnya. Setelan lengkap ada di WebUI modul ini."

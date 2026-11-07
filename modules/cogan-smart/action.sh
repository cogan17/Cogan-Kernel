#!/system/bin/sh
# Cogan Smart Kernel: the manager's Action button switches to the next mode; the thermal log keeps running.
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
# What Action changed is shown in the manager (audit 7 Nov): the recorder (started when it was stopped) and the mode.
case "$(sh "$MODDIR/thermal/report.sh" start 2> /dev/null)" in
  *'"running":1'*) echo "📈 Pencatat suhu: aktif" ;;
  *) echo "📈 Pencatat suhu: gagal mulai" ;;
esac
exec sh "$MODDIR/power/action.sh"

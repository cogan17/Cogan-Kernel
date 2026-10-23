#!/system/bin/sh
# Cogan Smart Kernel: the manager's Action button switches to the next mode; the thermal log keeps running.
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
sh "$MODDIR/thermal/report.sh" start > /dev/null 2>&1
exec sh "$MODDIR/power/action.sh"

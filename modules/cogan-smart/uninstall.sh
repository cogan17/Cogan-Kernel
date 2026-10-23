#!/system/bin/sh
# Cogan Smart Kernel: put CPU speed and charging back, stop the log, remove settings, history and whitelist.
# Logs saved to Download stay with the user.
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
sh "$MODDIR/power/uninstall.sh"
sh "$MODDIR/thermal/uninstall.sh"
rm -rf "${CS_ADB:-/data/adb}/cogan_smart/guard"
rmdir "${CS_ADB:-/data/adb}/cogan_smart" 2>/dev/null
exit 0

#!/system/bin/sh
# Cogan Smart Kernel: start the thermal sampler and the power controller; each waits for boot itself.
# The module guard finishes removals the user asked for (data of modules the root manager deleted).
# Aplikasi keeps chat and social apps from installing APKs while its block is on.
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
sh "$MODDIR/guard/report.sh" boot > /dev/null 2>&1 &
sh "$MODDIR/thermal/service.sh" &
sh "$MODDIR/power/service.sh" &
sh "$MODDIR/apps/report.sh" boot > /dev/null 2>&1 &

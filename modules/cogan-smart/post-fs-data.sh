#!/system/bin/sh
# Best effort before Android initializes ZRAM; an already initialized device is never reset.
MODDIR=${0%/*}
sh "$MODDIR/manager/report.sh" early >/dev/null 2>&1

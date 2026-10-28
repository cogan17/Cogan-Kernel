#!/system/bin/sh
# Cogan Smart · Power: start the controller once Android has finished booting.
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
until [ "$(getprop sys.boot_completed)" = 1 ]; do sleep 5; done
. "$MODDIR/common.sh"
load_config
# Manager is one-shot after Android finishes boot; power may remain stopped independently.
sh "$MODROOT/manager/report.sh" boot >/dev/null 2>&1
boot_session
[ "$AUTOSTART" = 1 ] || exit 0
sleep 20        # let Cogan Smart · Thermal take its first sample
sh "$MODDIR/report.sh" start > /dev/null 2>&1

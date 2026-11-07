#!/system/bin/sh
# Cogan Smart · Aplikasi: while the block is on, chat and social apps lose the right to install APKs.
# Screen on: one appops query every 5 seconds. Screen off (panel backlight 0): no query, only the backlight is
# read, and the first pass runs as soon as the screen lights up; granting the right again needs the screen on.
# A query or revoke that keeps failing waits longer each time (10, 20, 40, then 60 s) instead of asking again
# every 5 s. The loop ends when the block is switched off or the module is disabled or removed in the manager.
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
. "$MODDIR/common.sh"
leave_app_cgroup
mkdir -p "$CA_RUN" && echo $$ > "$CA_RUN/block.pid"
ca_wait=${CA_SLEEP:-5}
while :; do
  [ -f "$MODROOT/disable" ] || [ -f "$MODROOT/remove" ] && break
  load_config
  [ "$BLOCK" = 1 ] || break
  # One worker: when two start at once, the PID written last owns the file and the other one leaves.
  read_into ca_owner "$CA_RUN/block.pid"; [ "$ca_owner" = $$ ] || exit 0
  screen_lit
  if [ "$CB_SCREEN" = 0 ]; then
    ca_wait=${CA_SLEEP:-5}   # a fresh start once the screen is back
  elif block_pass; then
    ca_wait=${CA_SLEEP:-5}
  else
    ca_wait=$((ca_wait * 2)); [ "$ca_wait" -le 60 ] || ca_wait=60
  fi
  sleep "$ca_wait"
done
read_into ca_owner "$CA_RUN/block.pid"; [ "$ca_owner" = $$ ] && rm -f "$CA_RUN/block.pid"

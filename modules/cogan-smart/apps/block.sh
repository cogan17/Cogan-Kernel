#!/system/bin/sh
# Cogan Smart · Aplikasi: while the block is on, chat and social apps lose the right to install APKs.
# One appops query every 5 seconds; the loop ends when the block is switched off.
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
. "$MODDIR/common.sh"
leave_app_cgroup
mkdir -p "$CA_RUN" && echo $$ > "$CA_RUN/block.pid"
while :; do
  load_config
  [ "$BLOCK" = 1 ] || break
  # One worker: when two start at once, the PID written last owns the file and the other one leaves.
  read_into ca_owner "$CA_RUN/block.pid"; [ "$ca_owner" = $$ ] || exit 0
  block_pass
  sleep "${CA_SLEEP:-5}"
done
read_into ca_owner "$CA_RUN/block.pid"; [ "$ca_owner" = $$ ] && rm -f "$CA_RUN/block.pid"

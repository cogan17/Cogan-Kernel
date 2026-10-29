#!/system/bin/sh
# Cogan Smart · Aplikasi: while the block is on, chat and social apps lose the right to install APKs.
# One appops query every 5 seconds; the loop ends when the block is switched off.
MODDIR=${0%/*}; [ "$MODDIR" = "$0" ] && MODDIR=.
. "$MODDIR/common.sh"
mkdir -p "$CA_RUN" && echo $$ > "$CA_RUN/block.pid"
while :; do
  load_config
  [ "$BLOCK" = 1 ] || break
  block_pass
  sleep "${CA_SLEEP:-5}"
done
rm -f "$CA_RUN/block.pid"

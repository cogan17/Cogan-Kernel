# Cogan Smart · Aplikasi: shared by report.sh and block.sh (sourced, MODDIR set by the caller).
MODROOT=$(cd "$MODDIR/.." && pwd)
. "$MODROOT/bridge.sh"
CA_DATA=${CA_DATA:-${CS_ADB:-/data/adb}/cogan_smart/apps}
CA_RUN=$CA_DATA/run
CA_ROOT=${CA_ROOT:-}   # the offline tests put /data under a temporary folder
# Chat, social, email and SMS apps whose "install unknown apps" right is taken back while the block is on
# (owner 2026-10-29: scam APKs arrive through WhatsApp and social media; email and SMS added the same day).
# Browsers and file managers keep it.
CA_SOURCES='com.whatsapp com.whatsapp.w4b org.telegram.messenger org.telegram.messenger.web org.thunderdog.challegram
org.telegram.plus org.thoughtcrime.securesms com.michatapp.im
com.facebook.katana com.facebook.lite com.facebook.orca com.facebook.mlite com.instagram.android com.instagram.lite
com.instagram.barcelona com.zhiliaoapp.musically com.zhiliaoapp.musically.go com.ss.android.ugc.trill com.twitter.android
jp.naver.line.android com.discord com.snapchat.android com.viber.voip com.imo.android.imoim com.tencent.mm com.kakao.talk
com.bsb.hike
com.google.android.gm com.microsoft.office.outlook com.android.email com.yahoo.mobile.client.android.mail
com.google.android.apps.messaging com.android.mms'
BLOCK=1

load_config() {
  BLOCK=1
  [ -f "$CA_DATA/config" ] || return 0
  while IFS='=' read -r ca_k ca_v; do
    case "$ca_k:$ca_v" in BLOCK:0|BLOCK:1) BLOCK=$ca_v ;; esac
  done < "$CA_DATA/config"
}
CA_SOURCES=$(echo $CA_SOURCES)   # one line, single spaces
is_source() { case " $CA_SOURCES " in *" $1 "*) return 0 ;; esac; return 1; }
users() { pm list users 2>/dev/null | sed -n 's/.*UserInfo{\([0-9][0-9]*\):.*/\1/p'; }
block_pid() { safe_pid "$CA_RUN/block.pid" "$MODDIR/block.sh"; }

notify() {   # notify TEXT
  cmd notification post -S bigtext -t "🛡️ Cogan Smart" cogan_apps "$1" > /dev/null 2>&1 \
    || su 2000 -c "cmd notification post -S bigtext -t 'Cogan Smart' cogan_apps '$1'" > /dev/null 2>&1
}

# Back to Android's default for this op: a chat app cannot install an APK unless the user allows it again,
# and the block takes that back within seconds.
# Read back: Android lists the package again while any user still allows it. A failure is logged and shown once,
# not every 5 seconds. Switching the block off gives nothing back; the user allows an app again in Settings.
block_source() {   # block_source PKG
  ca_users=$(users)
  for ca_u in $ca_users; do cmd appops set --user "$ca_u" "$1" REQUEST_INSTALL_PACKAGES default > /dev/null 2>&1; done
  if [ -n "$ca_users" ] && ! cmd appops query-op REQUEST_INSTALL_PACKAGES allow 2> /dev/null | grep -Fxq "$1"; then
    ca_ok=1; rm -f "$CA_RUN/failed.$1"
  else
    ca_ok=0; [ -f "$CA_RUN/failed.$1" ] && return 1
    mkdir -p "$CA_RUN" && : > "$CA_RUN/failed.$1"
  fi
  mkdir -p "$CA_DATA" && printf '%s %s %s\n' "$(date +%s)" "$1" "$ca_ok" >> "$CA_DATA/blocked.log"
  tail -n 20 "$CA_DATA/blocked.log" > "$CA_DATA/blocked.tmp" && mv -f "$CA_DATA/blocked.tmp" "$CA_DATA/blocked.log"
  if [ "$ca_ok" = 1 ]; then notify "Izin memasang aplikasi dari $1 dicabut. Jangan pasang APK kiriman chat, sosmed, email atau SMS."
  else notify "Izin memasang aplikasi dari $1 GAGAL dicabut. Cabut sendiri di Pengaturan, Instal aplikasi tak dikenal."; fi
  [ "$ca_ok" = 1 ]
}
block_pass() {
  for ca_p in $(cmd appops query-op REQUEST_INSTALL_PACKAGES allow 2>/dev/null); do
    is_source "$ca_p" && block_source "$ca_p"
  done
}

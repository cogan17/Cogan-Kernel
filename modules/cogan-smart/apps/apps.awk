# Cogan Smart · Aplikasi: one JSON report from Android's own dumps (formats as in AOSP main, 2026-10):
#   list      pm list packages -3 --user U          package:NAME
#   packages  dumpsys package packages              Package [NAME], appId=, installerPackageName=,
#             initiatingPackageName=, packageSource=, User N: ... firstInstallTime=, PERM: granted=true
#   usage     dumpsys usagestats -c                 user=N, package=NAME lastTimeUsed=MS ...
#   appops    dumpsys appops                        Uid uNaM: / Package NAME: / OP (mode): / Access: ... (-1h2m3s)
#   admins    dumpsys device_policy                 Enabled Device Admins (User N ...): / NAME/CLASS:
#   launcher  cmd package query-activities --components (MAIN/LAUNCHER)   NAME/CLASS
#   battery   dumpsys batterystats --usage          UID uNaM: MAH ( ...   since the last full charge
#   net       dumpsys netstats --uid --full         UID stats: / ident=[..] uid=N set= / st=S rb=B .. tb=B
#   running   ps -A -w -o args;  a11y, notif: settings secure values (NAME/CLASS:NAME/CLASS)
#   trusted   the whitelist;  events: "EPOCH NAME" of chat/social/email/SMS apps whose install right was taken back
# A missing dump leaves its column unknown (-1 / absent), never "nothing found".
function pkg_ok(p) { return p ~ /^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$/ }
function value(s) { sub(/^[^=]*=/, "", s); sub(/[ \t\r].*$/, "", s); return s == "null" ? "" : s }
function save_install() { if (pkg != "") installed[pkg] = own_date != "" ? own_date : (user == 0 ? global_date : "") }
function age(s,   t, n) {   # "-1d2h3m4s5ms" -> seconds
  sub(/^[-+]/, "", s); t = 0
  while (match(s, /^[0-9]+/)) {
    n = substr(s, 1, RLENGTH) + 0; s = substr(s, RLENGTH + 1)
    if (substr(s, 1, 2) == "ms") { t += n / 1000; s = substr(s, 3); continue }
    u = substr(s, 1, 1); s = substr(s, 2)
    t += u == "d" ? n * 86400 : u == "h" ? n * 3600 : u == "m" ? n * 60 : n
  }
  return int(t)
}
function seen_access(p, kind, sec) { if (!((p SUBSEP kind) in acc) || sec < acc[p, kind]) acc[p, kind] = sec }
function components(line, set,   n, i, parts, p) {
  n = split(line, parts, ":")
  for (i = 1; i <= n; i++) { p = parts[i]; sub(/\/.*/, "", p); if (pkg_ok(p)) set[p] = 1 }
}
function json_list(s,   n, i, a, out) {
  n = split(s, a, " "); out = ""
  for (i = 1; i <= n; i++) out = out (out == "" ? "" : ",") "\"" a[i] "\""
  return "[" out "]"
}
BEGIN {
  split("com.android.vending com.xiaomi.market com.xiaomi.mipicks com.xiaomi.discover com.huawei.appmarket " \
        "com.sec.android.app.samsungapps com.amazon.venezia org.fdroid.fdroid com.aurora.store", a, " ")
  for (i in a) store[a[i]] = 1
  split("com.miui.backup com.google.android.apps.restore com.coloros.backuprestore com.android.managedprovisioning", a, " ")
  for (i in a) restore[a[i]] = 1
  split(sources, a, " "); for (i in a) source[a[i]] = 1
  split(managers, a, " "); for (i in a) manager[a[i]] = 1
  ACCESS["CAMERA"] = "cam"; ACCESS["RECORD_AUDIO"] = "mic"; ACCESS["FINE_LOCATION"] = "loc"; ACCESS["COARSE_LOCATION"] = "loc"
  ACCESS["READ_SMS"] = "sms"; ACCESS["RECEIVE_SMS"] = "sms"; ACCESS["SEND_SMS"] = "sms"; ACCESS["READ_CONTACTS"] = "contacts"
  ACCESS["READ_CALL_LOG"] = "calls"; ACCESS["CALL_PHONE"] = "calls"; ACCESS["READ_CLIPBOARD"] = "clip"
  week = now - 604800
}
{ f = FILENAME; sub(/.*\//, "", f) }
f == "list" { p = $0; sub(/^package:/, "", p); if (pkg_ok(p) && !(p in apps)) { apps[p] = 1; order[++napps] = p }; next }
f == "packages" {
  if ($0 ~ /^[^ ]/) { save_install(); pkg = ""; next }   # a new section (Shared users:, ...) owns what follows
  if ($0 ~ /^ +Package \[/) {
    save_install(); pkg = $0; sub(/^.*Package \[/, "", pkg); sub(/\].*$/, "", pkg)
    if (pkg in source) present[pkg] = 1   # Gmail and the SMS app are system apps, not in the user list
    if (!(pkg in apps)) pkg = ""
    own_date = global_date = ""; scope = -1; next
  }
  if (pkg == "") next
  if ($0 ~ /^ +User [0-9]+:/) { s = $0; sub(/^ +User /, "", s); sub(/:.*/, "", s); scope = s + 0; next }
  if ($0 ~ /^ +(appId|userId)=[0-9]/ && !(pkg in appid)) { appid[pkg] = value($0) + 0; next }
  if ($0 ~ /^ +installerPackageName=/) { installer[pkg] = value($0); next }
  if ($0 ~ /^ +initiatingPackageName=/) { initiator[pkg] = value($0); next }
  if ($0 ~ /^ +packageSource=/) { pkgsrc[pkg] = value($0) + 0; next }
  if ($0 ~ /firstInstallTime=[0-9][0-9][0-9][0-9]-/) {
    s = $0; sub(/^.*firstInstallTime=/, "", s); s = substr(s, 1, 19)
    if (s ~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]$/) {
      if (scope == user) own_date = s; else if (scope == -1) global_date = s
    }
    next
  }
  if (scope == user && $0 ~ /android\.permission\.(READ_SMS|RECEIVE_SMS|SEND_SMS|RECEIVE_MMS|RECEIVE_WAP_PUSH): granted=true/) sms[pkg] = 1
  next
}
f == "usage" {
  if (!install_done++) save_install()
  if ($0 ~ /^[ \t]*user=[0-9]+/) { s = $0; sub(/^[ \t]*user=/, "", s); sub(/[^0-9].*/, "", s); usage_user = s + 0; scoped = 1 }
  if (!scoped || usage_user != user) next
  p = ""; last = 0; found = 0
  for (i = 1; i <= NF; i++) {
    split($i, kv, "=")
    if (kv[1] == "package" && pkg_ok(kv[2])) p = kv[2]
    if (kv[1] ~ /^(lastTimeUsed|lastTimeVisible|lastTimeComponentUsed|lastTimeFS)$/ && kv[2] ~ /^[0-9]+$/) { found = 1; if (kv[2] + 0 > last) last = kv[2] + 0 }
  }
  if (p in apps && found && last <= (now + 60) * 1000 && last > used[p]) used[p] = last
  next
}
f == "appops" {
  if (!install_done++) save_install()
  if ($0 ~ /^ *(Discrete|Historical)/) opstop = 1
  if (opstop) next
  if ($0 ~ /^ +Uid u[0-9]+a[0-9]+:/) { s = $0; sub(/^ +Uid u/, "", s); sub(/a.*/, "", s); ouser = s + 0; opk = ""; next }
  if ($0 ~ /^ +Uid /) { ouser = -1; opk = ""; next }
  if ($0 ~ /^ +Package [^ ]+:$/) { opk = $2; sub(/:$/, "", opk); if (ouser != user || !(opk in apps)) opk = ""; next }
  if (opk == "") next
  if ($0 ~ /^ +[A-Z][A-Z0-9_]+ \(/) {
    op = $1; mode = $0; sub(/^[^(]*\(/, "", mode); sub(/[ )\/].*$/, "", mode)
    if (op == "SYSTEM_ALERT_WINDOW" && mode == "allow") overlay[opk] = 1
    if (op == "REQUEST_INSTALL_PACKAGES" && mode == "allow") install[opk] = 1
    next
  }
  if ($0 ~ /^ +Access: / && (op in ACCESS) && match($0, /\(-[0-9dhms]+\)/)) seen_access(opk, ACCESS[op], age(substr($0, RSTART + 1, RLENGTH - 2)))
  next
}
f == "admins" {
  if ($0 ~ /Enabled Device Admins \(User [0-9]+/) { s = $0; sub(/.*\(User /, "", s); sub(/[^0-9].*/, "", s); auser = s + 0; next }
  s = $0; sub(/^ +/, "", s)
  if (auser == user && s ~ /^[A-Za-z][A-Za-z0-9_.]*\/[^ ]+:$/) { sub(/\/.*/, "", s); admin[s] = 1 }
  next
}
f == "launcher" { has_launcher = 1; s = $0; sub(/^ +/, "", s); sub(/\/.*/, "", s); if (pkg_ok(s)) icon[s] = 1; next }
f == "battery" {
  has_battery = 1
  if (match($0, /UID u[0-9]+a[0-9]+: [0-9.]+/)) {
    s = substr($0, RSTART + 5, RLENGTH - 5); u = s; sub(/a.*/, "", u); b = s; sub(/^[0-9]+a/, "", b); sub(/:.*/, "", b)
    m = s; sub(/^.*: /, "", m); k = (u * 100000) + 10000 + b
    if (!(k in bat)) bat[k] = m
  }
  next
}
f == "net" {
  has_net = 1
  if ($0 ~ /^ *[A-Za-z ]* stats:/) { innet = ($0 ~ /^ *UID stats:/); nuid = ""; next }
  if (!innet) next
  if (match($0, / uid=-?[0-9]+ set=/)) { nuid = substr($0, RSTART + 5, RLENGTH - 10) + 0; next }
  if (nuid != "" && $1 ~ /^st=[0-9]+$/) {
    st = substr($1, 4) + 0; if (st < week) next
    for (i = 2; i <= NF; i++) if ($i ~ /^(rb|tb)=[0-9]+$/) net[nuid] += substr($i, 4) + 0
  }
  next
}
f == "running" { p = $1; sub(/:.*/, "", p); if (p in apps) running[p] = 1; next }
f == "a11y" { components($0, a11y); next }
f == "notif" { components($0, notif); next }
f == "trusted" { if (pkg_ok($0)) trusted[$0] = 1; next }
f == "events" { if ($1 ~ /^[0-9]+$/ && pkg_ok($2)) ev[++nev] = "{\"at\":" $1 ",\"p\":\"" $2 "\",\"ok\":" ($3 == "0" ? 0 : 1) "}"; next }
END {
  save_install()
  printf "{\"ok\":1,\"user\":%d,\"scanned_at\":%d,\"missing\":%s,\"block\":{\"on\":%d,\"running\":%d,\"sources\":[", user, now, json_list(missing), block, block_running
  sep = ""
  n = split(sources, a, " ")
  for (i = 1; i <= n; i++) if (a[i] in present) { printf "%s\"%s\"", sep, a[i]; sep = "," }
  printf "],\"events\":["
  first = nev > 5 ? nev - 4 : 1
  for (i = first; i <= nev; i++) printf "%s%s", (i > first ? "," : ""), ev[i]
  printf "]},\"apps\":["
  for (i = 1; i <= napps; i++) {
    p = order[i]; aid = appid[p] + 0; uid = user * 100000 + aid
    from = initiator[p] != "" ? initiator[p] : installer[p]
    if (!pkg_ok(from)) from = ""
    if (from in source) src = "chat"
    else if (installer[p] in store || from in store || pkgsrc[p] == 2) src = "store"
    else if (from in restore) src = "restore"
    else if (from == "com.android.shell") src = "adb"
    else if (from != "" || pkgsrc[p] == 3 || pkgsrc[p] == 4) src = "file"
    else src = "unknown"
    hidden = has_launcher && !(p in icon)
    perms = ""
    if (p in sms) perms = perms " sms"
    if (p in a11y) perms = perms " a11y"
    if (p in admin) perms = perms " admin"
    if (p in notif) perms = perms " notif"
    if (p in overlay) perms = perms " overlay"
    if (p in install) perms = perms " install"
    if (hidden) perms = perms " hidden"
    side = src == "chat" || src == "file"
    strong = (p in sms) || (p in a11y) || (p in admin)
    core = (p in manager) || (host > 0 && aid > 0 && aid == host % 100000)
    if (core) risk = 0   # a trusted app keeps its mark; the WebUI shows it as trusted and counts it apart
    else if (side && (strong || ((p in notif) && (p in overlay)) || (hidden && ((p in notif) || (p in overlay) || (p in install))))) risk = 2
    else if (src == "chat" || strong || (side && (hidden || (p in notif) || (p in overlay) || (p in install)))) risk = 1
    else risk = 0
    printf "%s{\"p\":\"%s\",\"src\":\"%s\",\"from\":\"%s\",\"inst\":\"%s\",\"used\":%d,\"run\":%d,\"perms\":%s,\"acc\":{", \
      (i > 1 ? "," : ""), p, src, from, installed[p], used[p] / 1000, (p in running), json_list(perms)
    sep = ""
    split("cam mic loc sms contacts calls clip", kinds, " ")
    for (k = 1; k <= 7; k++) if ((p SUBSEP kinds[k]) in acc) { printf "%s\"%s\":%d", sep, kinds[k], acc[p, kinds[k]]; sep = "," }
    printf "},\"net\":%.0f,\"bat\":%s,\"risk\":%d,\"trusted\":%d,\"core\":%d}", \
      has_net ? net[uid] + 0 : -1, has_battery ? ((uid in bat) ? bat[uid] : 0) : -1, risk, (p in trusted), core
  }
  printf "]}\n"
}

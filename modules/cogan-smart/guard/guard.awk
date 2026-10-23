# Cogan Smart · Modul: turns the records of report.sh scan into one JSON report.
# Reads the modules' text files itself and flags lines by what they do. A flag is a guess; its
# evidence (file:line and the line) goes with it so the user can judge.
BEGIN {
  FS = "\t"; MAXLINES = 4000; MAXEV = 40
  CORE = " ksu ksud ap apd magisk magisk.db modules modules_update metamodule post-fs-data.d post-mount.d service.d boot-completed.d "
  WRITE = "(^|[;&|( \t])(rm|mv|cp|ln|touch|chmod|chown|dd|tee|mkdir|sed[ \t]+-i)[ \t]"   # plus a redirect, per check
  SECPROP = "ro\\.(debuggable|secure|adb\\.secure|boot\\.verifiedbootstate|boot\\.flash\\.locked|boot\\.vbmeta)"
  # level 2 bahaya, 1 waspada, 0 info
  L["selinux"] = 2;      T["selinux"] = "Mematikan perlindungan SELinux"
  L["policy_all"] = 2;   T["policy_all"] = "Aturan SELinux membuka hampir semua akses"
  L["fetch_exec"] = 2;   T["fetch_exec"] = "Mengunduh lalu menjalankan kode dari internet"
  L["hidden_exec"] = 2;  T["hidden_exec"] = "Menjalankan kode tersembunyi (base64)"
  L["root_tamper"] = 2;  T["root_tamper"] = "Mengubah file root manager"
  L["partition"] = 2;    T["partition"] = "Menulis langsung ke partisi"
  L["su"] = 2;           T["su"] = "Membawa su sendiri (root di luar root manager)"
  # Nodes Cogan Smart controls: a second writer fights its readback (as the old two modules did).
  KNOB = "scaling_(max|min)_freq|scaling_governor|cpufreq|uclamp|input_suspend|charging_enabled|charge_control|battery_charging|thermal"
  L["conflict"] = 1;     T["conflict"] = "Bentrok dengan Cogan Smart: ikut mengatur CPU, cas atau termal"
  L["policy_wide"] = 1;  T["policy_wide"] = "Aturan SELinux luas (*)"
  L["network"] = 1;      T["network"] = "Menghubungi internet/server"
  L["hidden"] = 1;       T["hidden"] = "Membuka data tersandi (base64)"
  L["other_modules"] = 1; T["other_modules"] = "Mengubah modul lain"
  L["persist"] = 1;      T["persist"] = "Menaruh skrip boot di luar foldernya (tertinggal bila modul dihapus)"
  L["perm777"] = 1;      T["perm777"] = "Membuka izin file untuk semua (777)"
  L["apps"] = 1;         T["apps"] = "Mencopot/membekukan aplikasi"
  L["secprop"] = 1;      T["secprop"] = "Mengubah properti keamanan/boot (umum di modul spoof)"
  L["zygisk"] = 1;       T["zygisk"] = "Menyuntik kode ke aplikasi (Zygisk)"
  L["init_rc"] = 1;      T["init_rc"] = "Menambah layanan init sistem (.rc)"
  L["sys_bin"] = 1;      T["sys_bin"] = "Mengganti/menambah program sistem"
  L["identity"] = 1;     T["identity"] = "Identitas modul tidak lengkap"
  L["elf"] = 0;          T["elf"] = "Membawa program biner (isinya tidak terbaca)"
  L["overlay"] = 0;      T["overlay"] = "Mengganti/menambah file sistem"
  L["props"] = 0;        T["props"] = "Mengubah properti sistem"
  L["sepolicy"] = 0;     T["sepolicy"] = "Menambah aturan SELinux"
  L["firewall"] = 0;     T["firewall"] = "Mengatur firewall/jaringan"
  L["settings"] = 0;     T["settings"] = "Mengubah setelan Android"
  L["running"] = 0;      T["running"] = "Proses sedang berjalan"
}

function j(s) { gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s); gsub(/[[:cntrl:]]/, " ", s); return "\"" s "\"" }
function push(arr, k, v) { if (k in arr) arr[k] = arr[k] SUBSEP v; else arr[k] = v }   # test first: some awks create arr[k] before the right side
function list(s,   n, a, i, out) {
  n = split(s, a, SUBSEP); out = ""
  for (i = 1; i <= n; i++) out = out (i > 1 ? "," : "") j(a[i])
  return "[" out "]"
}
function hit(o, c, at, t) {
  if (!((o, c) in cnt)) push(codes, o, c)
  cnt[o, c]++
  if (at != "" && cnt[o, c] <= 3 && nev[o] < MAXEV) { nev[o]++; ev[o, nev[o]] = c SUBSEP at SUBSEP substr(t, 1, 160) }
}
function issues(o,   n, a, i, c, r, out, k, b, e) {
  r = 0; out = ""; e = ""
  n = (o in codes) ? split(codes[o], a, SUBSEP) : 0
  for (i = 1; i <= n; i++) {
    c = a[i]; if (L[c] > r) r = L[c]
    out = out (i > 1 ? "," : "") "{\"code\":" j(c) ",\"level\":" L[c] ",\"text\":" j(T[c]) ",\"count\":" cnt[o, c] "}"
  }
  for (k = 1; k <= nev[o]; k++) {
    split(ev[o, k], b, SUBSEP)
    e = e (k > 1 ? "," : "") "{\"code\":" j(b[1]) ",\"at\":" j(b[2]) ",\"line\":" j(b[3]) "}"
  }
  return "\"risk\":" r ",\"flags\":[" out "],\"hits\":[" e "]"
}

# What a line names elsewhere: /data/adb entries (who uses them) and other modules.
function refs(o, t, at,   s, tok) {
  s = t
  while (match(s, /\/data\/adb\/[A-Za-z0-9._-]+/)) {
    tok = substr(s, RSTART + 10, RLENGTH - 10)
    if (!(tok in user) && o !~ /^boot:/) user[tok] = o
    s = substr(s, RSTART + RLENGTH)
  }
  s = t
  while (match(s, /\/adb\/modules\/[A-Za-z][A-Za-z0-9._-]*/)) {
    tok = substr(s, RSTART + 13, RLENGTH - 13)
    if (o ~ /^boot:/) { if (!((tok, o) in rooted)) { rooted[tok, o] = 1; push(roots, tok, substr(o, 6)) } }
    else if (tok != o && (t ~ WRITE || t ~ />>?[ \t]*["']?[^ \t]*\/adb\/modules\//)) hit(o, "other_modules", at, t)
    s = substr(s, RSTART + RLENGTH)
  }
}

function sepol(o, t, at,   w, n, i, stars) {
  hit(o, "sepolicy", "", "")
  if (t ~ /^permissive([ \t]|$)/) { hit(o, "selinux", at, t); return }
  n = split(t, w, /[ \t]+/); stars = 0
  for (i = 1; i <= n; i++) if (w[i] == "*") stars++
  if (stars >= 3) hit(o, "policy_all", at, t)
  else if (stars) hit(o, "policy_wide", at, t)
}

function scan(o, path, rel,   line, n, t, at, net) {
  n = 0
  while ((getline line < path) > 0) {
    if (++n > MAXLINES) break
    t = line; sub(/^[ \t]+/, "", t)
    if (t == "" || t ~ /^#/) continue
    at = rel ":" n
    refs(o, t, at)
    if (rel ~ /(^|\/)sepolicy\.rule$/) { sepol(o, t, at); continue }
    if (rel ~ /(^|\/)system\.prop$/) {
      if (t ~ /=/) { hit(o, "props", "", ""); if (t ~ SECPROP) hit(o, "secprop", at, t) }
      continue
    }
    if (t ~ /setenforce[ \t]+0/) hit(o, "selinux", at, t)
    net = t ~ /(^|[^A-Za-z0-9_.-])(curl|wget)([ \t]|$)/ || t ~ /(^|[ \t;|&(])(busybox[ \t]+)?(nc|ncat|netcat)[ \t]/
    if (net && t ~ /\|[ \t]*(ba|z|k|mk)?sh([ \t]|$)/) hit(o, "fetch_exec", at, t)
    else if (net) hit(o, "network", at, t)
    if (t ~ /base64[ \t]+(-d|--decode)/) hit(o, t ~ /eval|\|[ \t]*(ba)?sh/ ? "hidden_exec" : "hidden", at, t)
    if (t ~ /\/data\/adb\/(ksu|ksud|magisk|ap|apd|metamodule)([\/ \t"';]|$)/ && (t ~ WRITE || t ~ />>?[ \t]*["']?\/data\/adb\/(ksu|ksud|magisk|ap|apd|metamodule)/)) hit(o, "root_tamper", at, t)
    if (t ~ /of=["']?\/dev\/block\// || t ~ />[ \t]*["']?\/dev\/block\// || t ~ /blockdev[ \t]+--setrw/) hit(o, "partition", at, t)
    if (t ~ /\/data\/adb\/(post-fs-data|post-mount|service|boot-completed)\.d/ && (t ~ WRITE || t ~ />>?[ \t]*["']?\/data\/adb\/[a-z-]+\.d/)) hit(o, "persist", at, t)
    if (t ~ /chmod[ \t]+(-R[ \t]+)?0?777/) hit(o, "perm777", at, t)
    if (o != SELF && t ~ KNOB && (t ~ />[ \t]*["']?\// || t ~ WRITE || t ~ /(^|[^A-Za-z0-9_])stop[ \t]/)) hit(o, "conflict", at, t)
    if (t ~ /(^|[^A-Za-z0-9_])pm[ \t]+(uninstall|disable|disable-user|hide|suspend)[ \t]/) hit(o, "apps", at, t)
    if (t ~ /(^|[^A-Za-z0-9_])(resetprop|setprop)[ \t]/) { hit(o, "props", at, t); if (t ~ SECPROP) hit(o, "secprop", at, t) }
    if (t ~ /(^|[^A-Za-z0-9_])ip6?tables[ \t]/) hit(o, "firewall", at, t)
    if (t ~ /(^|[^A-Za-z0-9_])settings[ \t]+put[ \t]/) hit(o, "settings", at, t)
  }
  close(path)
}

function readprop(id, path,   line, k, v) {
  while ((getline line < path) > 0) {
    k = index(line, "="); if (!k) continue
    v = substr(line, k + 1); sub(/[ \t\r]+$/, "", v)
    prop[id, substr(line, 1, k - 1)] = v
  }
  close(path)
  if (prop[id, "name"] == "" || prop[id, "id"] != id) hit(id, "identity", "module.prop", "id=" prop[id, "id"] " name=" prop[id, "name"])
  if (prop[id, "metamodule"] ~ /^(1|true)/) META = META == "" ? id : META
}

function file(id, rel, kind, path) {
  files[id]++
  if (rel ~ /^(system|vendor|product|system_ext|odm)\//) {
    hit(id, "overlay", "", "")
    if (++nov[id] <= 30) push(overlays, id, rel)
    if (rel ~ /^system\/x?bin\/su$/) hit(id, "su", rel, "")
    else if (rel ~ /^system\/x?bin\//) hit(id, "sys_bin", rel, "")
    if (rel ~ /^system\/etc\/init\/.*\.rc$/) hit(id, "init_rc", rel, "")
  }
  if (rel ~ /^zygisk\// && !zy[id]++) hit(id, "zygisk", rel, "")
  if (rel ~ /^((post-fs-data|post-mount|service|boot-completed|uninstall|action|customize)\.sh|system\.prop|sepolicy\.rule|webroot\/index\.html)$/) push(hooks, id, rel)
  if (kind == "elf") hit(id, "elf", rel, "")
  if (kind == "text") scan(id, path, rel)
}

function proc_owner(cmd,   i, rest, d, n, a) {
  if ((i = index(cmd, ADB "/modules/")) > 0) {
    rest = substr(cmd, i + length(ADB) + 9); sub(/[\/ ].*/, "", rest); return rest
  }
  n = split("post-fs-data.d post-mount.d service.d boot-completed.d", a, " ")
  for (d = 1; d <= n; d++) if ((i = index(cmd, ADB "/" a[d] "/")) > 0) {
    rest = substr(cmd, i + length(ADB) + length(a[d]) + 2); sub(/[\/ ].*/, "", rest); return "boot:" a[d] "/" rest
  }
  return ""
}

$1 == "self" { SELF = $2; next }
$1 == "meta" { META = $2; next }
$1 == "manager" { MGR = $2; MGRV = $3; next }
$1 == "trust" { trusted[$2] = 1; next }
$1 == "pending" { update[$2] = 1; next }
$1 == "module" { mods[++nm] = $2; installed[$2] = 1; readprop($2, $3 "/module.prop"); next }
$1 == "flag" { state[$2] = $3 == "remove" ? "remove" : $3 == "install" ? "install" : state[$2] == "" ? "off" : state[$2]; next }
$1 == "size" { size[$2] = $3 + 0; next }
$1 == "file" { file($2, $3, $4, $5); next }
$1 == "boot" { o = "boot:" $2 "/" $3; boots[++nb] = o; bdir[o] = $2; bname[o] = $3; scan(o, $4, $2 "/" $3); next }
$1 == "entry" { entries[++ne] = $2; etype[$2] = $3; next }
$1 == "proc" {
  sub(/[ \t]+$/, "", $3); o = proc_owner($3)
  if (o == "") {
    if (!index($3, ADB "/ksu") && !index($3, ADB "/ap/") && !index($3, ADB "/apd") && !index($3, ADB "/magisk")) push(strays, 1, $2 " " $3)
  } else {
    hit(o, "running", "", "")
    if (cnt[o, "running"] <= 8) push(procs, o, $2 " " $3)
  }
  next
}

END {
  K = ENVIRON["CG_KERNEL"]; D = ENVIRON["CG_DEVICE"]   # JSON from bridge.sh
  printf "{\"ok\":1,\"kernel\":%s,\"device\":%s", (K == "" ? "null" : K), (D == "" ? "null" : D)
  printf ",\"manager\":%s,\"manager_version\":%s,\"meta\":%s,\"self\":%s,\"modules\":[", j(MGR), j(MGRV), j(META), j(SELF)
  for (k = 1; k <= nm; k++) {
    id = mods[k]; core = (id == SELF || id == META)
    printf "%s{\"id\":%s,\"name\":%s,\"version\":%s,\"author\":%s,\"description\":%s", (k > 1 ? "," : ""), j(id),
      j(prop[id, "name"]), j(prop[id, "version"]), j(prop[id, "author"]), j(substr(prop[id, "description"], 1, 240))
    # one-true-awk takes no bare comparisons in a printf argument list
    st = state[id] == "" ? "on" : state[id]; upd = update[id] && st != "install"; tr = core || (id in trusted)
    data = etype[id] == "dir" && index(CORE, " " id " ") == 0
    printf ",\"state\":%s,\"update\":%d,\"core\":%d,\"trusted\":%d,\"size\":%d,\"files\":%d,\"overlay_count\":%d",
      j(st), upd, core, tr, size[id], files[id], nov[id]
    printf ",\"data\":%d,\"hooks\":%s,\"overlays\":%s,\"procs\":%s,\"roots\":%s,%s}",
      data, list(hooks[id]), list(overlays[id]), list(procs[id]), list(roots[id]), issues(id)
  }
  printf "],\"boot\":["
  for (k = 1; k <= nb; k++) {
    o = boots[k]; uses = ""
    for (key in rooted) { split(key, a, SUBSEP); if (a[2] == o) uses = uses (uses == "" ? "" : SUBSEP) a[1] }
    printf "%s{\"dir\":%s,\"name\":%s,\"modules\":%s,\"procs\":%s,%s}", (k > 1 ? "," : ""), j(bdir[o]), j(bname[o]), list(uses), list(procs[o]), issues(o)
  }
  printf "],\"entries\":["
  for (k = 1; k <= ne; k++) {
    e = entries[k]
    owner = index(CORE, " " e " ") || e == SELF ? "core" : (e in installed) ? e : (e in user) ? user[e] : ""
    printf "%s{\"name\":%s,\"type\":%s,\"owner\":%s}", (k > 1 ? "," : ""), j(e), j(etype[e]), j(owner)
  }
  printf "],\"strays\":%s}\n", list(strays[1])
}

# AOSP Android 16 dumpsys usagestats -c: numeric epoch-ms timestamps, scoped by user.
# Missing/zero usage or installation dates are unknown, never proof of seven idle days.
function pkg_ok(p) { return p ~ /^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$/ }
function save_install() {
  if (pkg_ok(pkg)) installed[pkg] = own_date != "" ? own_date : (user == 0 ? global_date : "")
}
FILENAME == ARGV[1] {
  p=$0; sub(/^package:/,"",p); if (pkg_ok(p)) apps[p]=1
  next
}
FILENAME == ARGV[2] {
  if ($0 ~ /^[ \t]*Package \[/) {
    save_install(); pkg=$0; sub(/^.*Package \[/,"",pkg); sub(/\].*$/,"",pkg)
    own_date=global_date=""; scope=-1
  } else if ($0 ~ /^[ \t]*User [0-9]+:/) {
    s=$0; sub(/^[ \t]*User /,"",s); sub(/:.*/,"",s); scope=s+0
  }
  if (pkg_ok(pkg) && $0 ~ /firstInstallTime=[0-9][0-9][0-9][0-9]-/) {
    s=$0; sub(/^.*firstInstallTime=/,"",s); s=substr(s,1,19)
    if (s ~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]$/) {
      if (scope == user) own_date=s; else if (scope == -1) global_date=s
    }
  }
  next
}
FILENAME == ARGV[3] {
  if (!install_done++) save_install()
  if ($0 ~ /^[ \t]*user=[0-9]+/) {
    s=$0; sub(/^[ \t]*user=/,"",s); sub(/[^0-9].*/,"",s); usage_user=s+0; scoped=1
  }
  if (!scoped || usage_user != user) next
  p=""; last=0; found=0
  for (i=1;i<=NF;i++) {
    split($i,kv,"=")
    if (kv[1]=="package" && pkg_ok(kv[2])) p=kv[2]
    if (kv[1] ~ /^(lastTimeUsed|lastTimeVisible|lastTimeComponentUsed|lastTimeFS)$/ && kv[2] ~ /^[0-9]+$/) {
      found=1; if (kv[2]+0 > last) last=kv[2]+0
    }
  }
  if (p in apps && found) {
    readable=1; seen[p]=1
    if (last > (now+60)*1000) bad[p]=1
    if (last > used[p]) used[p]=last
  }
  next
}
FILENAME == ARGV[4] {
  p=$1; sub(/:.*/,"",p); if (p in apps) running[p]=1
}
END {
  save_install()
  if (!readable) { print "{\"ok\":0,\"error\":\"Data pemakaian tujuh hari belum dapat dipastikan.\"}"; exit }
  printf "{\"ok\":1,\"user\":%d,\"days\":7,\"scanned_at\":%.0f,\"apps\":[",user,now
  for (p in apps) {
    total++
    if (bad[p] || !seen[p] || used[p]<=0 || installed[p]=="") { unknown++; continue }
    if (installed[p] > cutoff || used[p] > (now-604800)*1000 || running[p]) { recent++; continue }
    printf "%s{\"package\":\"%s\",\"last_used\":%.0f,\"idle_days\":%d}",n++?",":"",p,used[p]/1000,int((now-used[p]/1000)/86400)
  }
  printf "],\"total\":%d,\"unknown\":%d,\"recent\":%d}\n",total,unknown,recent
}

# Cogan Smart · Thermal: reports from the sampler's lines (tab separated, see sampler.sh).
# Needs thermal.awk first. Variables: mode (text|json|csv|detail|now|latest|main|date|label), since, now, secs,
# HOT (tenths of degC), TZOFF, KFILE (kernels.tsv), MFILE (modes.tsv from Cogan Smart · Power), zones (main),
# fresh (now: zones read just now), release (now: uname -r), running (now: 1/0).

BEGIN {
    FS = "\t"
    if (mode == "main") { print main_temp(zones); done = 1; exit }
    if (mode == "date") { print local_date(since - 86400); done = 1; exit }   # oldest data file to read
    if (mode == "label") { print label(app); done = 1; exit }
    G = "cpu gpu bat skin modem chg pmic apu wifi other"
    ng = split(G, GROUPS, " ")
    if (mode == "csv") {
        printf tr("waktu,aplikasi,layar,cas,arus_mA,cpu_persen,kernel_persen,gpu_persen,proses_teratas,wifi_kBps,seluler_kBps", "time,app,screen,charging,current_mA,cpu_percent,kernel_percent,gpu_percent,top_processes,wifi_kBps,cellular_kBps")
        for (i = 1; i <= ng; i++) printf ",%s", group_name(GROUPS[i])
        print tr(",semua_sensor", ",all_sensors")
    }
}

FILENAME == KFILE { if ($1 + 0 > 0) { kn++; kts[kn] = $1 + 0; kname[kn] = $2 }; next }
FILENAME == MFILE { if ($1 + 0 > 0) { mn++; mts[mn] = $1 + 0; mname[mn] = $2 }; next }
mode == "now" { last = $0; next }
$1 + 0 < since || $1 + 0 > now || NF < 13 { next }

{
    ts = $1 + 0; app = $2; screen = $3 + 0; chg = $4 + 0; cur = $5 + 0; bat = $6 + 0
    cpu = $7 + 0; kern = $8 + 0; gpu = $9 + 0; top = $10; net = $11; zl = $13
    split("", gmax)
    m = split(zl, z, ",")
    for (i = 1; i <= m; i++) {
        if (split(z[i], kv, "=") != 2) continue
        v = kv[2] + 0
        if (!(kv[1] in GC)) GC[kv[1]] = group(kv[1])   # a week holds millions of zone readings
        g = GC[kv[1]]
        if (!(g in gmax) || v > gmax[g]) gmax[g] = v
    }
    if (!("bat" in gmax) && bat > -999) gmax["bat"] = bat
    # Only test with "in": reading gmax["gpu"] would create it and count 0 °C for that sample.
    main = -9999
    if ("cpu" in gmax) main = gmax["cpu"]
    if (("gpu" in gmax) && gmax["gpu"] > main) main = gmax["gpu"]
    if (main == -9999) main = maxall()
    n++
    if (n == 1) first = ts
    lastts = ts
    for (g in gmax) {
        gsum[g] += gmax[g]; gcnt[g]++
        if (!(g in gpeak) || gmax[g] > gpeak[g]) { gpeak[g] = gmax[g]; gpts[g] = ts }
    }
    if (n == 1 || main > mpeak) {
        mpeak = main; mpts = ts; mapp = app; mcpu = cpu; mgpu = gpu; mchg = chg; mcur = cur; mtop = top
        mgroup = (("gpu" in gmax) && gmax["gpu"] == main && !(("cpu" in gmax) && gmax["cpu"] == main)) ? "gpu" : "cpu"
    }
    msum += main
    appn[app]++; appsum[app] += main
    if (!(app in apppeak) || main > apppeak[app]) apppeak[app] = main
    k = kernel_at(ts)
    kern_n[k]++; kern_sum[k] += main
    if (!(k in kern_peak) || main > kern_peak[k]) kern_peak[k] = main
    if (mn) {
        md = mode_at(ts)
        mode_n[md]++; mode_sum[md] += main
        if (!(md in mode_peak) || main > mode_peak[md]) mode_peak[md] = main
        if (main >= HOT) mode_hot[md]++
    }
    if (cpu >= 0) { cpusum += cpu; cpun++ }
    if (kern >= 0) { kernsum += kern; kernn++ }
    if (main >= HOT) { hot++; c = cause(); causes[c]++ }
    ser_ts[n] = ts; ser_v[n] = main
    if (mode == "csv") csv_row()
    if (mode == "detail") detail_row()
}

function maxall(   g, b) { b = -9999; for (g in gmax) if (gmax[g] > b) b = gmax[g]; return b }
function kernel_at(ts,   i, k) { k = "?"; for (i = 1; i <= kn; i++) if (kts[i] <= ts) k = kname[i]; return k }
function mode_at(ts,   i, m) { m = "none"; for (i = 1; i <= mn; i++) if (mts[i] <= ts) m = mname[i]; return m }
function top_first(   parts, kv) {
    TOPN = ""; TOPP = 0
    if (split(top, parts, ";") < 1 || parts[1] == "-") return
    split(parts[1], kv, ":"); TOPN = kv[1]; TOPP = kv[2] + 0
}
function net_kbps(kind,   kv) { if (match(net, kind ":-?[0-9]+")) { split(substr(net, RSTART, RLENGTH), kv, ":"); return kv[2] + 0 }; return "" }
function cell_kbps() { return net_kbps("cell") + 0 }
# "com.mobile.legends:250;..." as "Mobile Legends 25.0%; ...".
function top_text(t,   parts, n, i, kv, s) {
    s = ""; n = split(t, parts, ";")
    for (i = 1; i <= n; i++) if (split(parts[i], kv, ":") == 2) s = s (s == "" ? "" : "; ") label(kv[1]) sprintf(" %.1f%%", kv[2] / 10)
    return s == "" ? "-" : s
}

# Most likely reason for one hot sample, in priority order.
function cause() {
    top_first()
    if (chg && cur >= 1500) return tr("Cas cepat", "Fast charging")
    if (gpu >= 60) return tr("Grafis berat: ", "Heavy graphics: ") label(app)
    if (TOPN != "" && TOPN != app && TOPP >= 100) return tr("Latar belakang: ", "Background: ") label(TOPN)
    if (kern >= 100) return tr("Proses kernel", "Kernel processes")
    if (cell_kbps() >= 1500) return tr("Data seluler berat (modem)", "Heavy cellular traffic (modem)")
    if (app == "screen_off") return chg ? tr("Mengecas (layar mati)", "Charging (screen off)") : tr("Layar mati (proses latar belakang)", "Screen off (background processes)")
    if (cpu >= 250) return tr("Aplikasi berat: ", "Heavy app: ") label(app)
    if (chg) return tr("Mengecas", "Charging")
    return tr("Pemakaian ringan: ", "Light use: ") label(app)
}

function csv_row(   i, g, line) {
    line = local_date(ts) " " local_clock(ts) "," label(app) "," (app == "screen_off" ? tr("mati", "off") : tr("nyala", "on")) "," \
           (chg ? tr("ya", "yes") : tr("tidak", "no")) "," cur "," (cpu >= 0 ? cpu / 10 : "") "," (kern >= 0 ? kern / 10 : "") "," \
           (gpu >= 0 ? gpu : "") ",\"" top_text(top) "\"," net_kbps("wifi") "," net_kbps("cell")
    for (i = 1; i <= ng; i++) { g = GROUPS[i]; line = line "," ((g in gmax) ? deg(gmax[g]) : "") }
    print line ",\"" zl "\""
}

function detail_row(   i, g, s) {
    s = ""
    for (i = 1; i <= ng; i++) { g = GROUPS[i]; if (g in gmax) s = s (s == "" ? "" : " · ") group_name(g) " " deg(gmax[g]) }
    printf tr("%s %s  %s | %s | CPU %s | GPU %s | %s | teratas: %s\n", "%s %s  %s | %s | CPU %s | GPU %s | %s | top: %s\n"), local_date(ts), local_clock(ts), s, label(app), \
        (cpu >= 0 ? sprintf("%.1f%%", cpu / 10) : "-"), (gpu >= 0 ? gpu "%" : "-"), (chg ? tr("cas ", "charging ") cur " mA" : tr("tidak dicas", "not charging")), top_text(top)
}

# Clock time, with the day ("17/10 21:05") when the samples cover a day or more.
function stamp(ts,   d) { if (lastts - first < 86400) return local_clock(ts); d = local_date(ts); return substr(d, 9, 2) "/" substr(d, 6, 2) " " local_clock(ts) }
function span(s) { return s >= 86400 && s % 86400 == 0 ? (s / 86400) tr(" hari", " days") : s >= 3600 && s % 3600 == 0 ? (s / 3600) tr(" jam", " hours") : int(s / 60) tr(" menit", " minutes") }

# Sorted index of an array by value (descending), without gawk's asort.
function rank(arr, out,   k, n, i, j, t) {
    n = 0
    for (k in arr) { n++; out[n] = k }
    for (i = 2; i <= n; i++) { t = out[i]; for (j = i - 1; j >= 1 && arr[out[j]] < arr[t]; j--) out[j + 1] = out[j]; out[j + 1] = t }
    return n
}

function summary_text(   s, i, g, nc, order, na, apps, nk, kord, line, nm, mord) {
    s = tr("Cogan Smart · Thermal — ringkasan ", "Cogan Smart · Thermal — summary ") span(secs)
    if (n == 0) return s tr("\nBelum ada data pada rentang ini. Modul mencatat tiap beberapa detik setelah HP menyala.\n", "\nNo data in this range yet. The module records at the configured interval after boot.\n")
    s = s " (" stamp(first) "–" stamp(lastts) (lastts - first < 86400 ? ", " local_date(lastts) : "") ") · " n tr(" sampel\n\n", " samples\n\n")
    s = s tr("🌡️ Suhu tertinggi: ", "🌡️ Peak temperature: ") deg(mpeak) " °C (" group_name(mgroup) tr(") pukul ", ") at ") stamp(mpts) "\n"
    s = s tr("   saat ", "   during ") label(mapp) " · CPU " (mcpu >= 0 ? sprintf("%.0f%%", mcpu / 10) : "-") " · GPU " (mgpu >= 0 ? mgpu "%" : "-") \
          " · " (mchg ? tr("mengecas ", "charging ") mcur " mA" : tr("tidak dicas", "not charging")) "\n\n"
    s = s tr("Per bagian (tertinggi / rata-rata):\n", "By component (peak / average):\n")
    for (i = 1; i <= ng; i++) { g = GROUPS[i]; if (g in gpeak) s = s sprintf("  %-10s %s / %s °C\n", group_name(g), deg(gpeak[g]), deg(gsum[g] / gcnt[g])) }
    s = s tr("\n🔥 Penyebab panas (≥ ", "\n🔥 Heat causes (≥ ") deg(HOT) " °C):"
    if (!hot) s = s tr(" tidak ada momen panas.\n", " no hot samples.\n")
    else {
        s = s sprintf(tr(" %d%% waktu\n", " %d%% of samples\n"), int(hot * 100 / n + 0.5))
        nc = rank(causes, order)
        for (i = 1; i <= nc && i <= 6; i++) s = s sprintf("  %d. %s — %d%%\n", i, order[i], int(causes[order[i]] * 100 / hot + 0.5))
        s = s tr("  ➜ Kesimpulan: paling sering panas karena ", "  ➜ Most frequent inferred heat cause: ") order[1] ".\n"
    }
    for (a in appn) appavg[a] = appn[a]
    na = rank(appavg, apps)
    s = s tr("\n📱 Per aplikasi (waktu · rata-rata · tertinggi):\n", "\n📱 By app (time · average · peak):\n")
    for (i = 1; i <= na && i <= 8; i++)
        s = s sprintf("  %-22s %3d%% · %s · %s °C\n", label(apps[i]), int(appn[apps[i]] * 100 / n + 0.5), deg(appsum[apps[i]] / appn[apps[i]]), deg(apppeak[apps[i]]))
    nk = rank(kern_n, kord)
    s = s tr("\n🐧 Per kernel (rata-rata · tertinggi):\n", "\n🐧 By kernel (average · peak):\n")
    for (i = 1; i <= nk; i++) s = s sprintf(tr("  %s — %s · %s °C (%d%% waktu)\n", "  %s — %s · %s °C (%d%% of samples)\n"), kord[i], deg(kern_sum[kord[i]] / kern_n[kord[i]]), deg(kern_peak[kord[i]]), int(kern_n[kord[i]] * 100 / n + 0.5))
    if (mn) {
        nm = rank(mode_n, mord)
        s = s tr("\n⚡ Per mode (rata-rata · tertinggi · waktu panas):\n", "\n⚡ By mode (average · peak · hot samples):\n")
        for (i = 1; i <= nm; i++) s = s sprintf(tr("  %s — %s · %s °C · %d%% panas (%d%% waktu)\n", "  %s — %s · %s °C · %d%% hot (%d%% of samples)\n"), mode_name(mord[i]), deg(mode_sum[mord[i]] / mode_n[mord[i]]), \
            deg(mode_peak[mord[i]]), int(mode_hot[mord[i]] * 100 / mode_n[mord[i]] + 0.5), int(mode_n[mord[i]] * 100 / n + 0.5))
    }
    s = s tr("\nCPU rata-rata ", "\nAverage CPU ") (cpun ? sprintf("%.0f%%", cpusum / cpun / 10) : "-") tr(" · proses kernel ", " · kernel processes ") (kernn ? sprintf("%.1f%%", kernsum / kernn / 10) : "-") "\n"
    return s
}

function json_list(arr, total, limit, kind,   ord, nn, i, s, k) {
    nn = rank(arr, ord); s = ""
    for (i = 1; i <= nn && i <= limit; i++) {
        k = ord[i]
        if (kind == "cause") s = s (i > 1 ? "," : "") sprintf("{\"name\":\"%s\",\"pct\":%d}", jesc(k), int(arr[k] * 100 / total + 0.5))
        else if (kind == "app") s = s (i > 1 ? "," : "") sprintf("{\"name\":\"%s\",\"pkg\":\"%s\",\"pct\":%d,\"avg\":%d,\"peak\":%d}", jesc(label(k)), jesc(k), int(arr[k] * 100 / total + 0.5), int(appsum[k] / appn[k]), apppeak[k])
        else if (kind == "mode") s = s (i > 1 ? "," : "") sprintf("{\"name\":\"%s\",\"mode\":\"%s\",\"pct\":%d,\"avg\":%d,\"peak\":%d,\"hot_pct\":%d}", mode_name(k), jesc(k), int(arr[k] * 100 / total + 0.5), int(mode_sum[k] / mode_n[k]), mode_peak[k], int(mode_hot[k] * 100 / mode_n[k] + 0.5))
        else s = s (i > 1 ? "," : "") sprintf("{\"name\":\"%s\",\"pct\":%d,\"avg\":%d,\"peak\":%d}", jesc(k), int(arr[k] * 100 / total + 0.5), int(kern_sum[k] / kern_n[k]), kern_peak[k])
    }
    return "[" s "]"
}

function json_summary(   s, i, g, step, b, j, mx, sep) {
    s = sprintf("{\"samples\":%d,\"secs\":%d,\"hot\":%d,\"hot_pct\":%d", n, secs, HOT, n ? int(hot * 100 / n + 0.5) : 0)
    if (n) {
        s = s sprintf(",\"from\":\"%s\",\"to\":\"%s\",\"peak\":{\"t\":%d,\"group\":\"%s\",\"clock\":\"%s\",\"app\":\"%s\",\"cpu\":%d,\"gpu\":%d,\"charging\":%d,\"current\":%d}", \
            stamp(first), stamp(lastts), mpeak, group_name(mgroup), stamp(mpts), jesc(label(mapp)), mcpu, mgpu, mchg, mcur)
        s = s ",\"groups\":["; sep = ""
        for (i = 1; i <= ng; i++) { g = GROUPS[i]; if (g in gpeak) { s = s sep sprintf("{\"name\":\"%s\",\"peak\":%d,\"avg\":%d}", group_name(g), gpeak[g], int(gsum[g] / gcnt[g])); sep = "," } }
        s = s "],\"causes\":" (hot ? json_list(causes, hot, 6, "cause") : "[]")
        s = s ",\"apps\":" json_list(appn, n, 8, "app") ",\"kernels\":" json_list(kern_n, n, 4, "kernel")
        s = s ",\"modes\":" (mn ? json_list(mode_n, n, 4, "mode") : "[]")
        s = s sprintf(",\"cpu_avg\":%d,\"kernel_avg\":%d", cpun ? cpusum / cpun : -1, kernn ? kernsum / kernn : -1)
        step = int((n + 119) / 120); s = s ",\"series\":["; sep = ""
        for (b = 1; b <= n; b += step) {
            mx = ser_v[b]; for (j = b; j < b + step && j <= n; j++) if (ser_v[j] > mx) mx = ser_v[j]
            s = s sep sprintf("[%d,%d]", ser_ts[b], mx); sep = ","
        }
        s = s "]"
    }
    return s ",\"text\":\"" jesc_text(summary_text()) "\"}"
}
function jesc_text(t) { t = jesc(t); gsub(/\n/, "\\n", t); gsub(/\t/, " ", t); return t }

function json_now(   f, zl2, m2, z2, kv2, i, s, sep, gm, g, mainv, age) {
    split(last, f, "\t")
    # A live read with no usable zones must never resurrect a historical temperature.
    zl2 = fresh
    m2 = split(zl2, z2, ","); s = ""; sep = ""
    for (i = 1; i <= m2; i++) {
        if (split(z2[i], kv2, "=") != 2) continue
        g = group(kv2[1])
        if (!(g in gm) || kv2[2] + 0 > gm[g]) gm[g] = kv2[2] + 0
        s = s sep sprintf("{\"name\":\"%s\",\"group\":\"%s\",\"t\":%d}", jesc(kv2[1]), group_name(g), kv2[2]); sep = ","
    }
    mainv = main_temp(zl2)
    age = (f[1] + 0 > 0) ? now - f[1] : -1
    # Android's One True Awk rejects bare comparisons in a printf argument list.
    if (health == "") health = "null"
    printf "{\"sensor_ts\":%d,\"sample_ts\":%d,\"monitor\":%s,", sensor_ts, f[1] + 0, health
    printf "\"running\":%d,\"mode\":\"%s\",\"release\":\"%s\",\"age\":%d,\"main\":%d,\"app\":\"%s\",\"pkg\":\"%s\",\"charging\":%d,\"current\":%d,\"battery\":%d,\"cpu\":%d,\"kernel\":%d,\"gpu\":%d,\"top\":\"%s\",\"groups\":[", \
        running, (mn ? mode_name(mname[mn]) : ""), jesc(release), age, mainv, jesc(label(f[2])), jesc(f[2]), f[4] + 0, f[5] + 0, (f[6] == "" ? -999 : f[6] + 0), (f[7] == "" ? -1 : f[7] + 0), (f[8] == "" ? -1 : f[8] + 0), (f[9] == "" ? -1 : f[9] + 0), jesc(f[10])
    sep = ""
    for (i = 1; i <= ng; i++) { g = GROUPS[i]; if (g in gm) { printf "%s{\"name\":\"%s\",\"t\":%d}", sep, group_name(g), gm[g]; sep = "," } }
    print "],\"zones\":[" s "]}"
}

END {
    if (done) exit
    if (mode == "now") json_now()
    else if (mode == "latest") { if (n) printf "%d\t%d\t%d\t%d\t%s\t%s\n", ts, main, bat, chg, label(app), cause() }
    else if (mode == "json") print json_summary()
    else if (mode == "text") printf "%s", summary_text()
}

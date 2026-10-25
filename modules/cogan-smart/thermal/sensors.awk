# One sensor decoder for both tabs and both background workers.
# Needs thermal.awk first. Input: type temperature (millidegrees or degrees).
# Output: main_temp <TAB> zones <TAB> phone body (Badan HP), all in tenths of °C.
{
    if (NF < 2 || $NF !~ /^-?[0-9]+([.][0-9]+)?$/) next
    name = $1; t = $NF + 0
    gsub(/[^A-Za-z0-9_.+-]/, "_", name)
    v = (t >= 1000 || t <= -1000) ? int(t / 100) : int(t * 10)
    if (v == 0 || v < -400 || v > 1500 || name == "") next
    if (!(name in best)) order[++n] = name
    if (!(name in best) || v > best[name]) best[name] = v
}
END {
    zones = ""
    for (i = 1; i <= n; i++) zones = zones (i > 1 ? "," : "") order[i] "=" best[order[i]]
    printf "%d\t%s\t%d\n", main_temp(zones), zones, body_temp(zones)
}

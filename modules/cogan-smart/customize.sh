# Cogan Smart Kernel: installer step (sourced by KernelSU / Magisk with MODPATH set).
SKIPUNZIP=0
ADB=${CS_ADB:-/data/adb}   # overridden by the offline tests
DATA=$ADB/cogan_smart
ui_print "- Cogan Smart Kernel (gabungan Power Mode + Thermal Monitor)"
set_perm_recursive "$MODPATH" 0 0 0755 0644
for f in "$MODPATH"/*.sh "$MODPATH"/power/*.sh "$MODPATH"/thermal/*.sh "$MODPATH"/guard/*.sh; do set_perm "$f" 0 0 0755; done

# Keep the settings and history of the former separate modules. Copy them before their own
# uninstall.sh deletes the old folders at the next boot; runtime state (run/, locks) stays behind.
migrate() {   # migrate OLD_DIR NEW_DIR
  [ -d "$1" ] && [ ! -d "$2" ] || return 0   # only once, before the new folder exists
  mkdir -p "$2"
  for item in "$1"/*; do
    case "${item##*/}" in run|api.lock|'*') continue ;; esac
    cp -a "$item" "$2/" || { ui_print "! Gagal menyalin $item"; return 1; }
  done
  ui_print "- Setelan dan riwayat lama disalin dari $1"
}
migrate "$ADB/cogan_power" "$DATA/power"
migrate "$ADB/cogan_thermal" "$DATA/thermal"
mkdir -p "$DATA/power" "$DATA/thermal/data"

# Two controllers on the same CPU and charging nodes would fight, so the old modules go.
for old in cogan_power cogan_thermal; do
  [ -d "$ADB/modules/$old" ] || continue
  touch "$ADB/modules/$old/remove"
  ui_print "- Modul lama $old dihapus saat reboot (data sudah disalin)"
done

ui_print "- Mode bawaan: Kernel Default (badan HP dijaga ≤ 41 °C, CPU turun hanya saat prosesor bekerja, rem prosesor 95 °C)"
ui_print "- Suhu dicatat tiap 20 detik, riwayat 7 hari, log di /sdcard/Download/CoganThermal"
ui_print "- Suhu cas mengikuti sistem HP; jeda suhu modul nonaktif secara bawaan. Auto cut tetap 95/90."
ui_print "- Cogan Bridge: identitas asli + CPU QoS bila kernel mendukung ABI 1"
ui_print "- Tab Modul: periksa, whitelist dan hapus modul lain sampai ke akar"
ui_print "- Atur lewat WebUI modul; tombol Action = ganti mode"

#!/system/bin/sh
# Eksperimen Cogan Kernel (owner 1 Nov 2026): dijalankan sekali oleh ksud (KernelSU Next/BakaSU) dari
# /data/adb/boot-completed.d setelah flash ZIP eksperimen di TWRP. Memperbarui manager root yang sudah
# terpasang supaya sama versi dengan kernel, lalu menghapus dirinya. Manager yang belum terpasang (atau
# versi spoofed dengan nama paket lain) tidak disentuh, jadi tidak muncul manager kedua.
# Experiment: run once by ksud after boot; updates the installed root manager to the kernel's version,
# then removes itself. A manager that is not installed (or a spoofed one) is left alone.
ADB="${COGAN_ADB:-/data/adb}"
DIR="$ADB/cogan-manager"
APK="$DIR/manager.apk"
PKG="$(cat "$DIR/package" 2>/dev/null)"
{
  echo "$(date '+%F %T') package=$PKG"
  if [ ! -f "$APK" ] || [ -z "$PKG" ]; then
    echo "skip: nothing staged"
  elif ! pm path "$PKG" >/dev/null 2>&1; then
    echo "skip: $PKG not installed (install the manager from Android, or a spoofed manager is in use)"
  else
    # Streamed through stdin: the package manager cannot read files in /data/adb itself.
    pm install -r -S "$(stat -c %s "$APK")" < "$APK"
    echo "pm install exit: $?"
  fi
} >> "$DIR/log.txt" 2>&1
rm -f "$APK" "$DIR/package" "$0"

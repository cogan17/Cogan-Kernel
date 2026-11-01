### Eksperimen (owner 1 Nov 2026): manager root ikut ZIP kernel, hanya di artifact, tidak dirilis.
## Dijalankan anykernel.sh di TWRP setelah flash_boot. Tidak memasang apa pun di recovery (TWRP tidak bisa
## memasang aplikasi): APK dan skrip boot-completed disiapkan di /data/adb, lalu saat HP menyala KernelSU
## Next/BakaSU (ksud) memperbarui manager yang SUDAH terpasang dengan versi yang cocok dengan kernel ini.
## Experiment: the root manager rides in the kernel ZIP (artifact only). TWRP cannot install apps: this only
## stages the APK and a boot-completed script; at boot ksud updates an already installed manager.
## Tiap kegagalan hanya dilewati: flash kernel tetap berhasil / every failure is skipped, the flash succeeds.

cogan_manager() {
  local adb="${COGAN_ADB:-/data/adb}" src="$AKHOME/cogan" pkg dir
  pkg="$(cat "$src/package" 2>/dev/null)"
  [ -n "$pkg" ] && [ -f "$src/manager.apk" ] || { ui_print "Eksperimen: manager tidak ada di ZIP / no manager in the ZIP"; return 0; }
  # /data/adb/ksud exists only when /data is readable here and the root manager was opened once in Android.
  if [ ! -f "$adb/ksud" ]; then
    ui_print "Eksperimen: /data tidak terbaca atau manager belum pernah dibuka;" \
             "  pasang APK manager dari Android / /data unreadable or manager never opened: install the APK in Android"
    return 0
  fi
  dir="$adb/cogan-manager"
  if mkdir -p "$dir" "$adb/boot-completed.d" \
     && cp -f "$src/manager.apk" "$dir/manager.apk" \
     && echo "$pkg" > "$dir/package" \
     && cp -f "$src/cogan-manager-boot.sh" "$adb/boot-completed.d/cogan-manager.sh"; then
    chmod 700 "$dir"; chmod 600 "$dir/manager.apk" "$dir/package"; chmod 755 "$adb/boot-completed.d/cogan-manager.sh"
    chcon -R u:object_r:adb_data_file:s0 "$dir" "$adb/boot-completed.d/cogan-manager.sh" 2>/dev/null
    ui_print "Eksperimen: manager $pkg diperbarui saat HP menyala" \
             "  Experiment: manager $pkg is updated at boot" \
             "  (log: /data/adb/cogan-manager/log.txt)"
  else
    rm -rf "$dir" "$adb/boot-completed.d/cogan-manager.sh"
    ui_print "Eksperimen: gagal menyiapkan, dilewati / could not stage, skipped"
  fi
  return 0
}
cogan_manager

# Cogan Smart Kernel v2.8.2

## Penyesuaian HyperCharge / HyperCharge adjustment — v2.8.2

Indonesia:

- Menambahkan pengaturan "Jeda cas karena suhu oleh modul", nonaktif secara
  bawaan. Pengelolaan suhu dan daya pengisian tetap diserahkan kepada sistem HP.
- Memperbaiki batas baterai 42 °C yang sebelumnya tetap bisa menjeda cas walaupun
  opsi jeda karena panas prosesor dimatikan. Kedua pemicu suhu modul kini hanya
  bekerja jika pengguna mengaktifkan pengaturan jeda suhu tambahan.
- Auto cut charging berdasarkan persentase tetap bekerja, dengan bawaan berhenti
  95% dan lanjut 90%. Batas yang pernah disimpan pengguna tetap dipertahankan.
- Konfigurasi lama tanpa CHARGE_THERMAL otomatis memakai kebijakan baru (0).
  Tidak perlu reset; nilai ambang lama tetap disimpan untuk opsi jeda tambahan.
- Kolom ambang baterai dan jeda panas prosesor tidak aktif ketika jeda suhu modul
  dimatikan. WebUI menampilkan kebijakan cas yang sedang digunakan dalam ID/EN.
- Modul tidak mencari/menguji saklar karena panas saja saat kebijakan bawaan
  digunakan. Pencarian manual tetap tersedia, dengan keterangan bahwa pengujian
  mematikan dan menyalakan cas sebentar.
- Pengendalian CPU, pemantauan suhu, serta perbaikan AWK v2.8.1 tetap disertakan.
  Pembaruan ini tidak menonaktifkan driver termal atau mengubah negosiasi charger,
  arus, maupun tegangan pengisian.
- Pengujian: pengendali dengan sysfs tiruan, One True Awk, siklus 95/90,
  konfigurasi lama, jeda suhu opsional, dan penghormatan terhadap saklar yang
  dijeda pengendali lain. Alur UI dan bahasa diuji dengan model DOM.
  Belum diuji langsung dengan HyperCharge 120 W pada perangkat fisik.

English:

- Adds "Module temperature-based charging pauses", disabled by default.
  Charging temperature and power management remain with the phone system.
- Fixes the 42 °C battery limit still pausing charging when the separate CPU-heat
  pause was disabled. Both module heat triggers now require explicit opt-in.
- Percentage-based automatic cutoff remains enabled: 95% stop and 90% resume by
  default. Previously saved percentage limits are preserved.
- Older configurations without CHARGE_THERMAL automatically use the new policy
  (0). No reset is required; previous thresholds are retained for optional use.
- Battery threshold and CPU-heat pause fields are inactive when module heat
  pauses are off. The current charging policy is shown in both ID and EN.
- Heat alone no longer starts switch detection under the default policy. Manual
  detection remains available and explains that it briefly toggles charging.
- CPU control, temperature monitoring, and the v2.8.1 AWK fix are retained.
  This update does not disable thermal drivers or change charger negotiation,
  charging current, or charging voltage.
- Validation covers an isolated sysfs controller, One True Awk, 95/90 hysteresis,
  older configurations, optional heat pauses, and respect for a charging switch
  held by another controller. UI/language flows use a DOM model.
  Not yet tested with 120 W HyperCharge on a physical device.

## Perbaikan v2.8.1 / v2.8.1 fix

Indonesia:

- Memperbaiki `syntax error` pada fungsi `json_now` yang membuat tab Suhu gagal
  membaca data di AWK Android. Perbandingan kondisi dipisahkan dari daftar argumen
  `printf`; keluaran dan format data tetap sama.
- Menambahkan tanda kurung pada ekspresi pemisah JSON untuk konsistensi parser.
- Versi aset dan cache WebUI diperbarui agar halaman memuat kode terbaru.
- Error v2.8 berhasil direproduksi pada One True Awk 20251225. Versi perbaikan
  diuji pada interpreter tersebut dan mawk untuk pembacaan suhu, status pencatat,
  start/stop, ringkasan, dan ekspor TXT/CSV dalam dua bahasa.

English:

- Fixes the Android AWK `syntax error` in `json_now` that prevented the
  Temperature tab from reading data. The conditional comparison is evaluated
  outside the `printf` argument list; output and data formats are unchanged.
- Parenthesises JSON separator expressions for parser consistency.
- Updates WebUI asset and cache versions so pages load the latest code.
- The v2.8 failure was reproduced with One True Awk 20251225. The fix was tested
  with that interpreter and mawk for live temperatures, recorder status,
  start/stop, summaries, and bilingual TXT/CSV exports.

## Perubahan v2.8 / v2.8 changes

## Indonesia

- Tab Daya dan Suhu memakai decoder sensor serta snapshot pembacaan yang sama
  (maksimum 2 detik). Pengendali latar tetap membaca sensor langsung.
- Status pencatat berasal dari pemeriksaan PID dan umur sampel yang sama di kedua
  tab. Pencatat berhenti, sampel pertama dan sampel terlambat dibedakan. Toleransi
  umur sampel mengikuti interval pencatatan, termasuk interval 300 detik.
- Suhu langsung dan umur catatan aktivitas ditampilkan terpisah. Sensor yang tidak
  tersedia tidak digantikan oleh suhu dari riwayat lama.
- Pembaruan data dimulai lagi setelah halaman WebUI kembali dari cache navigasi.
- Pilihan Indonesia/English berlaku di seluruh tab, tombol, pesan, ringkasan,
  serta ekspor log TXT/CSV. Cache jawaban dipisahkan menurut bahasa dan versi UI.
- Pembacaan aktivitas melalui dumpsys dibatasi waktunya ketika timeout tersedia.
- ID modul tetap `cogan_smart`; pengaturan dan riwayat yang sudah ada dipertahankan.

Pembaruan: pasang ZIP ini sebagai pembaruan modul melalui root manager, reboot,
lalu tutup dan buka kembali WebUI. Bahasa dipilih di halaman Tentang.

Validasi: skrip shell dan JSON diuji pada sysfs/proc tiruan; alur WebUI diuji
dengan model DOM untuk API exec dan spawn. Termasuk start/stop pencatat,
sampel terlambat, pemulihan navigasi, pergantian bahasa dan ekspor log.
Belum diuji langsung di Xiaomi 14T Pro atau dirender dengan browser Android.

## English

- Power and Temperature share one sensor decoder and a snapshot lasting at most
  two seconds. Background controllers continue to read hardware directly.
- Both tabs use the same recorder PID and sample freshness checks. Stopped,
  starting and delayed recording states are distinct; freshness follows the
  configured recording interval, including 300 seconds.
- Live temperature and recorded activity age are labelled separately. Missing
  live sensors no longer fall back to historical temperatures.
- Polling resumes when WebUI returns from the back/forward navigation cache.
- Indonesia/English selection applies across every tab, buttons, feedback,
  summaries and TXT/CSV exports. Response caches are scoped by language and UI version.
- Activity reads use bounded dumpsys calls when timeout is available.
- Module ID remains `cogan_smart`; existing settings and history are retained.

Update: install this ZIP as a module update in your root manager, reboot, then
close and reopen WebUI. Choose the language on the About page.

Validation: shell/JSON checks with isolated sysfs/proc fixtures and functional
WebUI tests using a DOM model with both exec and spawn APIs. Recorder lifecycle,
delayed samples, navigation recovery, language persistence and exports are covered.
Not tested on a physical Xiaomi 14T Pro or rendered in an Android browser.

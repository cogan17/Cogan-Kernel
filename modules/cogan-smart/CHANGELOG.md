# Cogan Smart Kernel v2.9.0

## Mode mengikuti Badan HP / Modes follow the phone body — v2.9.0

Indonesia:

- Ambang Hemat, Kernel Default dan Performa kini dibaca dari suhu **Badan HP** (sensor
  kulit HP, yang terasa di tangan), bukan prosesor terpanas. Prosesor Dimensity HP ini
  saat santai pun sekitar 50 °C: dari log 3 hari owner (8.340 sampel), ambang 42 °C pada
  prosesor terlewati 97% waktu, sehingga Kernel Default menurut kodenya membatasi CPU
  besar ke 40% hampir sepanjang waktu (dihitung dari log, belum diukur di HP).
- Ambang baru: Hemat 40 °C, Kernel Default 42 °C, Performa 45 °C (Badan HP).
- Langkah halus (owner: "se-smooth mungkin"): mulai 1 °C sebelum ambang dengan dua langkah
  ringan saja; di ambang, CPU besar (X4) turun 10% per langkah sampai 60%, lalu CPU kecil
  (A720, yang menjaga UI tetap lancar) ke 90% dan 80%. Batas terdalam 60/80%, bukan 40%.
  Badan HP berubah pelan, jadi tiap langkah ditunggu tiga kali cek; naik lagi setelah tiga
  kali cek ≥ 1,5 °C di bawah ambang. Hemat tetap turun dari batasnya sendiri.
- CPU hanya diturunkan saat prosesor bekerja (≥ 60 °C). Panas dari cas (HyperCharge),
  ruangan atau HP yang santai tidak didinginkan oleh batas CPU, dan batas yang tertinggal dari
  saat itu hanya memperlambat pemakaian berikutnya; saat prosesor santai batasnya dilepas
  bertahap (owner, setelah uji HP 24 Okt: 3 jam data dengan HyperCharge 9,2 A).
- Simulasi saat layar menyala: data 3 jam owner, CPU penuh ±89% waktu (sebelumnya ±53%) dan
  tidak pernah ≤ 60%; log 3 hari, CPU penuh ±95% (sebelumnya ±75%).
- Jeda cas karena suhu oleh modul tetap **mati secara bawaan** (owner: HyperCharge yang
  mengatur); setelan yang tersimpan tidak diubah.
- GPU: tab Daya membaca node GPU HP ini (devfreq Mali, GED, gpufreqv2) dan menampilkannya di
  Kontrol kernel. **Baca saja**, tidak ada yang ditulis; batas GPU untuk game dipasang
  setelah node ini terbukti di HP.
- Rem darurat di semua mode: bila prosesor ≥ 95 °C, CPU diturunkan setiap cek.
- Tanpa sensor Badan HP, suhu baterai yang dipakai.
- Ambang suhu dari konfigurasi v2.8 dan sebelumnya (masih bermakna prosesor) diganti
  dengan bawaan baru. Mode, setelan cas dan interval tetap seperti yang disimpan.
- Tab Suhu: "panas" berarti Badan HP ≥ 42 °C (dari log owner: ±9% waktu, sebelumnya
  97%). Penyebab panas, grafik, serta rata-rata/tertinggi per aplikasi, kernel dan mode
  memakai Badan HP. Notifikasi panas juga membaca Badan HP. Prosesor tetap tampil di
  kotak Tertinggi dan tabel Bagian HP, dengan warna untuk komponen dalam (70/85 °C).
- Tab Daya menampilkan Badan HP sebagai suhu utama, prosesor di sebelahnya, dan
  penanda rem darurat. Jeda cas karena panas (opsional) juga memakai Badan HP.
- Pengujian: tes pengendali dan pencatat dengan sysfs tiruan, memakai mksh dan
  One True Awk 20231127. Simulasi pada log 3 hari dan data 3 jam owner. Uji HP owner
  (24 Okt, versi sebelum aturan "prosesor bekerja"): Badan HP terbaca dari `quiet_therm`,
  tab Daya/Suhu/Modul tampil, saklar cas `input_suspend` ditemukan.

English:

- Power saver, Kernel Default and Performance thresholds now read the **phone body**
  temperature (the skin sensor, what a hand feels) instead of the hottest processor
  sensor. This Dimensity processor sits around 50 °C even at rest: in the owner's 3-day
  log (8,340 samples) a 42 °C processor threshold was exceeded 97% of the time, so by its
  code Kernel Default capped the big cores at 40% almost all the time (computed from the
  log, not measured on the phone).
- New thresholds: Power saver 40 °C, Kernel Default 42 °C, Performance 45 °C (phone body).
- Smooth steps (owner: "as smooth as possible"): from 1 °C before the threshold only two
  light steps; at the threshold the big cores (X4) drop 10% per step down to 60%, then the
  little cores (A720, which keep the interface fluid) to 90% and 80%. The deepest step is
  60/80%, not 40%. The phone body changes slowly, so each step waits three checks; the
  CPU steps back up after three checks at least 1.5 °C below the threshold. Power saver
  still steps down from its own cap.
- The CPU is only lowered while the processor works (60 °C or more). Heat from charging
  (HyperCharge), the room or an idle phone is not cooled by a CPU cap, and a cap kept from
  then only slows the next use; with an idle processor the cap is released step by step
  (owner, after the phone test on 24 Oct: 3 hours of data with 9.2 A HyperCharge).
- Simulated with the screen on: the owner's 3-hour data, full CPU about 89% of the time
  (previously about 53%) and never at 60% or less; the 3-day log, full CPU about 95%
  (previously about 75%).
- Module charging heat pauses stay **off by default** (owner: HyperCharge is in charge);
  saved settings are not changed.
- GPU: the Power tab reads this phone's GPU nodes (Mali devfreq, GED, gpufreqv2) and shows
  them under Kernel controls. **Read only**, nothing is written; a GPU limit for games comes
  once these nodes are proven on the phone.
- Emergency brake in every mode: at a processor temperature of 95 °C or more, the CPU
  steps down at every check.
- Without a phone body sensor, the battery temperature is used.
- Temperature thresholds from v2.8 and older configurations (which meant the processor)
  are replaced by the new defaults. Mode, charging settings and interval are kept.
- Temperature tab: "hot" means phone body ≥ 42 °C (owner's log: about 9% of the time,
  previously 97%). Heat causes, the chart and per-app, per-kernel and per-mode
  average/peak use the phone body. The heat notification reads the phone body too. The
  processor still shows in the Peak tile and the components table, coloured for internal
  parts (70/85 °C).
- The Power tab shows the phone body as the main temperature, the processor beside it,
  and an emergency-brake marker. The optional heat-based charging pause uses the phone
  body as well.
- Validation: controller and recorder tests on a fake sysfs with mksh and One True Awk
  20231127, plus simulations on the owner's 3-day log and 3-hour data. Owner's phone test
  (24 Oct, the version before the "processor works" rule): the phone body reads from
  `quiet_therm`, the Power/Temperature/Modules tabs work, charging switch `input_suspend` found.

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

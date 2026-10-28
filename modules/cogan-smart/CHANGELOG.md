# Cogan Smart Kernel

## Kenali DRAM MediaTek / Identify MediaTek DRAM — v2.10.5 (paket uji / test build)

Indonesia:

- Hasil perintah owner mengidentifikasi DRAM sebagai mtk-dvfsrc-devfreq dengan governor userspace; UFS memakai ufshcd-mtk/simple_ondemand dan GPU mali/dummy. Ketiganya menampilkan daftar governor yang sama tanpa bw_hwmon. userspace adalah bacaan aktual, bukan bukti kegagalan profil ZRAM.
- Manager mengenali DRAM lewat ikatan device/driver yang tepat, menampilkan driver dan governor terbaca, serta menyembunyikan dropdown BW bila tidak ada pilihan yang dapat dipakai. Pilihan BW lama yang kini tidak tersedia tetap bisa dikembalikan ke DRAM Sistem.
- Perbaiki sasaran penulisan BW: daftar available_governors devfreq dapat bersifat global. UFS, GPU, dan perangkat lain tidak lagi menjadi target hanya karena nama governor muncul dalam daftar. Validasi, readback dan pemulihan kepemilikan tetap berlaku.
- Tetap gunakan pengaturan DRAM sistem; tidak mengganti userspace dengan simple_ondemand/performance/powersave, menebak OPP atau mengubah driver/termal. Ini perbaikan deteksi dan antarmuka, bukan port bw_hwmon ke MediaTek atau klaim peningkatan performa.
- Bukti HP v2.10.4 menunjukkan zram0: lz4 dengan swap aktif. Belum ada bukti ZSTD berhasil atau gagal setelah reboot. Integrasi ZRAM v2.10.4 tetap disertakan; tidak perlu kernel baru untuk perbaikan deteksi ini. v2.10.5 belum diuji di HP.

English:

- The owner's command output identifies DRAM as mtk-dvfsrc-devfreq with the userspace governor; UFS uses ufshcd-mtk/simple_ondemand and the GPU uses mali/dummy. All three show the same governor list without bw_hwmon. userspace is the actual readback, not evidence that the ZRAM profile failed.
- Identify DRAM through its exact device/driver binding, show its driver and current governor, and hide the BW dropdown when there is no usable choice. A previously saved BW choice that is now unavailable can still be returned to System DRAM.
- Correct BW write targets: devfreq available_governors can be global. UFS, GPU and other devices are no longer targets merely because a governor appears in that list. Validation, readback and ownership restoration remain in place.
- Preserve system DRAM settings; do not switch userspace to simple_ondemand/performance/powersave, guess OPPs or modify drivers/thermal controls. This is a detection and UI fix, not a MediaTek bw_hwmon port or a performance improvement claim.
- The v2.10.4 phone screenshot shows zram0: lz4 with active swap. There is no post-reboot evidence of ZSTD success or failure yet. The v2.10.4 ZRAM integration remains included; this detection fix needs no new kernel. v2.10.5 has not been phone-tested.

## Integrasi ZRAM sebelum inisialisasi / ZRAM integration before initialization — v2.10.4 (paket uji / test build)

Indonesia:

- Pilihan RAM + Terapkan saat boot membuat initrc di dalam modul dan menyegarkan cache melalui ksud initrc refresh. Aturan init, early-fs dan post-fs berjalan lewat hook bawaan KernelSU Next/BakaSU sebelum hook modul post-fs-data. Tidak menambah skrip global atau daemon.
- Aturan memeriksa properti rothko/mt6989, Cogan Bridge ABI 1, device/SoC/release, dukungan algoritme seluruh ZRAM, serta initstate=0 sebelum menulis. ZRAM aktif tetap tidak direset, swap tidak dimatikan, ukuran dan writeback tidak diubah.
- Bila sistem sudah mengaktifkan mmd, siapkan hanya mmd.zram.comp_algorithm lewat system.prop. Tidak mengaktifkan mmd, memanggil setprop pada hook post-fs-data atau mengganti kebijakan memori lain.
- Manager menampilkan kesiapan initrc/mmd, hasil hook pada boot ini dan error sinkronisasi. Algoritme serta status swap tetap dibaca dari kernel, bukan disimpulkan dari keberhasilan penyimpanan.
- Menonaktifkan penerapan boot atau Ikuti kernel menghapus aturan milik modul dan menyegarkan cache. Root manager menangani pengecualian modul yang dinonaktifkan/dihapus. Isi system.prop/initrc lain tidak ditimpa; kegagalan refresh memulihkan aturan sebelumnya dan dilaporkan.
- Selama pembaruan modul masih menunggu reboot, perubahan setelan diblokir agar cache tidak memakai salinan staged yang berbeda. Reset tetap memulihkan kontrol berjalan meski sinkronisasi init gagal.
- Hook modules.rc sudah ada pada commit root kedua varian rilis Cogan r5 (riwayat run 40538599681). Perubahan ini memakai dukungan tersebut; tidak mengganti Image kernel, partisi boot, KMI, root manager atau driver ZRAM vendor.
- Bila pilihan boot sudah tersimpan sebelum pembaruan, installer menyiapkannya untuk reboot pemasangan. Jika pilihan diubah setelahnya, Simpan lalu reboot satu kali. Hasil HP masih perlu dikonfirmasi melalui hasil hook dan algoritme aktual; belum ada klaim penghematan RAM/performa.

English:

- RAM selection plus Apply at boot generates module-owned initrc and refreshes the cache with ksud initrc refresh. Init, early-fs and post-fs actions use the existing KernelSU Next/BakaSU hook before module post-fs-data. No global boot script or daemon is added.
- Actions check rothko/mt6989 properties, Cogan Bridge ABI 1, device/SoC/release, algorithm support across every ZRAM device, and initstate=0 before writing. Live ZRAM is not reset, swap is not disabled, and size/writeback are unchanged.
- When the system already enables mmd, prepare only mmd.zram.comp_algorithm through system.prop. Do not enable mmd, call setprop during post-fs-data or change other memory policies.
- Manager shows initrc/mmd preparation, this boot's hook result and synchronization errors. The actual algorithm and swap activity are still read from the kernel, not inferred from saved settings.
- Disabling boot application or following the kernel removes module-owned rules and refreshes the cache. The root manager excludes disabled/removed modules. Unrelated property/RC contents are preserved; refresh failures restore prior rules and are reported.
- Block settings changes while a module update awaits reboot so the cache cannot silently select a different staged copy. Reset still restores live controls when init synchronization fails.
- The root commits for both Cogan r5 variants already contain the modules.rc hook (history run 40538599681). Reuse it without replacing the kernel Image, boot partition, KMI, root manager or vendor ZRAM driver.
- A boot choice saved before updating is prepared by the installer for the installation reboot. After later changes, save and reboot once. Phone results still need hook/algorithm readback confirmation; there are no RAM/performance gain claims.

## RAM sesuai dukungan perangkat / RAM controls follow device support — v2.10.3 (paket uji / test build)

Indonesia:

- Pisahkan kompresi ZRAM (Snappy LZ4 / Heavy ZSTD) dari governor DRAM (Sistem / bw_hwmon). Pemilihan kompresor tidak lagi diam-diam mengubah devfreq; pilihan bw_hwmon ditolak bila tidak tersedia, sebelum kontrol lain ditulis.
- Konfigurasi lama tanpa BW mengikuti DRAM Sistem. Governor devfreq yang dahulu tercatat milik Manager dipulihkan melalui jurnal yang sama, tanpa menimpa nilai berbeda dari pengendali lain.
- RAM menampilkan status pilihan mengikuti sistem, sesuai bacaan, belum diterapkan, menunggu boot, tidak didukung, atau percobaan boot yang belum berhasil. Toast memakai status yang sama; selesai memproses tidak lagi dianggap semua profil telah aktif.
- Pilihan algoritme yang sama dengan bacaan tidak membuktikan modul menggantinya. Tampilkan status swap dari /proc/swaps secara terpisah; data hilang ditandai belum terbaca.
- Setelah satu percobaan boot yang belum menghasilkan kompresor pilihan, tampilkan batas integrasi init/kernel, bukan menyuruh restart berulang. ZRAM aktif tidak di-reset, swap tidak dimatikan dan pengaturan DRAM MediaTek tidak ditebak.
- SS owner membuktikan policy CPU terbaca sugov_ext, zram0 terpilih lz4 dan bw_hwmon tidak tersedia. SS tidak membuktikan bahwa modul mengganti LZ4 atau swap aktif. Gunakan DRAM Sistem pada kondisi tersebut. Paket pembaruan belum diuji di HP.

English:

- Separate ZRAM compression (Snappy LZ4 / Heavy ZSTD) from the DRAM governor (System / bw_hwmon). Selecting compression no longer implicitly changes devfreq; unavailable bw_hwmon requests fail before other controls are written.
- Old configs without BW follow System DRAM. Restore devfreq nodes previously recorded as Manager-owned through the existing journal, preserving differing values from other controllers.
- RAM distinguishes system, matching readback, not applied, pending boot, unsupported and unsuccessful boot attempts. The toast uses the same state; processing a request no longer implies that every profile is active.
- A matching algorithm does not prove that the module changed it. Show swap activity from /proc/swaps separately; missing data remains unknown.
- After one boot attempt fails to produce the selected compressor, explain the init/kernel integration limit instead of suggesting repeated restarts. Do not reset live ZRAM, disable swap or guess MediaTek DRAM controls.
- The owner's screenshot shows CPU policies reading sugov_ext, zram0 selecting lz4 and no available bw_hwmon. It does not prove a module-induced LZ4 change or active swap. Use System DRAM in that situation. This update is not phone-tested.

## Tab sejajar / Aligned tabs — v2.10.2 (paket uji / test build)

Indonesia:

- Ikon berada di atas dan judul di bawah pada keempat tab. Area ikon, jarak dan tinggi tab disamakan; judul Manager tidak lagi pindah baris sendiri.
- Satu gaya navigasi dipakai Daya, Suhu, Manager, Modul dan Tentang. Font besar dapat menggulir navigasi ke samping tanpa memotong judul; fokus keyboard tetap terlihat.
- Perbaikan pemindai v2.10.1 tetap disertakan. Backend CPU/RAM dan termal tidak diubah.
- Pindah tab, pindai aplikasi dan menerapkan governor CPU yang didukung tidak memerlukan restart. Simpan hanya menyimpan pilihan; Terapkan sekarang mencoba menerapkannya. Kompresor ZRAM aktif tidak direset; opsi saat boot mencoba sebelum inisialisasi, tanpa menjanjikan perubahan pasti setelah reboot.
- Setelah memasang ZIP pembaruan lewat root manager, reboot satu kali. Tata letak dan fungsi pada HP owner belum dikonfirmasi untuk paket ini.

English:

- All four tabs place the icon above the label. Icon areas, spacing and tab heights match; Manager no longer wraps onto a separate row by itself.
- Power, Temperature, Manager, Modules and About share one navigation style. Large fonts can scroll the navigation horizontally without clipping labels; keyboard focus remains visible.
- Includes the v2.10.1 app scanner fixes. CPU/RAM and thermal backends are unchanged.
- Switching tabs, scanning apps and applying a supported CPU governor do not need a restart. Save only stores choices; Apply now attempts to apply them. Active ZRAM is never reset; boot application tries before initialization without guaranteeing a compressor change after reboot.
- Reboot once after installing the module update through the root manager. This package's layout and functions have not been confirmed on the owner's phone.

## Perbaikan pemindai aplikasi / App scanner fixes — v2.10.1 (paket uji / test build)

Indonesia:

- Hasil dumpsys yang terpotong karena timeout atau ditolak izin tidak lagi menghasilkan saran, termasuk saat kode proses 0. Respons kosong juga membatalkan pemindaian.
- Gagal membaca proses membatalkan saran. Gunakan ps native Android bila tersedia agar variasi opsi BusyBox tidak menghilangkan perlindungan aplikasi yang berjalan.
- Atur deadline dumpsys langsung (20 detik), dengan batas luar 25 detik. Kegagalan menyebut tahap, kode proses dan rincian singkat; pesan tetap terlihat di Manager setelah notifikasi menghilang.
- Tambah pemeriksaan regresi untuk kegagalan, respons kosong, penolakan izin dan timeout di setiap tahap; integrasi CPU/RAM, termal dan jalur info aplikasi Android dipertahankan.
- Owner melaporkan pemindaian gagal pada v2.10.0. Penyebab perintah yang gagal di HP belum diketahui karena pesan lama menggabungkan semua tahap. Pembaruan ini sudah diperiksa lokal; hasil pada HP belum dikonfirmasi.

English:

- Dumpsys results interrupted by timeout or denied permission no longer produce suggestions, even with exit code 0. Empty responses also abort the scan.
- Failed process reads abort suggestions. Prefer Android's native ps where available so BusyBox option differences cannot silently remove running-app protection.
- Set dumpsys' own 20-second deadline with a 25-second outer limit. Errors identify the stage, exit code and a short detail; Manager keeps the message visible after the notification disappears.
- Add regression coverage for failed, empty, denied and timed-out reads at every stage. CPU/RAM integration, thermal controls and Android app info remain intact.
- The owner reported a scan failure on v2.10.0. The exact failing phone command is unknown because the old error merged all stages. This update has local checks; its phone result is not yet confirmed.

## Manager CPU/RAM dan kontrol terpusat / CPU/RAM Manager and centralized controls — v2.10.0 (pengembangan / development)

Indonesia:

- Tab Manager dengan dropdown Prosesor (sugov_ext/schedutil sesuai dukungan semua policy) dan RAM: Snappy & Daily Driver (bw_hwmon + LZ4), Heavy Multitasker / Space Saver (bw_hwmon + ZSTD).
- CPU/RAM hanya ditulis bila perangkat rothko, platform mt6989 dan Cogan Bridge cocok. bw_hwmon hanya pada driver yang menyediakannya; governor memori bawaan dipertahankan bila tidak tersedia.
- ZRAM yang sedang aktif tidak di-reset atau dimatikan. Kompresor dicoba sebelum inisialisasi melalui opsi boot; UI tetap menunjukkan kompresor aktual dan status belum diterapkan jika terlambat.
- Tombol Simpan/Terapkan/Reset/Hentikan dari Daya dan Suhu, serta Hapus riwayat, dipusatkan di Manager. Draf kolom bertahan saat pindah tab; Simpan log tetap di Suhu.
- Pindai manual aplikasi user yang punya bukti tidak dipakai ≥ 7 hari. Aplikasi baru, proses aktif dan data tak cukup tidak menjadi saran. Info aplikasi Android menangani pilihan uninstall/nonaktifkan.
- Nilai governor awal dicatat per boot dan dipulihkan tanpa menimpa kontrol pihak lain. Backend Daya, pencatat Suhu, rem termal dan ABI kernel tidak diganti.
- Belum diuji pada HP sungguhan; tidak mengklaim penghematan RAM, peningkatan performa atau kompatibilitas bw_hwmon pada hardware owner.

English:

- Manager tab with a Processor dropdown (sugov_ext/schedutil when supported across every policy) and RAM profiles: Snappy & Daily Driver (bw_hwmon + LZ4), Heavy Multitasker / Space Saver (bw_hwmon + ZSTD).
- CPU/RAM writes require a matching rothko device, mt6989 platform and Cogan Bridge. bw_hwmon is used only where the driver advertises it; otherwise the memory governor is retained.
- Active ZRAM is never reset or disabled. Optional boot application tries compression before initialization; the UI still shows the actual compressor and a pending state if it is too late.
- Power/Temperature Save/Apply/Reset/Stop controls and Clear history move to Manager. Edited fields survive tab changes; Save logs stays in Temperature.
- On-demand review of user apps with evidence of at least seven idle days. New apps, running processes and insufficient data are excluded from suggestions. Android app info handles uninstall/disable choices.
- Initial governors are recorded per boot and restored without overwriting other controllers. Power, Temperature recording, thermal limits and the kernel ABI remain intact.
- Not tested on a physical phone. No claimed RAM savings, performance gains or bw_hwmon compatibility on the owner's hardware.

## Modul lebih hemat CPU, satu angka Badan HP, lonjakan suhu, nama aplikasi, batas CPU / A lighter module, one phone body number, temperature rises, app names, CPU cap — v2.9.1

Indonesia:

- Modul jauh lebih hemat CPU. Log 6 jam owner dengan build uji v2.9.1 pertama (25 Okt, 07.22–11.24
  WIB) menunjukkan pencatat dan pengendali memakai rata-rata 4,8% CPU seluruh HP, sama di semua
  aplikasi dan saat layar mati. Penyebabnya, tiap putaran menjalankan puluhan proses kecil: `cat` untuk
  tiap antarmuka jaringan, `awk`, `sed` dan `dumpsys`.
  - Kini file dibaca dengan builtin shell, dan nama proses diingat.
  - `dumpsys` hanya dijalankan saat aplikasi di depan berganti, paling lambat tiap 2 menit.
  - Badan HP ikut dari satu pembacaan sensor.
  - 40 sampel terakhir (untuk sensor macet) hanya dibaca tiap 5 menit.
  - Diukur di HP tiruan berbentuk rothko (60 sensor, 25 antarmuka jaringan):
    - pencatat: dari ±94 menjadi ±12 proses per sampel;
    - pengendali: dari 62 menjadi 15 proses per putaran (jalur kernel stok; dengan Cogan Bridge lebih sedikit lagi).
  - Angka di HP belum diukur. Perilaku pengendali tidak berubah.
- Pengendali lebih hemat lagi (owner 26 Okt). Log 3 jam dengan build hemat CPU (25 Okt, 12.06–14.49 WIB):
  beban modul turun dari 4,8% menjadi 2,9% CPU HP (pencatat 1,5%, pengendali 1,4%).
  - Kini pengendali hanya membaca sensor CPU/GPU dan angka Badan HP (HyperOS, atau sensor kulit), bukan
    ±60 sensor, dan tanpa `awk` tiap 10 detik.
  - Daftar sensornya dicari sekali saat mulai dan tiap jam, dengan pengelompokan yang sama seperti tab Suhu.
  - Di HP tiruan berbentuk rothko: file sensor yang dibuka per putaran dari 100 menjadi ±26.
  - Angkanya sama dengan tab Suhu (diuji).
- CPU kini juga diturunkan saat prosesor bekerja mulai 55 °C, sebelumnya 60 °C (owner 26 Okt). Saat
  scroll Instagram (log 3 jam, 14.16–14.37 WIB) prosesor rata-rata 56 °C dan Badan HP 42–43,9 °C,
  tetapi CPU hanya diturunkan di 4 dari 107 sampel. Dengan 55 °C, syarat itu terpenuhi di ±69% sampel
  Instagram tersebut (dihitung dari log, belum diukur di HP). Langkahnya tetap halus: mulai 1 °C sebelum
  ambang, CPU besar 90% lalu 80%. Ambang 41 °C tidak berubah.
- Penyebab baru "HP baru dinyalakan" untuk 5 menit pertama setelah HP menyala. Owner 25 Okt: memasang
  v2.9.1 lalu restart, Badan HP naik 37,3 → 43,0 °C, dan laporan menulis "Aplikasi berat: Layar
  utama". Pencatat menandai sampel pertama setelah restart (penghitung CPU mulai lagi).
- Lonjakan suhu: ringkasan menampilkan kenaikan Badan HP ≥ 2 °C dalam 5 menit beserta penyebab
  dan sarannya, walau belum sampai "panas" (owner 25 Okt: Badan HP 37,1 → 40,9 °C dalam ±3 menit
  dan ringkasan hanya menulis "tidak ada momen panas"). Paling banyak tiga lonjakan terbesar.
- Penyebab baru "Pembaruan aplikasi": Play Store atau pemasang paket di layar, atau memakai CPU ≥ 3%,
  dengan saran mengatur pembaruan otomatis Play Store. Di data owner: unduh sampai 9,5 MB/s lalu
  memasang, CPU 70–85%.
- Beban Cogan Smart: tiap sampel mencatat CPU yang dipakai pencatat dan pengendali modul, termasuk
  proses anak yang sudah selesai (awk, dumpsys…), yang tidak terlihat di daftar proses teratas.
  Ringkasan menulis rata-ratanya dan bagian pengendali (CSV: `beban_modul_persen`,
  `beban_pengendali_persen`). WebUI yang sedang dibuka tidak termasuk.
- Saran "Grafis berat" kini juga untuk video dan animasi saat scroll terus-menerus, bukan hanya game.
  Prosesor yang bekerja saat layar mati ditulis sebagai proses latar belakang, bukan "Aplikasi berat:
  Layar mati".
- Satu angka Badan HP di semua tempat: suhu badan milik HyperOS sendiri (`hyperos_board`, dari
  `board_sensor_temp`) bila ada, lalu sensor kulit terpanas, lalu baterai. Tab Daya, tab Suhu,
  kartu Rem HyperOS, log dan pengendali memakai angka yang sama. Owner: "suhu masih inkonsistensi".
  Dari CSV 6 jam owner (1.257 sampel): angka HyperOS rata-rata 0,1 °C di bawah `quiet_therm` dan
  90% waktu dalam −0,7…+0,3 °C, jadi ambang 39/41/44 °C tetap.
- Naik-turun: dari data yang sama, perubahan antar-sampel kecil (90% di bawah 0,3 °C); lompatan
  besar terjadi saat prosesor bekerja keras (baterai ikut naik) atau saat HP tidur/reboot, ketika
  log berhenti 3–5 menit. Grafik kini terputus pada jeda itu, bukan menarik garis curam, dan
  memakai rata-rata tiap potongan waktu, bukan puncaknya; suhu tertinggi tetap di kotak Tertinggi.
- Nama aplikasi asli di tab Suhu, ringkasan dan log yang disimpan. Nama diambil dari root manager
  (KernelSU Next dan BakaSU sama-sama menyediakan `getPackagesInfo`), paling sering tiap 6 jam,
  untuk nama paket yang belum dikenal. Contoh dari log owner: `weonse.bxmfmy.qeomje` (manager
  spoofed, nama paketnya sengaja acak) menjadi nama manager-nya, `com.anthropic.claude` menjadi
  Claude. Nama disimpan di `labels.tsv`; nama dengan karakter kontrol atau lebih dari 60 byte
  dibuang. Tanpa API itu, nama paket tetap tampil seperti sebelumnya.
- Batas CPU di log: tiap sampel mencatat batas CPU dari pengendali Daya (CPU besar/kecil dan
  langkah panas). Ringkasan menulis berapa persen waktu CPU diturunkan karena panas dan batas
  terendahnya, juga waktu batas mode Hemat. Baris detail dan CSV (kolom `batas_cpu`) ikut
  menampilkannya. Data lama tanpa kolom ini tetap terbaca.
- Sensor macet tidak dihitung: sensor yang nilainya sama persis selama 30 sampel (±10 menit)
  sementara prosesor bergerak 5 °C atau lebih (log owner: `mtk-master-charger` tetap 50,0 °C
  selama satu jam setelah mengecas) tidak dihitung di tabel per bagian dan kotak suhu langsung,
  dan namanya disebut di ringkasan. Sensor Badan HP dan baterai tidak pernah dibuang.
- CSV: nama aplikasi dan proses teratas diberi tanda kutip, karena nama aplikasi bisa memuat koma.

English:

- A much lighter module. The owner's 6-hour log with the first v2.9.1 test build (25 Oct, 07:22–11:24
  WIB) showed the recorder and controller using 4.8% of the phone's CPU on average, the same in every
  app and with the screen off. The cause: every round started dozens of small processes (`cat` for
  every network interface, `awk`, `sed`, `dumpsys`).
  - Files are now read with shell builtins, and process names are remembered.
  - `dumpsys` runs only when the app in front changes, at least every 2 minutes.
  - The phone body comes from the same sensor read.
  - The last 40 samples (for stuck sensors) are read only every 5 minutes.
  - Measured on a fake phone shaped like rothko (60 sensors, 25 network interfaces):
    - recorder: about 94 → 12 processes per sample;
    - controller: 62 → 15 per round (stock kernel path; fewer with Cogan Bridge).
  - Not measured on the phone yet. The controller behaves the same.
- A lighter controller again (owner 26 Oct). The 3-hour log with the lighter build (25 Oct, 12:06–14:49
  WIB): the module's load went from 4.8% to 2.9% of the phone's CPU (recorder 1.5%, controller 1.4%).
  - The controller now reads only the CPU/GPU sensors and the phone body number (HyperOS's, or the skin
    sensors) instead of about 60 sensors, and runs no `awk` every 10 seconds.
  - Which sensors those are is found at start and every hour, grouped as in the Temperature tab.
  - On a rothko-shaped fake phone: sensor files opened per round went from 100 to about 26.
  - The numbers equal the Temperature tab's (tested).
- The CPU is now also lowered while the processor works from 55 °C, before 60 °C (owner 26 Oct). Scrolling
  Instagram (3-hour log, 14:16–14:37 WIB) kept the processor at 56 °C on average and the phone body at
  42–43.9 °C, yet the CPU was lowered in only 4 of 107 samples. With 55 °C the rule holds in about 69% of
  those Instagram samples (computed from the log, not measured on the phone). The steps stay gentle: from
  1 °C before the threshold, big CPU 90% then 80%. The 41 °C threshold is unchanged.
- New cause "Phone just started" for the first 5 minutes after the phone starts. Owner 25 Oct:
  installing v2.9.1 and restarting took the body from 37.3 to 43.0 °C, and the report said "Heavy app:
  Home screen". The recorder marks the first sample after a restart (the CPU counters start again).
- Temperature rises: the summary shows phone body rises of 2 °C or more within 5 minutes with their
  cause and tip, even below "hot" (owner 25 Oct: the body went 37.1 → 40.9 °C in about 3 minutes and
  the summary only said "no hot samples"). At most the three biggest.
- New cause "App updates": the Play Store or a package installer on screen, or using 3% of the CPU or
  more, with a tip about Play Store auto-updates. In the owner's data: downloads up to 9.5 MB/s, then
  installing at 70–85% CPU.
- Cogan Smart load: every sample records the CPU used by the module's recorder and controller,
  including finished child processes (awk, dumpsys…) that the top-process list never shows. The
  summary shows the average and the controller's part (CSV: `module_load_percent`,
  `controller_load_percent`). An open WebUI is not included.
- The "Heavy graphics" tip now also covers video and animations while scrolling non-stop, not only
  games. A processor working with the screen off is named as a background process instead of
  "Heavy app: Screen off".
- One phone body number everywhere: HyperOS's own body temperature (`hyperos_board`, from
  `board_sensor_temp`) when there, else the hottest skin sensor, else the battery. The Power tab,
  the Temperature tab, the HyperOS brakes card, the log and the controller use the same number.
  Owner: "the temperature is still inconsistent". In the owner's 6-hour CSV (1,257 samples) the
  HyperOS number is 0.1 °C below `quiet_therm` on average and within −0.7…+0.3 °C 90% of the time,
  so the 39/41/44 °C thresholds stay.
- Ups and downs: in the same data, sample-to-sample changes are small (90% under 0.3 °C); big jumps
  come with a hard-working processor (the battery rises too) or across sleep and restarts, when the
  log pauses for 3–5 minutes. The chart now breaks at such gaps instead of drawing a steep line, and
  plots the average of each slice instead of its peak; the highest reading stays in the Peak tile.
- Real app names in the Temperature tab, summaries and saved logs. Names come from the root manager
  (KernelSU Next and BakaSU both offer `getPackagesInfo`), at most every 6 hours, for package names
  not known yet. From the owner's log: `weonse.bxmfmy.qeomje` (a spoofed manager, its package name is
  random on purpose) becomes the manager's name, `com.anthropic.claude` becomes Claude. Names are kept
  in `labels.tsv`; names with control characters or over 60 bytes are dropped. Without that API the
  package names show as before.
- CPU cap in the log: every sample records the CPU cap of the Power controller (big/little CPU and the
  heat step). The summary shows how much of the time the CPU was lowered for heat and the lowest cap,
  plus the time under the Power saver cap. Detail lines and the CSV (column `batas_cpu`) show it too.
  Older data without this column still reads.
- Stuck sensors are left out: a sensor that keeps one exact value for 30 samples (about 10 minutes)
  while the processor moves 5 °C or more (owner's log: `mtk-master-charger` stayed at 50.0 °C for an
  hour after charging) no longer counts in the component table and the live tiles, and the summary
  names it. Phone body and battery sensors are never left out.
- CSV: the app name and top processes are quoted, since an app name can hold a comma.

## Mode mengikuti Badan HP / Modes follow the phone body — v2.9.0

Indonesia:

- Ambang Hemat, Kernel Default dan Performa kini dibaca dari suhu **Badan HP** (sensor
  kulit HP, yang terasa di tangan), bukan prosesor terpanas. Prosesor Dimensity HP ini
  saat santai pun sekitar 50 °C: dari log 3 hari owner (8.340 sampel), ambang 42 °C pada
  prosesor terlewati 97% waktu, sehingga Kernel Default menurut kodenya membatasi CPU
  besar ke 40% hampir sepanjang waktu (dihitung dari log, belum diukur di HP).
- Ambang baru: Hemat 39 °C, Kernel Default 41 °C, Performa 44 °C (Badan HP). Owner setelah
  uji HP 24 Okt: Badan HP 41 °C sudah terasa "hangat menuju panas" (suhu papan HyperOS saat
  itu 40,6 °C, `quiet_therm` 40,8 °C).
- Langkah halus (owner: "se-smooth mungkin"): mulai 1 °C sebelum ambang dengan dua langkah
  ringan saja; di ambang, CPU besar (X4) turun 10% per langkah sampai 60%, lalu CPU kecil
  (A720, yang menjaga UI tetap lancar) ke 90% dan 80%. Batas terdalam 60/80%, bukan 40%.
  Badan HP berubah pelan, jadi tiap langkah ditunggu tiga kali cek; naik lagi setelah tiga
  kali cek ≥ 1,5 °C di bawah ambang. Hemat tetap turun dari batasnya sendiri.
- CPU hanya diturunkan saat prosesor bekerja (≥ 60 °C). Panas dari cas (HyperCharge),
  ruangan atau HP yang santai tidak didinginkan oleh batas CPU, dan batas yang tertinggal dari
  saat itu hanya memperlambat pemakaian berikutnya; saat prosesor santai batasnya dilepas
  bertahap (owner, setelah uji HP 24 Okt: 3 jam data dengan HyperCharge 9,2 A).
- Simulasi saat layar menyala dengan ambang 41 °C: data 3 jam owner (dengan HyperCharge) CPU
  penuh ±69% waktu (ambang 42 °C: ±89%, v2.8: ±53%), data 1 jam ±85%, log 3 hari ±92%
  (v2.8: ±75%). CPU besar tidak pernah di bawah 70%. Dihitung dari log, belum diukur di HP.
- Jeda cas karena suhu oleh modul tetap **mati secara bawaan** (owner: HyperCharge yang
  mengatur); setelan yang tersimpan tidak diubah.
- GPU: tab Daya membaca node GPU HP ini (devfreq Mali, GED, gpufreqv2) dan menampilkannya di
  Kontrol kernel. **Baca saja**, tidak ada yang ditulis; batas GPU untuk game dipasang
  setelah node ini terbukti di HP.
- Rem darurat di semua mode: bila prosesor ≥ 95 °C, CPU diturunkan setiap cek.
- Tanpa sensor Badan HP, suhu baterai yang dipakai.
- Ambang suhu dari konfigurasi v2.8 dan sebelumnya (masih bermakna prosesor) dan dari build
  uji v2.9.0 sebelumnya (42/45 °C) diganti dengan bawaan baru. Mode, setelan cas dan
  interval tetap seperti yang disimpan.
- Tab Suhu: "panas" berarti Badan HP ≥ 41 °C (log 3 hari owner: ±18% waktu; v2.8 memakai
  prosesor ≥ 42 °C: 97%). Penyebab panas, grafik, serta rata-rata/tertinggi per aplikasi, kernel dan mode
  memakai Badan HP. Notifikasi panas juga membaca Badan HP. Prosesor tetap tampil di
  kotak Tertinggi dan tabel Bagian HP, dengan warna untuk komponen dalam (70/85 °C).
- Penyebab panas per bagian HP, masing-masing dengan saran: cas cepat, cas, grafis (GPU),
  modem (data seluler), prosesor, proses latar belakang, proses kernel, layar mati, serta
  layar & pemakaian biasa. Badan HP baru panas beberapa menit setelah pemicunya, jadi tiap
  momen panas dijelaskan dari ±3 menit terakhir (9 sampel), dan nama aplikasi diambil dari
  yang membuat beban itu. Contoh dari log owner: YouTube lewat 5G → "Modem (data seluler):
  YouTube", saran "Pakai Wi-Fi atau 4G".
- Rem HyperOS (baca saja): kartu baru di tab Daya menampilkan batas yang dipasang HyperOS
  sendiri dari `thermal_message` (suhu papan, profil termal `sconfig`, `temp_state`, batas
  CPU, modem, Wi-Fi, kecerahan maks, mode video). Modul tidak menulis node itu.
- Suhu papan HyperOS (`board_sensor_temp`) ikut dicatat tiap sampel sebagai sensor
  `hyperos_board` di grup Badan HP, jadi muncul di log, CSV dan tabel sensor tanpa modul
  terpisah. Badan HP memakai sensor kulit terpanas.
- Tab Daya menampilkan Badan HP sebagai suhu utama, prosesor di sebelahnya, dan
  penanda rem darurat. Jeda cas karena panas (opsional) juga memakai Badan HP.
- Halaman Tentang: kredit hanya untuk yang dipakai modul ini (Cogan17, API WebUI
  KernelSU/KernelSU Next); kredit kernel ada di dokumen kernel repo. Keaslian menyebut repo
  `cogan17/Cogan-Kernel`.
- Pengujian: tes pengendali dan pencatat dengan sysfs tiruan, memakai mksh dan
  One True Awk 20231127. Simulasi pada log 3 hari dan data 3 jam owner. Uji HP owner
  (24 Okt, versi sebelum aturan "prosesor bekerja"): Badan HP terbaca dari `quiet_therm`,
  tab Daya/Suhu/Modul tampil, saklar cas `input_suspend` ditemukan. Kartu Rem HyperOS dan
  saran penyebab diperiksa di browser tanpa HP (ID/EN). Uji HP versi ini: menunggu owner.

English:

- Power saver, Kernel Default and Performance thresholds now read the **phone body**
  temperature (the skin sensor, what a hand feels) instead of the hottest processor
  sensor. This Dimensity processor sits around 50 °C even at rest: in the owner's 3-day
  log (8,340 samples) a 42 °C processor threshold was exceeded 97% of the time, so by its
  code Kernel Default capped the big cores at 40% almost all the time (computed from the
  log, not measured on the phone).
- New thresholds: Power saver 39 °C, Kernel Default 41 °C, Performance 44 °C (phone body).
  Owner after the phone test on 24 Oct: a 41 °C phone body already feels "warm, getting hot"
  (HyperOS board temperature 40.6 °C at the time, `quiet_therm` 40.8 °C).
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
- Simulated with the screen on at 41 °C: the owner's 3-hour data (with HyperCharge) full CPU
  about 69% of the time (42 °C: about 89%, v2.8: about 53%), the 1-hour data about 85%, the
  3-day log about 92% (v2.8: about 75%). The big cores never go below 70%. Computed from the
  logs, not measured on the phone.
- Module charging heat pauses stay **off by default** (owner: HyperCharge is in charge);
  saved settings are not changed.
- GPU: the Power tab reads this phone's GPU nodes (Mali devfreq, GED, gpufreqv2) and shows
  them under Kernel controls. **Read only**, nothing is written; a GPU limit for games comes
  once these nodes are proven on the phone.
- Emergency brake in every mode: at a processor temperature of 95 °C or more, the CPU
  steps down at every check.
- Without a phone body sensor, the battery temperature is used.
- Temperature thresholds from v2.8 and older configurations (which meant the processor) and
  from the earlier v2.9.0 test build (42/45 °C) are replaced by the new defaults. Mode,
  charging settings and interval are kept.
- Temperature tab: "hot" means phone body ≥ 41 °C (owner's 3-day log: about 18% of the
  time; v2.8 used processor ≥ 42 °C: 97%). Heat causes, the chart and per-app, per-kernel and per-mode
  average/peak use the phone body. The heat notification reads the phone body too. The
  processor still shows in the Peak tile and the components table, coloured for internal
  parts (70/85 °C).
- Heat causes per part of the phone, each with a tip: fast charging, charging, graphics (GPU),
  the modem (cellular data), the processor, a background process, kernel processes, screen
  off, and the screen & ordinary use. The phone body heats up minutes after its trigger, so
  each hot moment is explained from the last ~3 minutes (9 samples), and the app named is the
  one that made that load. Example from the owner's log: YouTube over 5G → "Modem (cellular
  data): YouTube", tip "Use Wi-Fi or 4G".
- HyperOS brakes (read only): a new card in the Power tab shows the limits HyperOS sets by
  itself from `thermal_message` (board temperature, thermal profile `sconfig`, `temp_state`,
  CPU, modem and Wi-Fi limits, maximum brightness, video mode). The module never writes them.
- The HyperOS board temperature (`board_sensor_temp`) is logged with every sample as the
  sensor `hyperos_board` in the phone body group, so it shows in the log, CSV and sensor
  table without a separate module. The phone body uses the hottest skin sensor.
- The Power tab shows the phone body as the main temperature, the processor beside it,
  and an emergency-brake marker. The optional heat-based charging pause uses the phone
  body as well.
- About page: credits only for what this module uses (Cogan17, the KernelSU/KernelSU Next
  WebUI API); the kernel credits are in the repo's kernel document. Authenticity names the
  repo `cogan17/Cogan-Kernel`.
- Validation: controller and recorder tests on a fake sysfs with mksh and One True Awk
  20231127, plus simulations on the owner's 3-day log and 3-hour data. Owner's phone test
  (24 Oct, the version before the "processor works" rule): the phone body reads from
  `quiet_therm`, the Power/Temperature/Modules tabs work, charging switch `input_suspend` found.
  The HyperOS brakes card and the cause tips were checked in a browser without the phone
  (ID/EN). Phone test of this version: waiting for the owner.

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

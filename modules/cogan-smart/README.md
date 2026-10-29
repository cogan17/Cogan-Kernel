# Cogan Smart Kernel (modul)

**Versi paket terbaru: v2.9.1** (`versionCode` 18): modul lebih hemat CPU, satu angka Badan HP dari HyperOS, lonjakan suhu, nama aplikasi asli, batas CPU di log, dan penyaringan sensor macet. Dampak optimisasi terakhir pada HP belum diukur. Catatan perubahan lengkap ada di [`CHANGELOG.md`](CHANGELOG.md); status publikasi ada di [Releases](https://github.com/cogan17/Cogan-Kernel/releases).

**Versi pengembangan: v2.11.0** (versionCode 28): Manager sebagai pusat kendali (📊 Ringkasan semua tab), teks ringkas dengan saklar Mode Dev, dan 📖 Panduan di modul. Belum diuji pada HP. Hook ZRAM v2.10.8 sudah terbukti di HP. Rilis v2.9.1 tetap tersedia.

📖 **Panduan pemakaian:** [PANDUAN.md](PANDUAN.md) · [English](PANDUAN.en.md)

## ⬇️ Unduh

| Versi | versionCode | ZIP siap pasang | Catatan | Salinan di repo | SHA256 ZIP |
|---|---|---|---|---|---|
| **v2.11.0** (paket uji Manager pusat kendali, Mode Dev, panduan) | 28 | [Paket pembaruan](rilis/v2.11.0/Cogan-Smart-Kernel-v2.11.0.zip) | [What's New](rilis/v2.11.0/Cogan-Smart-v2.11.0-Whats-New-and-Fixes.txt) | [rilis/v2.11.0](rilis/v2.11.0) | `e39523e0fa0d8a311956ac3c111979dcd844cfb91d3e553ddc6a17175e13443c` |
| **v2.10.8** (paket uji hook ZRAM sebelum system_perf_init) | 27 | [Paket pembaruan](rilis/v2.10.8/Cogan-Smart-Kernel-v2.10.8.zip) | [What's New](rilis/v2.10.8/Cogan-Smart-v2.10.8-Whats-New-and-Fixes.txt) | [rilis/v2.10.8](rilis/v2.10.8) | `552fb6fecb65d60373289601d4ad0ae32d4be775a5fc76354e6ca47f495afbd8` |
| **v2.10.7** (paket uji ZRAM sampai swap aktif) | 26 | [Paket pembaruan](rilis/v2.10.7/Cogan-Smart-Kernel-v2.10.7.zip) | [What's New](rilis/v2.10.7/Cogan-Smart-v2.10.7-Whats-New-and-Fixes.txt) | [rilis/v2.10.7](rilis/v2.10.7) | `4546ec64b2d06fa32f39be4e789827f2a5f40fa1e5c8f6e87d85277ccec14720` |
| **v2.10.6** (paket uji perbaikan hook init ZRAM) | 25 | [Paket pembaruan](rilis/v2.10.6/Cogan-Smart-Kernel-v2.10.6.zip) | [What's New](rilis/v2.10.6/Cogan-Smart-v2.10.6-Whats-New-and-Fixes.txt) | [rilis/v2.10.6](rilis/v2.10.6) | `585210b1d596853d8dc14dc1a4a20dbd676431e9e2c2cd85b22b865f83809ba7` |
| **v2.10.5** (paket uji deteksi DRAM MediaTek) | 24 | [Paket pembaruan](rilis/v2.10.5/Cogan-Smart-Kernel-v2.10.5.zip) | [What's New](rilis/v2.10.5/Cogan-Smart-v2.10.5-Whats-New-and-Fixes.txt) | [rilis/v2.10.5](rilis/v2.10.5) | `a148ff25d146b7cb162622b1eb5c8c5c45609a4d75ed26ff70c918539336966d` |
| **v2.10.4** (paket uji integrasi init ZRAM) | 23 | [Paket pembaruan](rilis/v2.10.4/Cogan-Smart-Kernel-v2.10.4.zip) | [What's New](rilis/v2.10.4/Cogan-Smart-v2.10.4-Whats-New-and-Fixes.txt) | [rilis/v2.10.4](rilis/v2.10.4) | `73abbc48992235ffcb7a2705eda6f561e892d09420713add514ed9651e262f90` |
| **v2.10.3** (paket uji perbaikan RAM) | 22 | [Paket pembaruan](rilis/v2.10.3/Cogan-Smart-Kernel-v2.10.3.zip) | [What's New](rilis/v2.10.3/Cogan-Smart-v2.10.3-Whats-New-and-Fixes.txt) | [rilis/v2.10.3](rilis/v2.10.3) | `d8198a30e3a059318b8049d2f54451aff3fb518f3ff1a7f8e5274af750daa45e` |
| **v2.10.2** (paket uji tab sejajar) | 21 | [Paket pembaruan](rilis/v2.10.2/Cogan-Smart-Kernel-v2.10.2.zip) | [What's New](rilis/v2.10.2/Cogan-Smart-v2.10.2-Whats-New-and-Fixes.txt) | [rilis/v2.10.2](rilis/v2.10.2) | `27286981665a4998fefeb2e88a1a2f84d5c3766ed6b0a1c3e19ea6dfde224e3c` |
| **v2.10.1** (paket uji perbaikan pemindai) | 20 | [Paket pembaruan](rilis/v2.10.1/Cogan-Smart-Kernel-v2.10.1.zip) | [What's New](rilis/v2.10.1/Cogan-Smart-v2.10.1-Whats-New-and-Fixes.txt) | [rilis/v2.10.1](rilis/v2.10.1) | `42281ceab4fac3704f778955d93cdb59e73213ef77ed8e3990a0248de1008de4` |
| v2.10.0 (paket uji; pemindai aplikasi bermasalah) | 19 | [Paket uji](rilis/v2.10.0/Cogan-Smart-Kernel-v2.10.0.zip) | [What's New](rilis/v2.10.0/Cogan-Smart-v2.10.0-Whats-New-and-Fixes.txt) | [rilis/v2.10.0](rilis/v2.10.0) | `981caad71dfb458c39e0d8283cf37c895caf9990ce3936a4b4c15c55da8d955e` |
| **v2.9.1** (paket rilis) | 18 | [Cogan-Smart-Kernel-v2.9.1.zip](rilis/v2.9.1/Cogan-Smart-Kernel-v2.9.1.zip) | [What's New](rilis/v2.9.1/Cogan-Smart-v2.9.1-Whats-New-and-Fixes.txt) | [`rilis/v2.9.1`](rilis/v2.9.1) | `64631a42c9133c2d91568ceb88c9582f5c5a95b1b6535c64cb27551fb502e29c` |
| v2.9.0 | 17 | [Cogan-Smart-Kernel-v2.9.0.zip](https://github.com/cogan17/Cogan-Kernel/releases/download/cogan-smart-v2.9.0/Cogan-Smart-Kernel-v2.9.0.zip) | [What's New](https://github.com/cogan17/Cogan-Kernel/releases/download/cogan-smart-v2.9.0/Cogan-Smart-v2.9.0-Whats-New-and-Fixes.txt) | [`rilis/v2.9.0`](rilis/v2.9.0) | `7d15a729ce184aef8a3f870d5c0837010e22ccf69b910309c7f208b870057522` |
| v2.8.2 | 16 | [Cogan-Smart-Kernel-v2.8.2.zip](https://github.com/cogan17/Cogan-Kernel/releases/download/cogan-smart-v2.8.2/Cogan-Smart-Kernel-v2.8.2.zip) | [What's New](https://github.com/cogan17/Cogan-Kernel/releases/download/cogan-smart-v2.8.2/Cogan-Smart-v2.8.2-Whats-New-and-Fixes.txt) | [`rilis/v2.8.2`](rilis/v2.8.2) | `73f6d9c9a167d1528057ff84c65d6db371a5cde63e1435ca6e5e4f14bfc367d5` |
| v2.8.1 | 15 | [Cogan-Smart-Kernel-v2.8.1.zip](https://github.com/cogan17/Cogan-Kernel/releases/download/cogan-smart-v2.8.1/Cogan-Smart-Kernel-v2.8.1.zip) | [What's New](https://github.com/cogan17/Cogan-Kernel/releases/download/cogan-smart-v2.8.1/Cogan-Smart-v2.8.1-Whats-New-and-Fixes.txt) | [`rilis/v2.8.1`](rilis/v2.8.1) | `441e0780d77480f6642a84f5478ce61d659110a640ca6b025f51d2c718ce594f` |

- ZIP di Pre-release ([`cogan-smart-v2.9.0`](https://github.com/cogan17/Cogan-Kernel/releases/tag/cogan-smart-v2.9.0), [`cogan-smart-v2.8.2`](https://github.com/cogan17/Cogan-Kernel/releases/tag/cogan-smart-v2.8.2), [`cogan-smart-v2.8.1`](https://github.com/cogan17/Cogan-Kernel/releases/tag/cogan-smart-v2.8.1)) dan di folder `rilis/` adalah file yang sama, byte per byte.
- Pasang lewat root manager sebagai pembaruan modul, lalu reboot. Setelan dan riwayat tetap dipakai (ID `cogan_smart` sama).
- Kernel tujuan: **r1** repo ini (ACK 6.1.176). Diuji owner di Xiaomi 14T Pro:
  - build uji v2.9.1 pertama (25 Okt 2026, 07.22–11.24 WIB): pencatat dan pengendali memakai rata-rata 4,8% CPU seluruh HP;
  - build uji v2.9.1 hemat CPU (25 Okt 2026, 12.06–14.49 WIB): beban modul 2,9% (pencatat 1,5%, pengendali 1,4%). Build berikutnya: pengendali hanya membaca sensor CPU/GPU dan Badan HP, CPU diturunkan mulai prosesor 55 °C;
  - **v2.9.0** (24 Okt 2026): dipakai owner 7 jam (15.38–22.38 WIB) dengan kernel r2 dan r3, mode Kernel Default dan Hemat; CPU penuh hampir sepanjang waktu, panas terbanyak saat HyperCharge. Suhu Badan HP masih terasa tidak konsisten (diperbaiki di v2.9.1);
  - **v2.8.2 dengan r1** (24 Okt 2026): identitas kernel terverifikasi lewat Cogan Bridge ("kernel dibuat untuk HP ini"), mode Kernel Default, pencatat suhu, mengecas cepat 3868 mA, penjaga modul "aman";
  - v2.8.1 dan v2.8.2 dengan kernel arsip r6 (6.1.176, 23 Okt 2026); v2.8.2 juga saat pengisian HyperCharge.
- Versi baru: taruh ZIP dan catatannya di `rilis/<versi>/`, lalu jalankan tombol **Cogan Smart Release** di tab Actions. Kolom versi diisi **`v2.9.1`**, tanpa awalan nama tag `cogan-smart-` atau revisi kernel `r4`.

Satu modul KernelSU / KernelSU Next / BakaSU / Magisk yang menggabungkan **Cogan Power Mode v1.2** dan **Cogan Thermal Monitor v1.3** (issue #21, fondasi Smart Kernel). Kode kedua bagian tetap sama; yang berubah hanya cara keduanya dipasang dan saling menemukan.

| Bagian | Folder | Tugas |
|---|---|---|
| Manager | `manager/` | Pusat kendali: ringkasan semua tab, mode daya, pindai modul, governor CPU, profil RAM, kontrol Daya/Suhu, saran aplikasi user ≥ 7 hari |
| Daya | `power/` | Mode, batas CPU, boost aplikasi di layar, auto cut charging, readback kontrol |
| Suhu | `thermal/` | Sensor tiap 20 detik (termasuk suhu papan HyperOS), dugaan penyebab panas per bagian HP dengan saran, riwayat 7 hari, simpan log |
| Modul | `guard/` | Penjaga modul: perilaku modul lain, whitelist, hapus sampai ke akar |
| Bersama | `bridge.sh`, `webroot/client.js` | Cogan Bridge ABI 1, transport WebUI |

WebUI punya empat tab: **⚡ Daya**, **🌡️ Suhu**, **🛠️ Manager** dan **🧩 Modul**, plus halaman **ℹ️ Tentang & kredit** (`about.html`, bahasa Indonesia dengan pilihan English) dan **📖 Panduan** (`guide.html`) dari tautan di bawah tiap tab. Bawaannya teks ringkas; saklar **Mode Dev** di Tentang (`localStorage` `cogan.dev`, elemen `.dev`) memunculkan detail teknis. Dua tema bergaya Material You di `webroot/theme.css`: **Terang hangat** dan **Gelap OLED** (hitam murni); bawaannya mengikuti mode gelap HP, pilihan tetap disimpan dari halaman Tentang. Setiap kartu bisa dilipat; posisi buka/tutup diingat per tab. Navigasi memakai susunan ikon di atas dan judul satu baris di bawah dengan tinggi yang sama pada semua halaman; font besar dapat menggulir navigasi ke samping.
Tiap tab adalah halaman sendiri, jadi `client.js` menyimpan jawaban baca terakhir (dan identitas kernel/HP) di `localStorage` WebView: pindah tab langsung menampilkan nilai terakhir (angka redup, ↻ di pojok) sampai bacaan baru datang. Tab Modul memakai hasil pindaian yang berumur < 2 menit apa adanya; Pindai ulang untuk memperbarui.

## 🛠️ Manager (v2.11.0, pengembangan)

- **Pusat kendali (v2.11.0):** kartu 📊 Ringkasan membaca Daya (`power/report.sh status brief`), Suhu (`thermal/report.sh status brief` dan `summary 3600` tiap 60 detik selama kartu terbuka) dan penjaga modul (hasil `guard/report.sh scan` terakhir, dipakai bersama tab Modul). Mode daya bisa diganti dari sini; Pindai modul memperbarui hasil yang juga dipakai tab Modul.

- **Prosesor:** Kernel Default, sugov_ext atau schedutil. Pilihan hanya aktif bila tersedia pada semua policy. Tulisan nilai aktif menampilkan governor yang benar-benar terbaca.
- **Kompresi ZRAM:** Snappy & Daily Driver (LZ4) atau Heavy Multitasker / Space Saver (ZSTD), hanya bila ditawarkan semua perangkat ZRAM. Pilihan terpisah dari governor DRAM. Bacaan algoritme yang sesuai pilihan bisa sudah menjadi bawaan; status swap aktif ditampilkan terpisah dari /proc/swaps.
- **DRAM MediaTek:** driver mtk-dvfsrc-devfreq dan governor userspace sudah dikonfirmasi melalui perintah owner. Manager menampilkan bacaan itu dan mempertahankan DRAM Sistem. bw_hwmon tidak tersedia pada hasil tersebut; dropdown hanya muncul bila ada target DRAM yang menawarkannya atau untuk membersihkan pilihan lama. Identifikasi memakai ikatan driver, bukan daftar governor global atau dugaan dari nama: UFS/GPU tidak menjadi target RAM. Pembaruan ini tidak menambahkan bw_hwmon atau mengganti governor MediaTek secara paksa. Konfigurasi lama tanpa BW mengikuti sistem dan melepas kepemilikan devfreq lama ketika diterapkan.
- **ZRAM aktif tidak di-reset atau dimatikan.** Kompresor berbeda tetap berstatus belum diterapkan. Opsi boot mencoba memilihnya lewat post-fs-data sebelum ZRAM diinisialisasi. Bila Android sudah mengaktifkannya, pilihan tetap tertunda; restart tidak dijanjikan selalu mengganti kompresor. Integrasi v2.10.4 memakai initrc bawaan root manager pada init/early-fs/post-fs dan properti kompresor mmd bila sistem sudah memakainya. Manager menampilkan apakah hook terlihat pada boot ini; periksa algoritme aktual sebelum mencoba restart lagi.
- **Integrasi:** penulisan CPU/RAM memerlukan rothko, platform mt6989 serta identitas Cogan Bridge/device tree yang cocok. Batas CPU, cas dan termal dari Daya/HyperOS tetap berlaku. Tidak menambahkan loop pengendali.
- **Kontrol Daya/Suhu:** Simpan, Terapkan, Reset dan Mulai/Hentikan dipindah dari kedua tab ke Manager; Hapus riwayat juga di sini. Formulir tetap di tab semula. Perubahan kolom disimpan sebagai draf lokal sampai diterapkan dari Manager; Simpan log tetap di tab Suhu.
- **Aplikasi:** pindai manual aplikasi user pada pengguna Android aktif. Saran hanya untuk bukti penggunaan terakhir ≥ 7 hari, tanggal pemasangan cukup lama, dan proses tidak sedang berjalan. Waktu aktivitas komponen/foreground service ikut dihitung; data hilang bukan bukti tidak dipakai. Tinjau aplikasi membuka info aplikasi Android untuk memilih uninstall/nonaktifkan, tanpa tindakan massal.
- **Keandalan pemindaian (v2.10.1):** hasil dump terpotong, ditolak atau kosong membatalkan saran. Pembacaan proses wajib berhasil, dengan ps native Android bila tersedia. Deadline dumpsys diatur langsung; kegagalan menampilkan tahap, kode proses dan rincian singkat yang tetap terlihat di halaman. Data belum cukup tetap bukan bukti tidak dipakai.
- **Pemulihan:** Ikuti kernel melepas governor milik Manager; perubahan pihak lain dipertahankan. Kompresor ZRAM yang sudah aktif mengikuti konfigurasi sistem pada restart. Pilihan boot bawaan mati.
- **Integrasi init (v2.10.4):** Simpan pilihan RAM dengan penerapan boot aktif. Modul membuat initrc miliknya dan memakai ksud initrc refresh; tidak menulis metadata sendiri atau menambah skrip global. Aturan memeriksa properti perangkat dan Cogan Bridge sebelum mengubah ZRAM yang belum diinisialisasi. Kesiapan aturan berbeda dari bukti hook benar-benar dijalankan. Hook modules.rc sudah terdapat pada commit KernelSU Next/BakaSU dalam [Cogan r5](../../kernel/history/run-40538599681-1.md), sehingga tidak perlu mengganti kernel hanya untuk integrasi ini.
- **Dukungan root manager:** KernelSU Next/BakaSU harus menyediakan CLI initrc dan hook kernel yang cocok; namespace SELinux ksu atau su dibaca saat persiapan. Pada root manager tanpa fitur itu, hook post-fs-data lama tetap dicoba dan UI menampilkan keterbatasan. Tidak memaksa mengaktifkan mmd.
- **Siklus setelan:** pilihan yang sudah disimpan sebelum pembaruan disiapkan oleh installer untuk reboot pemasangan. Pilihan sesudahnya berlaku pada boot berikutnya. Jika instalasi modul masih menunggu reboot, selesaikan reboot pembaruan sebelum mengubah setelan; cache root manager memprioritaskan folder pembaruan. Mematikan penerapan boot/Ikuti kernel membersihkan initrc serta properti milik modul; ZRAM yang sudah aktif mengikuti sistem pada restart. Modul yang dinonaktifkan/dihapus dikecualikan oleh mekanisme cache root manager.
- **Perlu restart?** Pindah tab dan pindai aplikasi langsung bekerja. Simpan hanya menyimpan pilihan; Terapkan sekarang mencoba governor CPU/bw_hwmon yang didukung saat itu juga. Kompresor ZRAM aktif tetap mengikuti penjelasan di atas. Pemasangan ZIP pembaruan membutuhkan satu reboot.
- Data Manager: `/data/adb/cogan_smart/manager`; draf UI memakai localStorage WebView.

English: Manager separates supported ZRAM compression from optional DRAM governors, shows matching/pending/blocked boot results and actual swap activity, and adds supported CPU governors, centralized Power/Temperature actions and seven-day app review. Hardware writes require a matching rothko/mt6989 Cogan Bridge. Active ZRAM is never reset; boot application is best effort and actual readbacks are shown. App removal/disable is chosen in Android app info. v2.10.1 rejects incomplete/denied/empty dumps and failed process reads, prefers native Android ps, sets dumpsys deadlines and keeps stage/exit details visible. v2.10.4 also uses native KernelSU Next/BakaSU initrc actions and optional mmd setup properties to select compression before initialization, reporting hook readback separately from preparation. It does not replace the existing kernel or reset live ZRAM. v2.10.5 identifies MediaTek DRAM by its mtk-dvfsrc-devfreq driver binding, shows its actual governor and never targets UFS or GPU devfreq; it adds no bw_hwmon. v2.10.6 fixes the initrc exec line so Android init actually runs the ZRAM hook (init's tokenizer has no escapes inside quotes and expands exec arguments twice); in v2.10.4–v2.10.5 the hook never ran. On rothko the vendor init rewrites lz4 on post-fs-data and Xiaomi's system_perf_init starts ZRAM on load-bpf-programs, so v2.10.8 runs the hook on load-bpf-programs, between the two (v2.10.7's boot-completed run was too late). The owner tested v2.10.8 on the phone: zram0 runs zstd with active swap. v2.11.0 makes Manager the control centre (a summary of every tab), shortens everyday text behind a Dev mode switch and adds an in-module guide (PANDUAN.en.md); it has not been tested on a physical phone.

## Mode

| Di layar | Nilai internal | Perilaku |
|---|---|---|
| 🌿 Hemat | `hemat` | CPU besar dibatasi `SAVER_CAP` %, ambang Badan HP 2 °C di bawah Kernel Default (39 °C) |
| 🧠 Kernel Default | `seimbang` | Bawaan. CPU diturunkan bertahap bila Badan HP ≥ `TARGET_TEMP` (41 °C) |
| 🎮 Performa | `game` | Performa penuh, CPU diturunkan bila Badan HP ≥ `GAME_LIMIT` (44 °C), boost aplikasi di layar |

Sejak v2.9.0 ambang mode dibaca dari suhu **Badan HP** (sensor kulit HP, yang terasa di tangan), bukan prosesor. Prosesor Dimensity HP ini saat santai pun sekitar 50 °C, sehingga ambang 42 °C pada prosesor (v2.8) membatasi CPU hampir sepanjang waktu. Badan HP memakai angka badan milik HyperOS sendiri (`board_sensor_temp`, dicatat sebagai `hyperos_board`) bila ada, lalu sensor kulit terpanas, lalu suhu baterai; semua kartu memakai angka yang sama (v2.9.1). "Panas" di tab Suhu juga berarti Badan HP ≥ 41 °C. Ambang 41/44 °C dipilih owner setelah uji HP (41 °C sudah terasa hangat menuju panas).

Langkah halus (Kernel Default dan Performa):

| Langkah | CPU besar (X4) | CPU kecil (A720) |
|---|---|---|
| 0 | 100 % | 100 % |
| 1–4 | 90 → 60 % | 100 % |
| 5–6 | 60 % | 90 → 80 % |

Mulai 1 °C sebelum ambang dengan langkah 1–2 saja; tiap langkah ditunggu tiga kali cek (Badan HP berubah pelan); naik lagi setelah tiga kali cek ≥ 1,5 °C di bawah ambang. CPU hanya diturunkan saat prosesor bekerja (≥ 55 °C): panas dari cas, ruangan atau HP yang santai tidak membuat CPU diturunkan, dan saat prosesor santai batasnya dilepas bertahap. Hemat turun 10 % dari `SAVER_CAP`. Di semua mode ada **rem darurat** bila prosesor ≥ 95 °C. Cogan Bridge ABI 1 memberi satu batas untuk semua inti X4 dan satu untuk A720.

Jeda cas karena suhu (`CHARGE_THERMAL`) tetap **mati secara bawaan**: HyperCharge dan sistem HP yang mengatur suhu cas. GPU dibaca saja (Kontrol kernel); batas GPU menyusul setelah node-nya terbukti di HP.

Kartu **🧯 Rem HyperOS** di tab Daya menampilkan batas yang dipasang HyperOS sendiri (`/sys/class/thermal/thermal_message`: suhu papan, `sconfig`, `temp_state`, batas CPU, modem, Wi-Fi, kecerahan maks, mode video). Baca saja; modul tidak menulis node itu.

Tab Suhu menjelaskan tiap momen panas dari ±3 menit terakhir, per bagian HP, dengan saran: cas cepat, cas, grafis (GPU), modem (data seluler), prosesor, proses latar belakang, proses kernel, layar mati, atau layar & pemakaian biasa.

**Henti Daya** melepas batas CPU, boost dan saklar cas milik pengendali Daya. Governor CPU/RAM dari Manager dilepas dengan **Ikuti kernel**; ZRAM aktif mengikuti sistem setelah restart. Tombol Action di root manager berpindah ke mode berikutnya.

## 🧩 Modul (penjaga modul, v2.2)

`guard/report.sh scan` membaca `/data/adb` (tanpa menjalankan apa pun dari modul lain) dan `guard/guard.awk` menyusun laporannya:

- **Tiap modul:** identitas, status (aktif, nonaktif, dihapus/dipasang saat reboot, update tertunda), ukuran, hook yang dipakai (skrip boot, `system.prop`, `sepolicy.rule`, Action, WebUI), file sistem yang diganti, program biner, proses yang sedang berjalan, dan **akar di luar foldernya** (skrip di `service.d` dan sejenisnya yang memakai modul itu).
- **Penanda risiko** dari isi skrip, `system.prop` dan `sepolicy.rule`, dengan bukti `file:baris`. ⛔ berbahaya: mematikan SELinux, aturan SELinux `* * * *`, unduh-lalu-jalankan, kode base64 yang dijalankan, mengubah file root manager, menulis partisi, membawa `su` sendiri. ⚠️ perlu dicek: internet, Zygisk, ganti program sistem, layanan init, skrip boot di luar folder, mengubah modul lain, prop keamanan, izin 777, mencopot aplikasi. Penanda ini **dugaan**, bukan antivirus; modul spoof yang sah pun bisa ditandai.
- **Terintegrasi perangkat ⇄ kernel ⇄ modul (D-023):** tab ini memuat kartu Kernel yang sama dengan tab lain (identitas asli dari Cogan Bridge, ✓ kernel dibuat untuk HP ini). Modul lain yang menulis node yang dikendalikan Cogan Smart (cpufreq, uclamp, saklar cas, termal, `stop` layanan termal) ditandai ⚔️ **bentrok**: dua pengendali di node yang sama saling tarik, seperti alasan Power Mode dan Thermal Monitor digabung.
- **Di luar modul:** skrip di `post-fs-data.d`, `post-mount.d`, `service.d`, `boot-completed.d`; isi `/data/adb` beserta pemakainya; proses dari `/data/adb` yang bukan milik modul mana pun.
- **Whitelist:** root manager, metamodule (NoMount) dan Cogan Smart selalu dilindungi. Modul yang ditandai 🛡️ Percaya tidak dihitung mencurigakan dan tidak bisa dihapus sebelum dilepas. Daftar: `/data/adb/cogan_smart/guard/trusted`.
- **Hapus sampai ke akar:** proses modul dihentikan, modul ditandai `disable` + `remove` (root manager menjalankan `uninstall.sh`-nya lalu menghapus folder saat reboot), update tertunda dan skrip boot luar yang memakainya langsung dihapus. Data `/data/adb/<id>` hanya dihapus bila dipilih, **setelah** reboot (`service.sh` → `guard/report.sh boot`), karena `uninstall.sh` modul mungkin masih memerlukannya. ↩ Batal hapus tersedia sebelum reboot.
- Nonaktifkan/aktifkan memakai berkas `disable` seperti root manager (berlaku setelah reboot). Isi `/data/adb` yang tidak dikenal dan tidak dipakai modul terpasang bisa dihapus.

## Pasang

- Data: `/data/adb/cogan_smart/power`, `/data/adb/cogan_smart/thermal` dan `/data/adb/cogan_smart/guard` (whitelist); log yang disimpan ada di `/sdcard/Download/CoganThermal`.
- Bila **Cogan Power Mode** atau **Cogan Thermal Monitor** lama masih terpasang, installer menyalin setelan dan riwayatnya (tanpa `run/`) lalu menandai modul lama untuk dihapus saat reboot. Dua pengendali di node CPU/cas yang sama akan saling tarik.
- Reboot sekali setelah memasang.

## Perangkat ⇄ kernel ⇄ modul

Ketiganya saling mengenal (D-023). Kartu Kernel di semua tab WebUI menampilkan hasilnya.

| Arah | Tanpa Cogan Bridge (kernel r2) | Dengan Cogan Bridge (r3) |
|---|---|---|
| Modul → perangkat | `ro.product.device`, nama, `ro.board.platform`; modul diuji untuk `rothko` (`CB_DEVICES`) | Sama |
| Modul → kernel | Identitas dari `/proc` (kandidat, **belum terverifikasi**) | `release`/`banner` asli dari kernel, di balik spoof SUSFS |
| Kernel → perangkat | Nama kernel menyebut `rothko` (`…-Cogan-Rothko-…`) = kandidat | Atribut `device` (target build) dan `soc` (dari device tree) = terverifikasi |
| Kernel → modul | Tidak ada | Heartbeat `power_client`/`thermal_client`, lease CPU QoS dilepas kernel bila modul berhenti |

`device_json` (di `bridge.sh`) melaporkan `match`: 1 kernel dibuat untuk HP ini, 0 untuk HP lain, -1 belum diketahui. Pada HP selain `rothko` modul tetap berjalan dengan kontrol sysfs, tetapi menandai "belum diuji".

**Untuk build r3**, driver Cogan Bridge menambah dua atribut opsional ABI 1 (modul ini sudah membacanya): `device` = `TARGET_DEVICE` saat kompilasi (`rothko`), `soc` = platform dari device tree saat boot (mis. `mt6989`). Atribut lain ABI 1 tidak berubah.

## Uji dan paket

```sh
cd tests && python3 -m unittest test_cogan_smart_power test_cogan_smart_thermal test_cogan_smart_bridge test_cogan_smart_android test_cogan_smart_module test_cogan_smart_guard test_cogan_smart_manager
python3 scripts/package_module.py modules/cogan-smart OUT_DIR   # ZIP siap pasang, tanpa README dan folder rilis/
```

Tes memakai `mksh` dan `original-awk` bila terpasang (shell dan awk Android).

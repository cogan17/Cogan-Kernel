# Checkpoint — 29 Okt 2026 (WIB)

Cogan Smart **v2.12.4** (versionCode 35: 🔍 Cari) di atas v2.12.3 (Percaya/blokir langsung) dan v2.12.2 (pindai terbukti di HP). Siap diuji. **Rilis ditahan owner** sampai diuji. Sesi berikutnya baca `CLAUDE.md`, file ini dan `CHECKPOINT.md`, lalu tunggu instruksi owner. Jangan otomatis menguji HP, menjalankan build atau menerbitkan rilis.

## v2.12.4 — Cari aplikasi (owner 29 Okt ±13.55 WIB, rilis tetap DITAHAN)

- **Permintaan owner** (screenshot daftar panjang dengan Pindai ulang di bawah): "Disebelah pindai bisa tambah cari ga? … ada saran peletakan yg tepat?" Saran yang dipakai: kotak cari di atas daftar (di atas filter) dan sticky, bukan di sebelah Pindai ulang yang ada di paling bawah.
- `apps.html`: `#appSearch` (`.find` sticky). `query` mencocokkan label atau nama paket; saat ada isian, mencari di semua aplikasi tanpa memedulikan filter. Pesan "Tidak ada aplikasi yang cocok dengan …" bila kosong. Ditambah i18n, Panduan (WebUI, PANDUAN.md/.en.md) dan tes Node (nama, paket, tidak cocok).
- [Paket uji](modules/cogan-smart/rilis/v2.12.4/Cogan-Smart-Kernel-v2.12.4.zip) 190463 byte, SHA256 `c32130a038a9dca1f676dd6c2bd3408846b2d6e65b1fc59e04e424a53587e47b` (dua kali dikemas, sama). Terukur lokal: semua tes lolos; Playwright 412 px tanpa error, kotak tetap di atas saat digeser. Belum diuji di HP.

## v2.12.3 — Percaya dan blokir langsung (owner 29 Okt ±13.45 WIB, rilis tetap DITAHAN)

- ✅ **v2.12.2 diuji di HP:** owner 29 Okt 13.44–13.45 WIB, screenshot tab Aplikasi terisi (Swift Backup, WhatsApp, Hunter, SpotiFLAC, dll.): "Berjalan dengan baik." Pindai lewat pipa terbukti. Gerak-gerik, internet dan baterai terbaca.
- **Laporan owner:** Menambah ke whitelist sekitar 40 detik ("bisa salah bisa benar"). Penyebab (kode v2.12.2): handler `trust`/`untrust`/`remove` di `apps.html` menjalankan `await scan()` sesudah aksi, dan klien `api` mengantrekan perintah di belakang pindai yang sedang berjalan. Backend `trust` hanya mengedit file whitelist, tetapi menunggu `api.lock`.
- **Perbaikan v2.12.3 (versionCode 34):** `status`, `trust`, `untrust` dan `block` dijalankan sebelum `api.lock` (kunci hanya untuk `scan` dan `remove`). WebUI memakai klien `quick` terpisah. Percaya/Lepas mengubah kartu lokal tanpa pindai. Hapus diikuti pindai di latar belakang. `apps.awk` tidak lagi menolkan risiko aplikasi yang dipercaya (UI menghitung dipercaya terpisah). `status` membawa `trusted` untuk memperbarui daftar dari cache. Tes baru: Percaya dan blokir selesai < 2,5 detik saat pindai lambat memegang kunci.
- **Cek acak owner 13.49 WIB:** Netflix "Dipasang: 1999-12-31" (sumber toko aplikasi, 37 hari tidak dipakai). Tanggal itu `firstInstallTime` dari Android, bukan hitungan modul; dugaan: aplikasi bawaan Xiaomi dengan tanggal tetap dari image sistem (belum dibuktikan di HP). WebUI kini memberi keterangan untuk tanggal sebelum 2008-09-23.
- [Paket uji](modules/cogan-smart/rilis/v2.12.3/Cogan-Smart-Kernel-v2.12.3.zip) 189659 byte, SHA256 `3079c3577a8bb2a9a042f9c5f0f3b3d726f8ebbe67650bddbabee6c78adc3d60` (dua kali dikemas, sama). Terukur lokal: semua tes lolos (mksh, dash, BusyBox ash). Belum diuji di HP.

## Bug pindai di HP + audit v2.12.1 → v2.12.2 (owner 29 Okt ±12.57 WIB, rilis tetap DITAHAN)

- **Bukti HP (screenshot owner, v2.12.1):** tab Aplikasi "Pemindaian gagal pada daftar aplikasi: cmd: Failure calling service package: Failed transaction (2147483646)", berulang setelah Pindai ulang. Kedua tombol blokir aktif walau status tidak terbaca.
- **Audit v2.12.1 owner** menarik sendiri temuan IFS lama (byte `27 09 27`). Owner meminta: "Jangan langsung ditelan mentah-mentah. Pastikan kebenaran terlebih dahulu."
- **A (pindai gagal): benar, penyebab ditemukan.** `read_must` dan `read_may` mengarahkan stdout/stderr `pm`/`dumpsys`/`settings` ke file di `/data/adb/cogan_smart/apps/scan.*` (`adb_data_file`). `cmd` meneruskan fd itu ke system_server lewat Binder. Kernel `security/selinux/hooks.c selinux_binder_transfer_file` memeriksa akses system_server ke file itu; ditolak → `binder.c` `-EPERM` → FAILED_TRANSACTION. Bagian modul yang membaca lewat pipa `$(...)` (dumpsys tab Suhu, hapus, blokir) bekerja di HP. Perbaikan: `run_to` (pipa `| cat > file`, kode keluar ke `.rc`), `settings` lewat pipa, `exec < /dev/null`. Reproduksi offline: fake Binder di tes gagal bila fd 1/2 bukan pipa atau `/dev/null`; kode v2.12.1 gagal dengan pesan yang sama persis.
- **B (readback blokir): benar menurut kode.** `! query | grep` bernilai benar saat query gagal. Kini kode keluar dan teks `query-op` dicek (`CA_QUERY_BAD`). `block_pass` yang gagal membaca query menandai `run/query.failed`, dan `status` mengembalikan `query_ok` 0. Readback memakai `query-op`, yang mencakup semua user (getPackagesForOps). Set per user boleh gagal untuk user yang tidak memasang aplikasi itu.
- **C (tombol blokir): benar.** Kini ada perintah ringan `report.sh status`. Kedua tombol `disabled` di HTML sampai status terbaca, `blockUnknown` dipanggil bila status gagal dibaca, dan aksi blokir dilaporkan terpisah dari pindai.
- Tes menemukan bug tambahan: one-true-awk menolak `$3 == "0" ? 0 : 1` tanpa kurung di argumen printf (`block_json`). Sudah diberi kurung.
- **v2.12.2 (versionCode 33):** [paket uji](modules/cogan-smart/rilis/v2.12.2/Cogan-Smart-Kernel-v2.12.2.zip) 188377 byte, SHA256 `f3c5ccf16f6bfa5f6ef696dac73a3a98b7591dfd7c6c42c3c6b6816496f3a700` (dua kali dikemas, sama). Terukur lokal: semua tes lolos (mksh, dash, BusyBox ash, one-true-awk, BusyBox awk), cek Node lolos. Belum diuji di HP.
- **Cek opsional di HP (read-only; membuat lalu menghapus satu file sementara di folder data modul):** `su -c 'f=/data/adb/cogan_smart/apps/t; pm list packages -3 > $f 2>&1; echo file rc=$?; head -c 100 $f; echo; pm list packages -3 | head -n 1; rm -f $f'`. Harapan: baris file gagal "Failed transaction", baris pipa menampilkan satu paket.

## Audit v2.12.0 → v2.12.1 (owner 29 Okt, rilis tetap DITAHAN)

- Owner mengirim audit read-only atas ZIP v2.12.0 (SHA `7acc2022…6d47`). Hasil cek:
  - **P1 IFS jurnal restore: tidak terbukti.** `manager/report.sh` baris 96 berisi TAB asli (`od -c` menunjukkan `\t` satu byte). Baris yang sama di mksh, dash dan BusyBox ash membaca 4 kolom utuh. Reproduksi audit mengetik `IFS='\t'` secara harfiah. `test_cpu_restore_preserves_other_controllers` sudah memulihkan governor lewat jurnal. Hanya ditambah komentar.
  - **P1 root manager berganti nama: benar, bersyarat.** Diperbaiki: `manager_pkgs` mengenali `libksud.so`, `libmagisk*.so`, `libapd.so` dan `libkpatch.so` di `/data/app/*/*/lib/*`. Host tidak terbaca atau `appId` tidak terbaca → penghapusan dibatalkan (gagal tertutup).
  - **P2 blokir tanpa readback: benar.** `block_source` kini membaca ulang lewat `query-op`, mencatat `ok` 0/1 di `blocked.log`, dan memberi tahu "GAGAL dicabut" sekali per paket (penanda `run/failed.PKG`). Block off tetap tidak mengembalikan izin (keputusan desain), dan teks konfirmasinya kini menyebut itu.
  - **P2 race pekerja blokir: benar.** Tiap putaran memeriksa `block.pid == $$`; yang kalah keluar. `stop_block` menunggu maksimal 3 detik.
  - **P2 timeout scan: benar** (190 detik > 120 detik). Bacaan opsional kini berbagi anggaran 100 detik (`CA_BUDGET`, tes 0). `settings` diberi `timeout 5`.
  - **Catatan cgroup:** `leave_app_cgroup` kini membaca ulang dan menulis ke logcat (`CoganSmart`) bila ditolak.
- **v2.12.1 (versionCode 32):** [paket uji](modules/cogan-smart/rilis/v2.12.1/Cogan-Smart-Kernel-v2.12.1.zip) SHA256 `4568aeb4b1fe0e8c85f33b9cb13d47d7572898799e9226e4653d0dc42669a8e8` (dua kali dikemas, sama). Terukur lokal: semua tes lolos, termasuk 4 tes regresi baru di `test_cogan_smart_apps` (manager berganti nama, host tidak dikenal, readback gagal, dua pekerja) yang diulang di dash dan BusyBox ash. Belum diuji di HP.

## Sedang berjalan

- PR v2.12.4 (lihat bagian v2.12.4). v2.12.3 sudah di-merge (#85).

## Sudah selesai (sesi 28–29 Okt)

- PR #82 `4e85020`: v2.11.2, pekerja tetap hidup setelah root manager ditutup (lihat bagian Bug Mulai berhenti).
- PR #81: checkpoint owner 29 Okt.
- [PR #79](https://github.com/cogan17/Cogan-Kernel/pull/79) `381e848`: v2.11.1 (Manager hanya memantau, keluar WebUI sekali usap). ✅ Owner 29 Okt: "Semuanya lolos uji disisi saya".
- v2.11.1 (lihat bagian v2.11.1): revisi owner atas v2.11.0 dan perbaikan usap kembali.
- [PR #77](https://github.com/cogan17/Cogan-Kernel/pull/77) `61dbf3cfefc3b3942289b5c25734964ea8e18ee5`, digabung 29 Okt 09.55 WIB: v2.11.0 (lihat bagian v2.11.0). [Validate 40809071342](https://github.com/cogan17/Cogan-Kernel/actions/runs/40809071342) lolos 09.54 WIB. ZIP uji dikirim ke owner.
- [PR #76](https://github.com/cogan17/Cogan-Kernel/pull/76) `2291616df26941b6393c071a2f7c9bfb43382da1`, digabung 29 Okt 07.11 WIB: artifact dan rilis kernel hanya membawa modul SUSFS sidex15 (file 5); modul simonpunk tidak dibangun lagi, SUSFS simonpunk tetap dicek di Cek pembaruan (aturan di `CLAUDE.md`).
- PR #72–#75 (28 Okt): hook init ZRAM v2.10.6 → v2.10.7 → v2.10.8; v2.10.8 diuji owner di HP 23.23 WIB (`zram0: zstd`).
- PR #70–#71 (28 Okt): deteksi DRAM MediaTek v2.10.5 dan checkpoint.

## Tertunda (keputusan owner)

- Uji v2.12.3 di HP: Percaya/Lepas langsung selesai; sisanya: tekan Mulai di Kontrol Daya/Suhu, tutup root manager, buka lagi → tetap aktif; tab 📱 Aplikasi terisi; APK kiriman WhatsApp/sosmed/email/SMS ditolak dan izin yang dinyalakan lagi dicabut dengan notifikasi.
- Rilis Cogan Smart: **ditahan owner** ("Untuk rilis tahan dulu!", 29 Okt 11.26 WIB).

## Langkah pertama berikutnya

- Tunggu hasil uji owner. Bila ada yang salah, perbaiki dari screenshot (versi baru v2.12.1). Format dump HyperOS 3 untuk appops, netstats dan batterystats belum terbukti; kolom "Belum terbaca" atau angka kosong adalah petunjuk pertama.

## Bug Mulai berhenti → v2.11.2 (owner 29 Okt ±11.26 WIB, rilis DITAHAN)

- **Laporan owner** (screenshot Manager v2.11.1 dan berkas investigasi read-only): Mulai di Kontrol Daya/Suhu kembali "berhenti" setelah keluar dari root manager lalu masuk lagi. Di HP terbaca AUTOSTART=1, power `run/pid` dan `daemon.lock/pid` = 26305, thermal = 27125, tanpa flag disable/remove. Cmdline kedua PID tidak tercetak. Owner: **"Untuk rilis tahan dulu!"**
- **Penyebab (dari kode, belum dibuktikan di HP):** pekerja yang dimulai dari WebUI (`start_controller`/`start_sampler` lewat `setsid`/`nohup`) tetap berada di cgroup v2 aplikasi root manager (`uid_N/pid_M`). Saat proses aplikasi mati, system_server menulis `cgroup.kill` (AOSP `libprocessgroup/processgroup.cpp` `sendSignalToProcessGroup`, dicek 29 Okt) sehingga semua proses di cgroup itu mati, termasuk proses root. SIGKILL melewati trap EXIT, jadi PID dan lock tertinggal, sesuai bukti owner. Pekerja dari `service.sh` saat boot tidak terkena.
- **Perbaikan v2.11.2 (versionCode 30):** `bridge.sh leave_app_cgroup` memindahkan pekerja ke `/sys/fs/cgroup/cgroup.procs`, hanya bila `/proc/$$/cgroup` berisi `::/uid_`. Dipanggil di awal `power/controller.sh` dan `thermal/sampler.sh`. Tes baru ada di `test_cogan_smart_bridge`. [Paket uji](modules/cogan-smart/rilis/v2.11.2/Cogan-Smart-Kernel-v2.11.2.zip) 164759 byte, SHA256 `559d113d1e56e4b6ad48d601d567923897e8ba064839ba564abaa0d403ebc10b` (dua kali dikemas, sama). Belum diuji di HP.
- **Bukti di HP (owner, 29 Okt 12.26 WIB, Termux):** power PID 13892 dan thermal PID 12704 keduanya `0::/`. Owner belum menyebut apakah kedua PID itu dimulai lewat tombol Mulai dan apakah status bertahan setelah root manager ditutup; jadi v2.11.2 belum ditandai lolos uji HP.
- **Cara cek (read-only):** `su -c 'for f in /data/adb/cogan_smart/power/run/pid /data/adb/cogan_smart/thermal/run/sampler.pid; do p=$(cat $f); echo $f $p; cat /proc/$p/cgroup | grep "^0::"; done'` harus menampilkan `0::/`, bukan `0::/uid_…`. Lalu tutup root manager, buka lagi, dan status harus tetap aktif.
- **Dampak ke PR #80 (v2.12.0):** sudah dikerjakan atas "Lanjutkan" owner (lihat bagian v2.12.0).

## v2.12.0 — tab Aplikasi (versionCode 31)

- **Permintaan owner (29 Okt, dengan screenshot kartu Aplikasi jarang dipakai):** ganti fungsinya jadi bisa melihat semua gerak-gerik aplikasi dan menghapus sampai ke akar, termasuk APK scam/virus kiriman WA/sosmed; fungsi nonaktifkan tidak usah ada. Pilihan owner lewat pertanyaan: **tab baru 📱 Aplikasi** (Manager hanya ringkasan), **hapus manual + konfirmasi**, **blokir APK dari chat & sosmed** (saklar, bawaan aktif), pantau **akses sensitif, izin berbahaya, sumber & waktu instal, data internet & baterai**.
- **Backend `apps/`:** `report.sh` (scan, trust/untrust, remove, block on|off, boot, stop), `apps.awk` (gabungan dump), `block.sh` (loop 5 detik), `common.sh` (daftar sumber chat/sosmed, blokir, notifikasi). Pemindai lama Manager (`manager/report.sh scan|app`, `manager/apps.awk`) dihapus; tesnya pindah ke `tests/test_cogan_smart_apps.py`.
- **Bukti AOSP (main, dicek 29 Okt):** `dpm remove-active-admin` = `forceRemoveActiveAdmin` yang menolak admin non-uji; `handlePackagesChanged` melepas admin yang receiver-nya tidak bisa dibaca, jadi `pm disable` receiver sebagai root melepasnya; `setEnabledSettings` hanya membatasi uid shell (root bebas) dan paket DO/PO; `pm uninstall` tanpa `--user` = `DELETE_ALL_USERS`; format `appops get`/`dumpsys appops`, `query-op`, `dumpsys package` (installer/initiating/packageSource), `device_policy`, `batterystats --usage` (`UID uNaM: mAh`, locale English) dan `netstats` (Android 12, `UID stats:`).
- **WebUI:** `apps.html` (blokir, filter Perlu dicek/Semua/Jarang dipakai, kartu per aplikasi, Percaya, Hapus sampai akar), nav 5 tab di semua halaman, baris 📱 Aplikasi di Ringkasan Manager, kartu aplikasi lama Manager dihapus, terjemahan English, Panduan (WebUI + PANDUAN.md/.en.md) bagian Aplikasi dan tanya jawab APK penipuan.
- Terukur lokal: 257 tes lolos (7 tes baru tab Aplikasi dengan HP tiruan: scam APK dari WhatsApp sebagai admin perangkat, salinan APK berspasi di folder WhatsApp, root manager, blokir + loop), juga di mksh, dash, BusyBox ash, one-true-awk dan BusyBox awk; cek WebUI Node; Playwright 412 px ID/EN tanpa error, 5 tab muat. [Paket uji](modules/cogan-smart/rilis/v2.12.0/Cogan-Smart-Kernel-v2.12.0.zip) 45 file, 183994 byte, SHA256 `7acc20223baabc925345f7d3e6c328bb8bf94a97460c92f9b65e15f27b566d47` (dua kali dikemas, sama).
- **Sesudah checkpoint (owner "Lanjutkan", 29 Okt):** blokir APK ditambah sosmed lain, email dan SMS (33 paket; Gmail dan Pesan adalah aplikasi sistem, jadi "Terpasang" dibaca dari semua paket); `main` (v2.11.2) di-merge; versionCode 31; `apps/block.sh` memanggil `leave_app_cgroup` (blokir yang dinyalakan dari WebUI tidak mati bersama root manager).
- **Belum diuji di HP dan belum dirilis.** Yang paling mungkin berbeda di HyperOS 3: format dump appops/netstats/batterystats, dan apakah pemasang paket Xiaomi menghormati izin sumber yang dicabut (mode disimpan per paket atau per UID).

## v2.10.4 — initrc ZRAM (versionCode 23)

- Integrasi init ZRAM Cogan Smart **v2.10.4 / versionCode 23** sudah masuk `main`: [PR #68](https://github.com/cogan17/Cogan-Kernel/pull/68), commit `0386eed3f4952a837a81c36da80a22644083c563`; [Validate 40693190837](https://github.com/cogan17/Cogan-Kernel/actions/runs/40693190837) dengan **251 tes lolos**. [Paket uji v2.10.4](modules/cogan-smart/rilis/v2.10.4/Cogan-Smart-Kernel-v2.10.4.zip) SHA256 `73abbc48992235ffcb7a2705eda6f561e892d09420713add514ed9651e262f90`. Tidak ada GitHub Release baru; rilis publik terakhir v2.9.1.
- v2.10.4 menggunakan dukungan `initrc` KernelSU Next/BakaSU pada Cogan r5 untuk memilih kompresor sebelum ZRAM diinisialisasi. Tidak menambah governor DRAM, tidak reset ZRAM dan tidak swapoff.
- Screenshot HP owner menunjukkan **v2.10.4 terpasang**, `zram0: lz4 · swap aktif`, opsi LZ4 terpilih, status “initrc tersiapkan untuk boot berikutnya”, dan `bw_hwmon` abu-abu. Bacaan LZ4/swap aktif terbukti, tetapi tidak membuktikan modul yang mengganti LZ4. Belum ada bukti hasil ZSTD atau hasil eksekusi hook initrc pada HP.
- Owner menjalankan pembacaan root `/sys/class/devfreq/*`. Hasilnya: `112b0000.ufshci` → driver `ufshcd-mtk`, governor `simple_ondemand`; `13000000.mali` → driver `mali`, governor `dummy`; **`mtk-dvfsrc-devfreq` → driver `mtk-dvfsrc-devfreq`, governor `userspace`**. Ketiganya menampilkan daftar sama: `dummy apupassive-pe apuconstrain apuuser apupassive userspace powersave performance simple_ondemand`. **Tidak ada `bw_hwmon`.** `available_governors` devfreq dapat bersifat global; daftar UFS/GPU bukan bukti dukungan DRAM. `userspace` adalah governor aktif DRAM, bukan bukti ZRAM gagal. Jangan mengganti ke `simple_ondemand` atau port governor Qualcomm dengan asumsi.

## v2.11.1 — Manager hanya memantau, keluar sekali usap (versionCode 29)

- **Revisi owner (29 Okt, dengan screenshot tombol mode dan Pindai modul di Manager):** mode diatur tab Daya dan pindai modul oleh tab Modul; Manager hanya memantau. "Sisanya tidak perlu diubah": kartu Prosesor, RAM, Kontrol Daya/Suhu dan Aplikasi di Manager tetap.
- **Manager:** tiga tombol mode diganti satu baris `#modeLine` (nama mode + keterangan dari setelan tab Daya); tombol Pindai modul dihapus, `#guardLine` membaca pindaian terakhir tab Modul (`guard.cached('scan')`, tab Modul memindai otomatis bila hasil > 2 menit).
- **Bug keluar WebUI (owner: harus usap berkali-kali):** tiap tab adalah halaman sendiri, jadi setiap pindah tab menambah riwayat WebView, dan usap kembali menelusuri riwayat itu dulu sebelum menutup WebUI. `i18n.js` (dimuat semua halaman) kini mengganti riwayat (`location.replace`) untuk tautan internal, kecuali `guide.html`, jadi kembali dari Panduan membuka tab sebelumnya. Terukur lokal (Playwright): 5 kali pindah tab → satu entri riwayat; kembali dari Panduan → tab Manager. Penyebab di HP disimpulkan dari cara kerja WebView, belum dibuktikan di HP.
- Panduan (WebUI, PANDUAN.md/.en.md), README, CHANGELOG disesuaikan. Tes Manager memeriksa `modeLine`.
- Terukur lokal: tes Python + cek WebUI lolos. [Paket uji](modules/cogan-smart/rilis/v2.11.1/Cogan-Smart-Kernel-v2.11.1.zip) 41 file, 163739 byte, SHA256 `8961d4c5d23c0f02a1a326b9f86ff87b524a7e8b40bdc38a1fd71b54d54d3175` (dua kali dikemas, sama).
- **Belum diuji di HP dan belum dirilis.**

## v2.11.0 — Manager pusat kendali, Mode Dev, Panduan (versionCode 28)

- **Permintaan owner (29 Okt):** Manager hierarkinya di atas tab lain (lihat semua statistik/grafik, terapkan/paksa perubahan); teks terlalu baku dan panjang, perlu versi user ringkas dan versi Dev/debug; buku panduan. Pilihan owner lewat pertanyaan: **pusat kendali** (Manager ringkasan + semua tombol, tab lain untuk detail dan pilihannya sendiri), **satu saklar Mode Dev** di Tentang, **panduan di modul + repo**, log **cukup dianalisa**.
- **Manager:** kartu 📊 Ringkasan (suhu Badan HP/baterai/prosesor, pengendali, pencatat, tombol mode, grafik 1 jam + waktu panas + penyebab utama, hasil pindai modul + tombol Pindai modul). Grafik dipindah ke `client.js` (`UI.chart`) dan dipakai tab Suhu juga. Aksi per modul (percaya, nonaktifkan, hapus) tetap di tab Modul karena per item.
- **Mode Dev:** `theme.css` menyembunyikan `.dev` kecuali `<html data-dev="1">` (`localStorage cogan.dev`); `.user` disembunyikan saat Mode Dev. Detail teknis di semua tab ditandai `.dev`; setelan lanjutan (interval cek, terapkan ulang, interval pencatat) hanya di Mode Dev.
- **Panduan:** `webroot/guide.html` (ID/EN), `PANDUAN.md` dan `PANDUAN.en.md` (isi sama, tidak ikut ZIP: `scripts/package_module.py` melewatinya seperti README).
- **Terjemahan:** perbaikan aturan i18n (isian tidak melewati pemisah " · " atau baris baru), entri baru, `tests/test_cogan_smart_webui.py` menjalankan cek WebUI Node dan memastikan mode English tanpa teks Indonesia (dijalankan Validate).
- **Log 16 jam owner (28 Okt 17.31 – 29 Okt 09.31 WIB):** Badan HP maks 43,6 °C, baterai maks 44,0 °C (mengecas), beban modul median 1,8% CPU. Arus 13–16 A berurutan saat HyperCharge dan kolom GPU kosong saat GPU tidur adalah normal; tidak ada perubahan pencatat, dijelaskan di Panduan.
- Terukur lokal: semua tes Python + cek WebUI lolos; halaman dimuat Playwright tanpa error di mode pengguna dan Dev. [Paket uji](modules/cogan-smart/rilis/v2.11.0/Cogan-Smart-Kernel-v2.11.0.zip) 41 file, 163348 byte, SHA256 `e39523e0fa0d8a311956ac3c111979dcd844cfb91d3e553ddc6a17175e13443c` (dua kali dikemas, sama).
- **Sudah di `main`:** PR #77, commit `61dbf3c`, 29 Okt 09.55 WIB. **Belum diuji di HP dan belum dirilis.**

## v2.10.8 — hook ZRAM sebelum system_perf_init (versionCode 27)

- **v2.10.7 di HP (28 Okt, 22.52 WIB):** `Hook boot ini: zstd boot-completed pending`, `zram0: lz4`. Saat boot selesai ZRAM sudah aktif; tahap boot-completed v2.10.7 terlambat.
- **Bukti di HP (root, 22.53–22.56 WIB):**
  - dmesg 0,35 dtk `ExtM: Added device: zram0`; 9,751 dtk KernelSU `exec '/system_ext/xbin/system_perf_init'`; 9,768 dtk `zram0: detected capacity change`; 9,776 dtk `Adding 12582908k swap on /dev/block/zram0. Priority:-2`; 9,789 dtk `INIT:zygote-start`. Prioritas -2 berarti bukan `swapon_all` fstab (`swapprio=10`).
  - `/system_ext/etc/init/init.miui.ext.rc`: `service system_perf_init /system_ext/xbin/system_perf_init` (class main, disabled), dan baris 226–228 `# system_perf_init: after load_persist_props_action && before zygote-start` → `on load-bpf-programs` → `start system_perf_init`. String biner memuat `swapon`, `mkswap`, `/sys/block/zram0/disksize`, `persist.sys.zram.disksize`, tanpa `comp_algorithm`: ia memakai algoritme yang sedang terpasang.
  - `/proc/swaps`: hanya `/dev/block/zram0`, prioritas -2. Modul lain (AshLooper, tcp_optimiser, dll.) tidak menyentuh ZRAM.
- **Perbaikan:** tahap hook terakhir menjadi `on load-bpf-programs` (boot-completed dihapus). AOSP `rootdir/init.rc`: `trigger post-fs-data` (520) → `trigger load-bpf-programs` (523) → `trigger zygote-start` (527); `init.cpp` membaca `/system/etc/init/hw/init.rc` sebelum `/system_ext/etc/init`. Jadi hook berjalan sesudah lz4 vendor dan sebelum `start system_perf_init`.
- Terukur lokal: tes Manager lolos. [Paket uji](modules/cogan-smart/rilis/v2.10.8/Cogan-Smart-Kernel-v2.10.8.zip) 40 file, 151578 byte, SHA256 `552fb6fecb65d60373289601d4ad0ae32d4be775a5fc76354e6ca47f495afbd8` (dua kali dikemas, sama).
- ✅ **Diuji di HP:** Uji HP owner 28 Okt, 23.23 WIB: `zram0: zstd · swap aktif` dan `Hook boot ini: zstd load-bpf-programs matching`. Pilihan ZSTD kini benar-benar dipakai saat ZRAM dinyalakan. Dampak ke performa/baterai belum diukur. **Belum dirilis**: GitHub Release lewat workflow Cogan Smart Release adalah keputusan owner.

## v2.10.7 — pilihan ZRAM bertahan sampai swap aktif (versionCode 26)

- **v2.10.6 di HP (28 Okt, 22.41 WIB):** `Hook boot ini: zstd post-fs matching`, jadi perbaikan hook v2.10.6 terbukti bekerja. Tetapi `zram0` kembali `lz4`.
- **Penyebab, terbaca di HP (root):** `/vendor/etc/init/hw/init.mt6989.rc` baris 192 `write /sys/block/zram0/comp_algorithm lz4` di `on post-fs-data` (baris 180), dan baris 1138 `swapon_all /vendor/etc/fstab.enableswap` di `on property:sys.boot_completed=1` (baris 1122). fstab: `/dev/block/zram0 none swap defaults zramsize=100%,swapprio=10`. `mmd.enabled_aconfig=false`. Hanya baris 192 yang menulis `comp_algorithm` di semua folder init.
- **Perbaikan:** hook juga berjalan pada `property:sys.boot_completed=1`. Menurut kode init AOSP (`import_parser.cpp` `EndFile`, `action_manager.cpp`), import vendor dibaca sesudah `init.rc` (tempat KernelSU menempel aturan modul), dan aksi dengan pemicu sama berjalan sesuai urutan baca. Jadi hook menulis pilihan sesudah lz4 vendor dan tepat sebelum `swapon_all`. Tes Manager memeriksa empat blok dan pemicu terakhirnya.
- Terukur lokal: tes Manager lolos. [Paket uji](modules/cogan-smart/rilis/v2.10.7/Cogan-Smart-Kernel-v2.10.7.zip) 40 file, 150996 byte, SHA256 `4546ec64b2d06fa32f39be4e789827f2a5f40fa1e5c8f6e87d85277ccec14720` (dua kali dikemas, sama).
- **Belum diuji di HP dan belum dirilis.** Uji: pasang v2.10.7, reboot, tunggu boot selesai, buka Manager. Harapan: `zram0: zstd` dan `Hook boot ini: zstd boot-completed matching`.

## v2.10.6 — perbaikan hook init ZRAM (versionCode 25)

- **Bukti HP owner, 28 Okt sekitar 22.18–22.26 WIB (v2.10.5 terpasang):** bagian DRAM tampil benar (`DRAM MediaTek · mtk-dvfsrc-devfreq: userspace`, tanpa dropdown BW). Setelah memilih ZSTD dan restart, `zram0` tetap `[lz4]` (zstd tersedia) dan penanda `/dev/.cogan_smart_zram_init` tidak ada. Root: rc modul punya 3 blok `on` dengan `exec u:r:ksu:s0`; cache `/metadata/vold/ksu/modules.rc` berisi aturan Cogan; dmesg `KernelSU: module rc: loaded 4024 bytes`; config `RAM=heavy BOOT=1`, `init.state=ready`. Kesimpulan: hook v2.10.4–v2.10.5 tidak pernah berjalan.
- **Penyebab, dari kode init AOSP (mirror GitHub `aosp-mirror/platform_system_core`, `init/tokenizer.cpp`, `action.cpp`, `service.cpp`, `util.cpp`):** di dalam `"..."` tokenizer init tidak mengenal escape, jadi `\"` di program menutup kutipan dan baris exec terpotong. Argumen `exec` diekspansi dua kali (`RunBuiltinFunction`, lalu `ExpandArgsAndExecv` saat proses dimulai), dan `$` tunggal sesudah ekspansi pertama memicu `LOG(FATAL)` "deprecated syntax". Bukti `dmesg` untuk pesan itu belum terbaca: perintahnya tertelan karena ditempel sebelum prompt root muncul.
- **Perbaikan:** program ditulis sebagai satu token init tanpa kutipan (`\\`, `\"`, `\ `) dan setiap `$` menjadi `$$$$`. Isi program dan pemeriksaannya tidak berubah. Tes Manager kini meniru tokenizer dan ekspansi init AOSP; tes itu gagal pada kode v2.10.5 dan lolos pada v2.10.6.
- [Paket uji](modules/cogan-smart/rilis/v2.10.6/Cogan-Smart-Kernel-v2.10.6.zip) 40 file, 150361 byte, SHA256 `585210b1d596853d8dc14dc1a4a20dbd676431e9e2c2cd85b22b865f83809ba7` (dua kali dikemas, sama).
- **Belum diuji di HP dan belum dirilis.** Risiko berikutnya: `zram.ko` adalah modul (GKI `CONFIG_ZRAM=m`); bila belum dimuat pada tahap init/early-fs/post-fs, penanda akan berbunyi `missing`, dan itu masalah waktu muat yang perlu langkah lain.
- Uji HP berikutnya (keputusan owner): pasang ZIP v2.10.6, reboot, buka Manager. Harapan: `zram0: zstd` dan baris `Hook boot ini: zstd post-fs matching`.

## v2.10.5 — paket uji deteksi DRAM MediaTek (versionCode 24)

- **Sudah di `main`:** [PR #70](https://github.com/cogan17/Cogan-Kernel/pull/70), commit `8b1fe721a22aa5ed1d4ec24c98794cad8489a8bd`, digabung 28 Okt sekitar 22.11 WIB. [Validate 40713132298](https://github.com/cogan17/Cogan-Kernel/actions/runs/40713132298) lolos (tes, YAML, shell; 22.10 WIB). Branch draf `fix/cogan-smart-dram-detection` tidak diperlukan lagi.
- Draf dari branch `fix/cogan-smart-dram-detection` diperiksa dan diselesaikan. DRAM dikenali dari ikatan driver `mtk-dvfsrc-devfreq`; Manager menampilkan governor aktual; UFS/GPU tidak lagi menjadi target BW walau daftar governor-nya sama; dropdown BW disembunyikan bila tidak ada pilihan yang bisa dipakai, kecuali untuk mengembalikan pilihan lama ke DRAM Sistem.
- Tambahan saat penyelesaian: teks DRAM di mode English kini diterjemahkan penuh (termasuk "belum terbaca" → "unavailable").
- Terukur lokal: 252 tes Python dan cek WebUI lolos; `sh -n` lolos. [Paket uji](modules/cogan-smart/rilis/v2.10.5/Cogan-Smart-Kernel-v2.10.5.zip) 40 file, 149444 byte, dapat dibuat ulang dengan SHA256 `a148ff25d146b7cb162622b1eb5c8c5c45609a4d75ed26ff70c918539336966d` (cara kemas dibuktikan dengan membuat ulang ZIP v2.10.4: SHA256 sama).
- **Belum ada uji HP v2.10.5 dan belum ada GitHub Release** (rilis publik terakhir v2.9.1). Ini perbaikan deteksi dan tampilan; tidak menambah `bw_hwmon`, tidak mengganti governor DRAM dan tidak butuh kernel baru.
- Uji HP berikutnya (keputusan owner): pasang ZIP sebagai pembaruan modul, reboot, buka Manager. Bagian DRAM seharusnya menampilkan `DRAM MediaTek · mtk-dvfsrc-devfreq: userspace` tanpa dropdown BW.

[Checkpoint sebelumnya](https://github.com/cogan17/Cogan-Kernel/blob/f8312e007c6cca8829aec01bc3d251334e467135/checkpoint.md) memuat riwayat v2.10.0–v2.10.3, pemindai aplikasi dan rilis v2.9.1. Gunakan identitas git Cogan, PR ke main, catatan ID/EN dan hemat Actions sesuai `CLAUDE.md`.

## English state summary

The owner reported that Start in Power/Temperature controls fell back to stopped after closing the root manager. Workers started from the WebUI sat in the app's cgroup, which Android kills with cgroup.kill. v2.11.2 (PR #82) moves them to the root cgroup; the owner's Termux check showed both workers in `0::/`, but the close/reopen test is not confirmed yet. v2.12.0 (versionCode 31) adds the 📱 Apps tab with the same fix for its APK block loop, and the block now covers 33 chat, social, email and SMS apps. Releases are on hold by the owner. Wait for the owner's test results.

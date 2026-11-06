# Checkpoint

## 6 Nov 2026 (checkpoint owner)

**Sedang berjalan**
- Tidak ada workflow atau PR yang berjalan.

**Selesai hari ini (catatan rilis makin ringkas untuk end user)**
- PR #138 (sebelumnya): generator What's New & Fixes digabung seperti teks Telegram (versi sekali, tiap perubahan sekali per root).
- PR #139: tombol **Rapikan catatan rilis** (`.github/workflows/rapikan-catatan.yml` + `kernel/tidy_release_notes.py`) untuk merapikan body rilis yang sudah terbit — mengedit lewat token Actions, tanpa build ulang, tanpa menyentuh file rilis. Dijalankan: r12 854→327 baris, r11/r8 ikut ringkas; r1–r3 format lama dibiarkan.
- PR #140: bagian **Komponen & fitur** jadi satu seksi `## ROOT` per root manager (`kernel/telegram.py` `compact_components`), dipakai `compact_notes` (Builder + Rilis dari run) dan `tidy_components` (tombol, idempoten). Tiap seksi tetap lengkap agar `previous()` bisa membandingkan rilis berikutnya. Tombol dijalankan ulang: r12 330→147 baris (3 seksi, dari 21 blok), r11/r8 ikut.
- PR #141: CoganSU masuk sebagai proyek saudara di `docs/keaslian-dan-kredit.md` (ID+EN).

**Tertunda**
- CoganSU "Tidak terpasang" di HP (dari 4 Nov): menunggu owner kirim `cogansu-terpasang.apk` untuk pastikan sertifikat APK terpasang = rilis r1. Diagnosa lengkap ada di entri 4 Nov di bawah.
- Terbitkan r38 lewat Rilis dari run bila owner minta (run_id 41819469210, diuji di HP).
- CoganSU di kombinasi root bila owner mau.
- Penyebab NoMount menolak aturan di SukiSU (telusuri kode, tanpa HP).
- Branch `feat/stabil-dev-utama` di GitHub (hapus manual).
- `modules/cogan-smart/webroot/about.html` masih sebut proyek saudara TWRP saja (modul Cogan Smart diparkir, D-025); CoganSU belum ditambah di sana — hanya bila owner minta.

**Langkah pertama berikutnya**
- Baca `CLAUDE.md`, lalu tunggu instruksi owner.

## 4 Nov 2026 malam (checkpoint owner)

**Sedang berjalan**
- Tidak ada workflow yang berjalan.

**Selesai**
- Akar CoganSU "Tidak terpasang" di r36 ketemu: sertifikat kunci rilis CoganSU (RSA 4096) 1261 byte, melebihi batas 1024 byte `kernel/manager/apk_sign.c` hulu. Owner memilih opsi B: CoganSU PR #8 (`5ef9ac2`), batas 2048 + buffer `kmalloc`. Compile lokal driver lolos; patch SUSFS tetap cocok.
- Kartu Cogan Kernel di CoganSU menulis "bukan Cogan Kernel": `ShellUtils.fastCmd` hanya mengembalikan baris terakhir. CoganSU PR #9 (`f26b1b9`), semua baris dibaca lewat `newJob()`.
- Rilis CoganSU `v26.11.04-r2` (Pre-Release, run #3) dan `v26.11.04-r3` (Pre-Release, run #4; job Terbit diulang sekali karena GitHub 502).
- Builder r37 (run 41815461522, CoganSU r2) dan **r38** (run [41819469210](https://github.com/cogan17/Cogan-Kernel/actions/runs/41819469210), CoganSU r3, 6.1.176, SUSFS, gate KMI OK). **r38 diuji di HP owner 4 Nov ±18.37 WIB**: CoganSU Berfungsi (`v3.3.1-49-gf26b1b9e`), kartu Cogan Kernel `6.1.176-Cogan-Rothko-ACK-r38-5be85323d` · SUSFS · NoMount · BBG.

**Tertunda**
- Terbitkan r38 lewat Rilis dari run (`run_id` 41819469210, centang diuji di HP) dan jadikan CoganSU r3 Release, bila owner meminta.
- CoganSU di kombinasi root bila owner mau.
- Penyebab NoMount menolak aturan di SukiSU (telusuri kode, tanpa HP).
- Branch `feat/stabil-dev-utama` di GitHub (hapus manual).

**Langkah pertama berikutnya**
- Baca `CLAUDE.md`, lalu tunggu instruksi owner (kemungkinan: rilis r38).

## 4 Nov 2026 (checkpoint owner)

**Sedang berjalan**
- Menunggu owner mengirim APK CoganSU yang benar-benar terpasang (`su -c 'cp /data/app/*/com.cogan.su-*/base.apk /sdcard/cogansu-terpasang.apk'`) untuk memastikan sertifikatnya. Akar "Tidak terpasang" belum pasti.

**Run #36 dicek: build BENAR, manager "Tidak terpasang" — akar belum pasti**
- Run #36 ([41773264948](https://github.com/cogan17/Cogan-Kernel/actions/runs/41773264948)) lolos. ZIP kernel r36 yang owner kirim = artifact run #36 (SHA256 `cdcc301b…` cocok). Owner flash r36 di HP 4 Nov ±11.55 WIB: boot dan root/su jalan.
- **Koreksi (catatan "bug sertifikat" di PR #134 SALAH):** kernel r36 tidak salah sertifikat. Log build run #36 (Kbuild `$(info)`) mencetak `signature size: 0x04ed`, `signature hash: b0fb06ca…` — identitas CoganSU yang benar dari `cogansu.mk`. Analisis `strings` pada Image sebelumnya menyesatkan (hash tidak muncul sebagai teks biasa, bukan berarti salah); jangan ambil kesimpulan dari `strings` Image lagi.
- Jadi kernel r36 (menuntut `b0fb06ca`) + APK rilis r1 (sertifikat `0x04ed`/`b0fb06ca`, terbukti `cogansu_cert.py`) **seharusnya cocok**. Tapi dmesg HP: `Found manager com.cogan.su …, is_manager: 0`, tanpa baris `expected:` → gagal sebelum banding hash (tahap baca struktur/ukuran sertifikat APK).
- Dugaan terkuat: **APK yang terpasang di HP bukan rilis r1** (ukuran sertifikat ≠ 0x04ed). Belum dipastikan.

**Selesai 3–4 Nov**
- PR #119–#123: modul yang dipakai owner di README (20 modul + TEESimulator).
- PR #124: SukiSU (root `SUKI`). Dengan SUSFS menunggu pengembang SukiSU (`CONFIG_KSU_SUSFS_PRIORITY_UID_FILTER`). Run #33 tanpa SUSFS lolos build + gate KMI; uji HP: NoMount menolak aturan (kode 1, penyebab belum ketemu). Owner kembali ke r11 KernelSU. SukiSU tidak dirilis.
- PR #125: kombinasi root dua/tiga, BakaSU hanya sendiri.
- PR #126: cara melihat kernel asli lewat Termux di panduan pasang.
- PR #127: hasil uji HP SukiSU di CLAUDE.md.
- PR #128, #129: semua nama Kredit bertautan, sumber BSP Xiaomi (6.1.57, Android 14).
- PR #130: form Stabil Dev Utama dibatalkan owner (branch `feat/stabil-dev-utama` masih ada; hapus lewat GitHub, sesi ini tidak bisa).
- PR #131: CoganSU (root `CSU`, `cogan17/CoganSU`): kernel dan manager dari rilis CoganSU terbaru yang sama.
- PR #132: aturan gaya jawaban di CLAUDE.md.

**Tertunda**
- Pastikan sertifikat APK CoganSU yang terpasang (menunggu file dari owner). Bila ≠ rilis r1 → pasang `2-MANAGER_CoganSU_v26.11.04-r1.apk` yang benar. Bila = r1 tapi tetap ditolak → selidiki parsing `apk_sign` kernel r36, perbaiki + build r37 (owner sudah setuju perbaiki + build bila memang bug).
- Penyebab NoMount menolak aturan di SukiSU (telusuri kode, tanpa HP).
- CoganSU di kombinasi root bila owner mau.
- Rilis r8 (run #20) hanya atas permintaan owner.

**Langkah pertama berikutnya**
- Owner kirim `cogansu-terpasang.apk`; hitung sertifikatnya (`scratchpad/cogansu/scripts/cogansu_cert.py apk`), bandingkan dengan `b0fb06ca`. Bila beda → pasang APK rilis r1 yang benar. Bila sama → selidiki `apk_sign` kernel r36, perbaiki + Build r37. Lanjut hanya setelah owner meminta.
- Repo CoganSU (`cogan17/CoganSU`) sudah ter-attach sesi ini (untuk perbaikan bila terbukti bug kernel).

## 2 Nov 2026

Catatan terbaru: **[checkpoint.md](checkpoint.md)** — 2 Nov 2026, 09.04 WIB. Tidak ada PR atau workflow yang berjalan.

- Selesai 31 Okt – 2 Nov: PR #91–#108 (centang SUSFS, BakaSU dari `main` bukan ReSukiSU, baris fitur `No …`, samarkan identitas, CVE-2026-53163, Tanpa LTO bawaan, centang timpa di Rilis dari run).
- KSUN r19 dan BakaSU r21 tanpa SUSFS lolos uji HP owner; percobaan, tetap di artifact, tidak dirilis.
- Issue #105 selesai (PR #112, #113): 141 lolos build + gate KMI untuk KSUN dan BakaSU.
- Tertunda: rilis r8 (run #20) hanya atas permintaan owner.
- Baca `CLAUDE.md` dan `checkpoint.md`, lalu tunggu instruksi owner.

Riwayat 29 Okt:

- v2.12.4 (versionCode 35, PR #86): 🔍 Cari di tab Aplikasi. ✅ Lulus uji owner di HP (29 Okt 21.36 WIB, kernel r6) dan terbit sebagai Release [`cogan-smart-v2.12.4`](https://github.com/cogan17/Cogan-Kernel/releases/tag/cogan-smart-v2.12.4) dengan label diuji di HP. Catatan rilis lengkap v2.9.1 → v2.12.4 (PR #89).
- Builder: NoMount diunggah sekali per versi (PR #88).
- v2.12.3 (versionCode 34): Percaya/Lepas/blokir langsung, tanpa menunggu pindai (sebelumnya ±40 detik). Paket uji di `modules/cogan-smart/rilis/v2.12.3/`; belum diuji di HP.
- v2.12.2 (versionCode 33): pindai aplikasi gagal di HP ("Failed transaction") karena output Binder ke file `/data/adb`; kini lewat pipa. Readback blokir jujur, tombol blokir nonaktif sampai status terbaca. Paket uji di `modules/cogan-smart/rilis/v2.12.2/`. ✅ Pindai berjalan di HP owner 29 Okt 13.44 WIB.
- v2.12.1 (versionCode 32): perbaikan audit v2.12.0 (pengaman root manager gagal tertutup, readback blokir APK, satu pekerja blokir, anggaran waktu pindai). Temuan IFS jurnal tidak terbukti. Paket uji di `modules/cogan-smart/rilis/v2.12.1/`; belum diuji di HP.
- v2.12.0 (versionCode 31): tab 📱 Aplikasi (pantau, hapus sampai akar, blokir APK dari 33 aplikasi chat/sosmed/email/SMS) + perbaikan v2.11.2. Paket uji di `modules/cogan-smart/rilis/v2.12.0/`; belum diuji di HP.
- v2.11.2 (versionCode 30): pengendali/pencatat yang dimulai dari WebUI tidak lagi mati saat root manager ditutup (keluar dari cgroup aplikasi). Termux owner: keduanya `0::/`; uji tutup/buka root manager belum dikonfirmasi.
- v2.11.1 (versionCode 29): ✅ lolos uji owner di HP 29 Okt.
- v2.10.8: ✅ ZRAM ZSTD saat boot. Rilis kernel hanya membawa modul SUSFS sidex15 (#76).
- Baca `CLAUDE.md` dan `checkpoint.md`, lalu tunggu instruksi owner.

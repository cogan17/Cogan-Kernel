# Checkpoint — 24 Okt 2026, 09.20 WIB · GitHub App untuk Rilis dari run

Sesi berikutnya mulai dari sini. Aturannya ada di `CLAUDE.md`. Semua waktu dalam WIB.

## Sedang berjalan
- Integrasi GitHub App untuk **Rilis dari run** disiapkan sesuai keputusan owner. Pendaftaran/instalasi App dan pengisian variable/secret akun belum selesai pada sesi ini: browser berhenti pada halaman login GitHub. Jangan menganggap App sudah aktif atau r2 sudah terbit.
- Pekerjaan checkpoint terdahulu tidak dilanjutkan. Perubahan sesi ini hanya autentikasi rilis, panduan, tes dan checkpoint.
- Status PR dan Validate akhir untuk perubahan ini tercatat pada PR integrasi GitHub App; jangan menjalankan build kernel atau publikasi hanya untuk menguji konfigurasi yang belum lengkap.

## Sudah selesai
### Perbaikan rilis dan pilihan GitHub App (owner 24 Okt)
- [Run rilis 40052126936](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/40052126936) gagal saat `gh release create`: HTTP 403. Build sumber `40046361218`, unduhan, SHA256 dan gate KMI lolos. Commit sumber `4730fee1297fa5ef1a779a4223136ab1912b09e2` memiliki workflow berbeda dari `main`; GITHUB_TOKEN bawaan tidak dapat diberi Workflows: write untuk membuat tag itu.
- **#27**, merge `8f6c580`: dukungan PAT `RELEASE_TOKEN` dan diagnostik 403. [Validate 40052599557](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/40052599557): **138/138 tes lolos**, YAML dan shell lolos.
- Owner memilih **GitHub App** agar tidak memperbarui PAT berkala. Workflow kini menyiapkan token baru lewat action resmi `actions/create-github-app-token@v3`, khusus repo ini, dengan Contents + Workflows: write. Token dibuat sesudah unduhan/gate dan dicabut action saat job selesai. Pemicu tetap `workflow_dispatch`; tidak ada jadwal atau rilis otomatis.
- `GITHUB_TOKEN` untuk baca run/artefak kini read-only. SHA publikasi memakai `run.json` yang sudah divalidasi, sehingga App tidak membutuhkan izin Actions. SHA256, gate KMI dan penolakan rilis duplikat tetap ketat. `RELEASE_TOKEN` PAT tidak dipakai lagi.
- Pengaturan yang harus tersedia: **variable** `RELEASE_APP_CLIENT_ID` = Client ID (bukan App ID); **secret** `RELEASE_APP_PRIVATE_KEY` = seluruh PEM. App harus terpasang pada `cogan17/Xiomi_14T_Pro` dengan Contents + Workflows: Read and write. Detail ID/EN: `docs/masalah-dan-log.md` dan `.en.md`.
- Tes rilis lokal: **10/10 lolos** (3 release notes + 7 tes workflow, termasuk konfigurasi tidak lengkap, publikasi tanpa izin Actions, SHA asli, Pre-Release/Release, duplikat, 403 dan 500). Input action dicocokkan dengan `action.yml` resmi v3. Ini bukti kode/simulasi; bukan bukti App terpasang atau publikasi sungguhan.
- Tidak ada private key, token, atau kredensial akun yang disimpan di source/checkpoint. Pendaftaran App dan uji rilis sungguhan masih menunggu owner.

### Dasar repo (owner 23 Okt)
- README simpel ID/EN, CHANGELOG, panduan, keaslian & kredit, modul Cogan Smart Kernel + tes, `CLAUDE.md` (tanpa kunci, gate KMI tetap, summary 2 bahasa, hemat run).
- **Workflow (semua manual):** Cogan Kernel Builder, Rilis dari run, Cogan Smart Release, Hapus log run lama, Cek sublevel baru. Validate hanya jalan di PR ke `main` (tes, YAML, shell; tanpa build).
- **Arsip:** r5, r6, r8, cogan-smart-v2.8.1 dan v2.8.2 dari `cogan17/Kernel-14t-pro`. Kernel arsip bernama arsip r5/r6/r8 dengan tag `arsip-v26.10.22-r5`, `arsip-v26.10.22-r6`, `arsip-v26.10.23-r8` (#7).

### r1: rilis pertama repo ini (terbukti CI dan HP)
- Builder run #2 [39992351534](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/39992351534): KSUN 6.1.176, SUSFS v2.3.0 `c27ebe9`, NoMount v2.2.0, gate `CRC differs 0`.
- Pre-release [`v26.10.23-r1`](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/v26.10.23-r1), diuji owner di HP. Cogan Smart v2.8.2 diuji owner di r1 (#12).

### Sesudah checkpoint 07.10 WIB
- **#16–#18:**
  - Klaim "ACK sampai 190" diluruskan: 6.1.190 adalah Linux stable, bukan ACK.
  - README memuat tabel sublevel yang didukung.
  - Sebutan 141 dihapus.
- **#19 form Builder:** centang SUSFS dihapus (SUSFS selalu ada), root default KernelSU Next. NoMount opsional; bila dicentang, selalu tertanam di kernel (bukan LKM).
- **#20 summary Builder:** satu tabel hasil dua bahasa (✅ berhasil, ❌ gagal + alasan, ⏳ tunggu siapa), ZIP + sha256.
- **#21 resolve:** coba ulang saat 429/503 dan satu Makefile per bulan. Run #5 gagal 429, run berikutnya lolos.
- **#22 Teks Telegram:** kotak kode ID/EN siap salin (✨ Baru diukur dari rilis sebelumnya, 🔧 Perbaikan dari commit `fix(kernel…)`). Muncul di summary Builder (satu build) dan Rilis dari run.
- **#23 + #25 Cek sublevel baru:** hanya manual oleh owner. Owner: "Jangan otomatis, Manual run workflow saja"; tanpa jadwal dan tanpa pemicu `workflow_run`.
  - Satu tombol: catat run Builder terakhir dari `main` (atau `run_id`) ke `kernel/sublevels.json` + tabel README, lalu bangun rilis ACK baru dengan semua fitur bila ada.
  - Tabel README menampilkan ✅ lolos build + gate KMI, ⏳ tunggu hulu, atau 🧪 repo pendahulu. Sublevel yang gagal di sini tidak dicantumkan.
  - Jangan mengedit tabel di antara penanda `sublevel:start/end` dengan tangan.
- **Run #6, bukti `semua` + Unicode fix** ([40048269498](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/40048269498), 08.06–08.34 WIB):
  - 176, 172, 162, 157: ✅ build + gate KMI, CRC beda 0, `UNICODE_FIX=fa76c90`.
  - 145 dan 138: ⏳ tunggu simonpunk. Patch SUSFS terbaru `c27ebe9` gagal 1 hunk di `fs/namespace.c`; Unicode fix sendiri terpasang bersih. Tag 138 yang dibangun sekarang `2025-06_r17` (rilis ACK terbaru di sublevel itu; kernel bawaan HP `r11`).
  - 141: ❌ ditolak gate KMI.
  - Hasilnya dicatat ke README (commit `3d2b531`, versi otomatis sebelum #25). #24 menyesuaikan kalimat Unicode fix di README dan CLAUDE.md.
- **r2 (kandidat Unicode fix) berjalan di HP** (owner, tangkapan layar 08.49 WIB, "r2 selesai"):
  - Versi kernel `6.1.176-Cogan-Rothko-ACK-r2-35f0a136c`, dibangun 07.47 WIB (00:47:23 UTC).
  - Builder run #4 [40046361218](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/40046361218): KSUN 6.1.176, Unicode fix, gate CRC beda 0 (juga terhadap stok 6.1.138).
  - Apakah r2 sudah diterbitkan belum dicek saat checkpoint.

## Belum terbukti
- Uji khusus Unicode fix di HP (nama file berkarakter tak terlihat) belum dilaporkan terpisah; yang dilaporkan: r2 berjalan di HP.
- Tombol Cek sublevel baru versi manual (#25) belum pernah ditekan. Bagian catat sudah terbukti lewat versi otomatis (run 40050437017).
- Terbit langsung dari Builder (Release Type Pre-Release/Release).
- Varian BakaSU (tunggu pengembang BakaSU: rc3 belum siap untuk SUSFS terbaru).
- ZIP dari Builder run #1 jangan dipakai (alat flasher 32-bit).

## Keputusan owner 24 Okt
- Repo lama `cogan17/Kernel-14t-pro` sudah diarsipkan: **abaikan**.
- r1 tetap Pre-release.
- Cek sublevel baru **hanya manual**; jangan menambah jadwal atau pemicu otomatis.
- Sublevel tidak diuji satu per satu di HP; cukup bukti CI.

## Langkah pertama sesi berikutnya
1. **Selesaikan pengaturan GitHub App**, setelah owner meminta: daftar pada akun cogan17, Webhook Active mati, tanpa OAuth/device flow, izin Contents + Workflows: Read and write, Only on this account. Pasang hanya ke `Xiomi_14T_Pro`.
2. Simpan Client ID di Actions variable `RELEASE_APP_CLIENT_ID` dan seluruh private key PEM di Actions secret `RELEASE_APP_PRIVATE_KEY`. Konektor GitHub sesi ini tidak memiliki operasi pendaftaran App/pengaturan secret; browser memerlukan login owner. Jangan meminta private key atau password lewat chat.
3. Setelah App dan konfigurasi lengkap, jalankan **Rilis dari run → Run workflow** terbaru dari `main`, `run_id=40046361218`, **Pre-Release**, diuji di HP `true`, catatan `Tested on my device.` (input yang digunakan owner pada run gagal). Gunakan artefak build hijau yang sama; tidak perlu membangun ulang. File rilis wajib tersedia sampai sekitar **31 Okt 2026, 08.02 WIB**. Jangan rerun job lama karena ia memakai workflow lama.
4. Verifikasi tag `v26.10.24-r2` menunjuk commit sumber `4730fee1297fa5ef1a779a4223136ab1912b09e2`, SHA256 aset sama dengan artefak, jenis Pre-release, dan summary ID/EN benar. Baru sesudah rilis terbukti terbit, catat r2 di CHANGELOG ID/EN dan status uji README.
5. Pekerjaan lain tetap tertunda: tabel sublevel lewat tombol **Cek sublevel baru** manual; 145/138 menunggu simonpunk; BakaSU menunggu pengembangnya. Jangan melanjutkannya tanpa permintaan owner.

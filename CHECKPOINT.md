# Checkpoint — 24 Okt 2026, 09.55 WIB · r2 terbit dan tercatat

Sesi berikutnya mulai dari sini. Aturannya ada di `CLAUDE.md`. Semua waktu dalam WIB.

## Sedang berjalan
- Tidak ada.

## Sudah selesai
### r2 terbit (terbukti CI dan HP)
- Pre-release [`v26.10.24-r2`](https://github.com/cogan17/Cogan-Kernel/releases/tag/v26.10.24-r2), terbit 09.39 WIB lewat [Rilis dari run 40055078111](https://github.com/cogan17/Cogan-Kernel/actions/runs/40055078111) (owner), dari Builder run [40046361218](https://github.com/cogan17/Cogan-Kernel/actions/runs/40046361218).
- Isi: ACK 6.1.176 (`2026-09_r4`), KernelSU Next dev-susfs `d21e0a6` (33405), SUSFS v2.3.0 `c27ebe9`, NoMount v2.2.0, Unicode fix `fa76c90`, gate KMI CRC beda 0. Label "diuji di HP" (owner menjalankan r2 di HP, 08.49 WIB).
- r2 tercatat di CHANGELOG ID/EN, status uji README dan catatan sublevel 176 (`kernel/sublevels.json` → `sublevels.py readme`). Status: diuji di HP; owner mengonfirmasi Unicode fix terpasang di r2 (09.50 WIB) dan bekerja (uji Termux 09.54 WIB: `UJI.txt` ditemukan, `u`+U+200B+`ji.txt` tidak ditemukan).
- Tag menunjuk `main` `7fafb5a` (aturan #29, workflow commit build berbeda). Aset: ZIP kernel `sha256:1e3cd537…ea11`, manager dan spoofed sama dengan arsip r5/r6, NoMount v2.2.0, `checksums.txt`.

### Perbaikan Rilis dari run (owner 24 Okt)
- [Run rilis 40052126936](https://github.com/cogan17/Cogan-Kernel/actions/runs/40052126936) gagal saat `gh release create`: HTTP 403. Build sumber `40046361218`, unduhan, SHA256 dan gate KMI lolos. Commit sumber `4730fee1297fa5ef1a779a4223136ab1912b09e2` memiliki workflow berbeda dari `main`; GITHUB_TOKEN bawaan tidak dapat diberi Workflows: write untuk membuat tag itu.
- **#27**, merge `8f6c580`: dukungan PAT `RELEASE_TOKEN` dan diagnostik 403. [Validate 40052599557](https://github.com/cogan17/Cogan-Kernel/actions/runs/40052599557): **138/138 tes lolos**, YAML dan shell lolos.
- #28 (GitHub App) diganti atas saran Claude yang diikuti owner: **tanpa App, PAT atau secret**. Langkah Terbitkan membandingkan tree `.github/workflows` commit build dengan commit yang menjalankan rilis; sama → tag di commit build, beda → tag di `GITHUB_SHA` (aturan lama repo pendahulu yang sudah terbukti). Untuk run 40046361218 tree-nya beda (`2fcfc9e` vs `004fde4` di `main`), jadi tag menunjuk commit `main`. #29 merge `7fafb5a`, Validate lolos; terbukti oleh rilis r2.

### Dasar repo (owner 23 Okt)
- README simpel ID/EN, CHANGELOG, panduan, keaslian & kredit, modul Cogan Smart Kernel + tes, `CLAUDE.md` (tanpa kunci, gate KMI tetap, summary 2 bahasa, hemat run).
- **Workflow (semua manual):** Cogan Kernel Builder, Rilis dari run, Cogan Smart Release, Hapus log run lama, Cek sublevel baru. Validate hanya jalan di PR ke `main` (tes, YAML, shell; tanpa build).
- **Arsip:** r5, r6, r8, cogan-smart-v2.8.1 dan v2.8.2 dari `cogan17/Kernel-14t-pro`. Kernel arsip bernama arsip r5/r6/r8 dengan tag `arsip-v26.10.22-r5`, `arsip-v26.10.22-r6`, `arsip-v26.10.23-r8` (#7).

### r1: rilis pertama repo ini (terbukti CI dan HP)
- Builder run #2 [39992351534](https://github.com/cogan17/Cogan-Kernel/actions/runs/39992351534): KSUN 6.1.176, SUSFS v2.3.0 `c27ebe9`, NoMount v2.2.0, gate `CRC differs 0`.
- Pre-release [`v26.10.23-r1`](https://github.com/cogan17/Cogan-Kernel/releases/tag/v26.10.23-r1), diuji owner di HP. Cogan Smart v2.8.2 diuji owner di r1 (#12).

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
- **Run #6, bukti `semua` + Unicode fix** ([40048269498](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498), 08.06–08.34 WIB):
  - 176, 172, 162, 157: ✅ build + gate KMI, CRC beda 0, `UNICODE_FIX=fa76c90`.
  - 145 dan 138: ⏳ tunggu simonpunk. Patch SUSFS terbaru `c27ebe9` gagal 1 hunk di `fs/namespace.c`; Unicode fix sendiri terpasang bersih. Tag 138 yang dibangun sekarang `2025-06_r17` (rilis ACK terbaru di sublevel itu; kernel bawaan HP `r11`).
  - 141: ❌ ditolak gate KMI.
  - Hasilnya dicatat ke README (commit `3d2b531`, versi otomatis sebelum #25). #24 menyesuaikan kalimat Unicode fix di README dan CLAUDE.md.
- **r2 (kandidat Unicode fix) berjalan di HP** (owner, tangkapan layar 08.49 WIB, "r2 selesai"):
  - Versi kernel `6.1.176-Cogan-Rothko-ACK-r2-35f0a136c`, dibangun 07.47 WIB (00:47:23 UTC).
  - Builder run #4 [40046361218](https://github.com/cogan17/Cogan-Kernel/actions/runs/40046361218): KSUN 6.1.176, Unicode fix, gate CRC beda 0 (juga terhadap stok 6.1.138).
  - Diterbitkan 09.39 WIB sebagai Pre-release `v26.10.24-r2` (lihat di atas).

## Belum terbukti
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
1. Tidak ada yang mendesak. Pekerjaan yang tertunda: tabel sublevel lewat tombol **Cek sublevel baru** manual; 145/138 menunggu simonpunk; BakaSU menunggu pengembangnya. Jangan melanjutkannya tanpa permintaan owner.

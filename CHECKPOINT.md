# Checkpoint — 24 Okt 2026, ±00.20 WIB

Sesi berikutnya mulai dari sini. Aturannya ada di `CLAUDE.md`. Semua waktu dalam WIB.

## Sedang berjalan
- Tidak ada run Actions atau PR terbuka di repo ini. #1–#5 sudah di-merge.

## Sudah selesai (repo baru, owner 23 Okt)
- **Fase A:** README simpel ID/EN, CHANGELOG, panduan, keaslian & kredit lengkap, modul Cogan Smart Kernel + 75 tes, `CLAUDE.md` (tanpa kunci, gate KMI tetap, summary 2 bahasa, hemat run).
- **Arsip rilis:** r5, r6, r8, cogan-smart-v2.8.1 dan v2.8.2 disalin dari `cogan17/Kernel-14t-pro` (run 39981928955, SHA256 cocok). Kernel arsip diganti nama 24 Okt (owner) menjadi arsip r5, arsip r6, arsip r8 dengan tag `arsip-v26.10.22-r5`, `arsip-v26.10.22-r6`, `arsip-v26.10.23-r8`.
- **Workflow:** Cogan Kernel Builder, Rilis dari run, Cogan Smart Release, Hapus log run lama (diuji mode cek).
- **Builder run 1** (39984036101, KSUN & BakaSU, `lts`, CI), terbukti CI:
  - KSUN 6.1.176, fork pershoot `d21e0a6` (33405), SUSFS `c27ebe9`, NoMount v2.2.0;
  - gate `CRC differs 0` terhadap BSP dan stok 6.1.138;
  - BakaSU tidak dibangun: tunggu pengembang BakaSU (rc3 belum siap untuk SUSFS terbaru).
- **Perbaikan setelah run 1:**
  - #4: ccache disimpan di `~/.ccache`.
  - #5: alat AnyKernel3 dari branch osm0sis `arm64-tools`. Flash r1 di HP gagal karena alat 32-bit (`magiskboot: syntax error`); flash berhenti sebelum `boot` ditulis. Paket kini ditolak bila ada alat non-arm64 (diuji lokal).
  - #5: Rilis dari run mengunduh file lewat ID artifact + cek SHA256. Run 39990063457 gagal karena `gh run download` membongkar ZIP kernel.

## Belum terbukti
- Build dengan perbaikan #4 dan #5 (belum ada run baru, sesuai aturan hemat run).
- Flash di HP, jalur Rilis dari run, dan terbit langsung dari Builder.
- ZIP r1 (run 1) **jangan dipakai**: alat flasher-nya 32-bit.

## Menunggu keputusan owner
1. Izin satu run Builder baru: Release Type **CI**, KernelSU Next, `lts`. Hasilnya untuk di-flash owner.
2. Repo lama `cogan17/Kernel-14t-pro`:
   - branch `feat/builder-centang-opsional`, PR #146 dan #147 (tanpa SUSFS, `ENGINE_COMMIT 3461993`) dibuat Claude di sesi lain atas permintaan owner 23 Okt (D-032); PR #148 masih terbuka;
   - run 31/32 dari branch itu hijau.
   - Belum disentuh.
3. r9 (repo lama, run 22, BakaSU + NoMount v2.2.0) menunggu uji HP. Pengingat 25 Okt 12.30 WIB masih menunjuk repo lama.

## Langkah pertama sesi berikutnya
1. Jangan lanjut sebelum owner meminta.
2. Bila owner setuju, jalankan satu run Builder (CI, KernelSU Next, `lts`). Periksa alat arm64 di ZIP dan gate KMI, lalu serahkan ZIP untuk di-flash owner.

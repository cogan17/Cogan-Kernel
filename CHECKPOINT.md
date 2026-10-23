# Checkpoint — 24 Okt 2026, ±00.20 WIB (diperbarui ±06.30 WIB: r1 diuji di HP)

Sesi berikutnya mulai dari sini. Aturannya ada di `CLAUDE.md`. Semua waktu dalam WIB.

## Sedang berjalan
- Tidak ada run Actions atau PR terbuka di repo ini. #1–#9 sudah di-merge.

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

- **r1, rilis pertama repo ini** (owner, 24 Okt), terbukti CI dan HP:
  - Builder run #2 ([39992351534](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/39992351534), 00.06 WIB, commit `ebab365` dengan perbaikan #4 dan #5): KSUN 6.1.176, SUSFS v2.3.0 `c27ebe9`, NoMount v2.2.0, gate `CRC differs 0`.
  - Terbit sebagai Pre-release [`v26.10.23-r1`](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/v26.10.23-r1) lewat Rilis dari run #3 (05.51 WIB), ditandai diuji di HP. Rilis dari run #2 (05.42 WIB) ditolak di langkah *Periksa run*: ID run `39238126721` bukan run Builder repo ini.
  - Diuji owner di HP (tangkapan layar KernelSU Next ±05.57 WIB): BUILT-IN (GKI2) 33405, SUSFS v2.3.0, NoMount v2.2.0 (605) terpasang, SELinux Enforcing. Modul NoMount v2.2.0 hanya mau dipasang di kernel dengan driver v22, jadi yang berjalan memang r1 (arsip r6 membawa driver v21).
  - Versi kernel di layar manager tampil `6.1.170-android14-11-g9876543210ab…`, bukan 6.1.176: kemungkinan besar disamarkan spoof uname SUSFS. Versi asli: `su -c cat /sys/kernel/cogan/banner`.
- **Arsip r5, r6, r8** pindah ke tag `arsip-…` (#7, run 40038421596; id rilis, nama file dan SHA256 sama; tag lama dihapus). Tombol sekali pakainya dihapus (#8).
- **README dan CHANGELOG** mencatat r1 sebagai rilis repo ini yang diuji di HP (#9).

## Belum terbukti
- Terbit langsung dari Builder (Release Type Pre-Release/Release).
- Varian BakaSU di repo ini (belum dibangun: tunggu pengembang BakaSU).
- ZIP dari Builder run #1 (bukan rilis r1) **jangan dipakai**: alat flasher-nya 32-bit.

## Menunggu keputusan owner
1. Repo lama `cogan17/Kernel-14t-pro`:
   - branch `feat/builder-centang-opsional`, PR #146 dan #147 (tanpa SUSFS, `ENGINE_COMMIT 3461993`) dibuat Claude di sesi lain atas permintaan owner 23 Okt (D-032); PR #148 masih terbuka;
   - run 31/32 dari branch itu hijau.
   - Belum disentuh.
2. r9 (repo lama, run 22, BakaSU + NoMount v2.2.0) menunggu uji HP. Pengingat 25 Okt 12.30 WIB masih menunjuk repo lama.

## Langkah pertama sesi berikutnya
1. Jangan lanjut sebelum owner meminta.
2. Tanyakan langkah berikutnya: varian BakaSU (menunggu pengembang BakaSU), sisa repo lama (PR #148), dan r9.

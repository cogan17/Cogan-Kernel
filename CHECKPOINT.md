# Checkpoint — 24 Okt 2026, ±00.20 WIB (diperbarui ±07.10 WIB: Validate, Unicode fix, Cogan Smart di r1, bersih branch)

Sesi berikutnya mulai dari sini. Aturannya ada di `CLAUDE.md`. Semua waktu dalam WIB.

## Sedang berjalan
- Tidak ada run Actions atau PR terbuka di repo ini. #1–#15 sudah di-merge. Branch tinggal `main`.

## Sudah selesai (repo baru, owner 23 Okt)
- **Fase A:** README simpel ID/EN, CHANGELOG, panduan, keaslian & kredit lengkap, modul Cogan Smart Kernel + 75 tes, `CLAUDE.md` (tanpa kunci, gate KMI tetap, summary 2 bahasa, hemat run).
- **Arsip rilis:** r5, r6, r8, cogan-smart-v2.8.1 dan v2.8.2 disalin dari `cogan17/Kernel-14t-pro` (run 39981928955, SHA256 cocok). Kernel arsip diganti nama 24 Okt (owner) menjadi arsip r5, arsip r6, arsip r8 dengan tag `arsip-v26.10.22-r5`, `arsip-v26.10.22-r6`, `arsip-v26.10.23-r8`.
- **Workflow:** Cogan Kernel Builder, Rilis dari run, Cogan Smart Release, Hapus log run lama (diuji mode cek), Validate (#10).
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
- **Yang digabung dari WildKernel (owner 24 Okt: "yang bisa digabungkan, lanjutkan"; jangan merusak yang ada):**
  - #10 **Validate** di setiap PR: tes, YAML workflow, sintaks shell; tanpa build kernel (±30 detik). `.gitignore` untuk `__pycache__`; 18 file `.pyc` keluar dari git.
  - #11 **centang Unicode Fix**, mati secara default: patch terbaru `WildKernels/kernel_patches` dipasang ketat; tidak cocok = "Tunggu WildKernel"; gate KMI tetap. Patch hanya mengubah `fs/unicode/utf8-norm.c`, yang identik di Linux stable 6.1–6.1.190 (kernel.org, **bukan ACK**) dan di ACK 6.1.138. ACK terbaru saat ini 6.1.176 (`android14-6.1-2026-09_r4`). Terbukti: ACK 6.1.138 (lokal, patch terpasang ketat) dan 6.1.176 (CI). ACK 145, 157, 162 dan 172 belum dibuktikan langsung, diharapkan cocok; bila tidak, build berhenti "Tunggu WildKernel". Bukti CI [run 40041706993](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/40041706993) (KSUN 6.1.176, CI): gate `CRC differs 0` (juga terhadap stok 6.1.138), fitur `SUSFS, BBRv3 (default, also bbr3), BBG, NoMount, Unicode fix, Cogan Bridge, Full LTO`, `UNICODE_FIX=fa76c90`.
  - Tidak berlaku untuk rothko: Ptrace (kernel < 5.16), BTF (sudah aktif di kernel bawaan), FUSE-BPF (6.12). Tetap tidak dipakai: DroidSpaces, NTSync, Performance, `allow_version_mismatch`, page size, keep_kmi.
- **Cogan Smart Kernel fokus ke r1** (#12): owner menguji v2.8.2 di r1 (tangkapan layar 06.47 WIB: Cogan r1 · 6.1.176 terverifikasi lewat Cogan Bridge, mengecas cepat 3868 mA, pencatat suhu, penjaga modul aman). Label rilis `cogan-smart-v2.8.2` = "r1 (6.1.176) + arsip r6, termasuk HyperCharge" (run 40041708914); default `kernel_uji` = `r1 (6.1.176)`.
- **Bersih branch:** "Automatically delete head branches" diaktifkan owner. 9 branch PR #1–#9 dihapus lewat tombol sekali pakai (#13, run 40043075372; dari sesi Claude hapus branch ditolak 403), tombolnya dihapus (#14).

## Belum terbukti
- Unicode fix di HP: mengubah cara nama file berkarakter tak terlihat dicocokkan di penyimpanan internal. Uji HP sebelum build dengan centang ini dirilis.
- Terbit langsung dari Builder (Release Type Pre-Release/Release).
- Varian BakaSU di repo ini (belum dibangun: tunggu pengembang BakaSU).
- ZIP dari Builder run #1 (bukan rilis r1) **jangan dipakai**: alat flasher-nya 32-bit.

## Keputusan owner 24 Okt
- Repo lama `cogan17/Kernel-14t-pro` sudah diarsipkan owner: **abaikan** (termasuk PR #148 dan r9). Pengingat 25 Okt 12.30 WIB yang masih menunjuk repo lama juga diabaikan.
- r1 **tetap Pre-release** ("ada hal yang perlu dipastikan").

## Langkah pertama sesi berikutnya
1. Jangan lanjut sebelum owner meminta.
2. Owner: run bukti `semua` dengan centang Unicode Fix (KernelSU Next, ACK 138–176) "nanti saja"; jalankan hanya bila owner meminta.
3. Bila owner mau, uji Unicode fix: satu build CI (KernelSU Next, `lts`, centang Unicode Fix) untuk di-flash owner, lalu cek nama file di penyimpanan internal tetap normal.
4. Varian BakaSU tetap menunggu pengembang BakaSU; summary Builder memberi tahu bila sudah siap.

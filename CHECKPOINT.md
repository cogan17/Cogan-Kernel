# Checkpoint

Catatan terbaru: **[checkpoint.md](checkpoint.md)**. **CHECKPOINT owner 29 Okt 2026 ±11.15 WIB: semua pekerjaan dihentikan.**

- **v2.11.2 (versionCode 30), rilis DITAHAN owner:** perbaikan Mulai yang kembali berhenti setelah root manager ditutup (pekerja keluar dari cgroup aplikasi). Paket uji di `modules/cogan-smart/rilis/v2.11.2/`, belum diuji di HP. PR #80 perlu merge `main`, versionCode 31 dan `leave_app_cgroup` di `apps/block.sh`.
- **Sedang berjalan:** [PR #80](https://github.com/cogan17/Cogan-Kernel/pull/80) (`feat/cogan-smart-tab-aplikasi`): Cogan Smart v2.12.0 dengan tab 📱 Aplikasi. Commit WIP `5130ca8` menambah blokir untuk email, SMS dan sosmed lain (33 paket).
- **Belum:** ZIP `rilis/v2.12.0` belum dikemas ulang setelah commit WIP, dan SHA-nya belum diganti di README dan checkpoint. Validate belum dicek, PR belum di-merge, ZIP belum dikirim. Belum diuji di HP.
- **Langkah pertama:** di branch PR #80, kemas ulang ZIP dua kali, ganti SHA, jalankan tes, push, lalu cek Validate, merge dan kirim ZIP.
- **Sudah:** v2.11.1 (#79) ✅ lolos uji owner di HP. v2.10.8 ✅ ZRAM ZSTD saat boot. Rilis kernel hanya membawa modul SUSFS sidex15 (#76).
- Baca `CLAUDE.md` dan `checkpoint.md`, lalu lanjut **hanya setelah owner meminta**.

# Checkpoint

Catatan terbaru: **[checkpoint.md](checkpoint.md)** — 29 Okt 2026, ±21.50 WIB. Tidak ada PR atau workflow yang berjalan.

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

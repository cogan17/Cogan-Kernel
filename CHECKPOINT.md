# Checkpoint

Catatan terbaru: **[checkpoint.md](checkpoint.md)** — 29 Okt 2026 (WIB).

- v2.12.0 (versionCode 30): tab 📱 Aplikasi (pantau gerak-gerik, hapus sampai akar, blokir APK dari chat & sosmed). Paket uji di `modules/cogan-smart/rilis/v2.12.0/`; belum diuji di HP dan belum dirilis.
- v2.11.1 (versionCode 29): Manager hanya memantau, sekali usap keluar dari WebUI. ✅ Lolos uji owner di HP 29 Okt. Belum dirilis.
- v2.11.0 (versionCode 28): Manager pusat kendali, Mode Dev, Panduan ID/EN. Di `main` lewat PR #77 (29 Okt 09.55 WIB); paket uji di `modules/cogan-smart/rilis/v2.11.0/`, belum diuji di HP dan belum dirilis.
- v2.10.8 (versionCode 27): hook ZRAM pada `load-bpf-programs`, sesudah lz4 vendor dan sebelum `system_perf_init` Xiaomi menyalakan ZRAM (v2.10.7 terlambat). Paket uji di `modules/cogan-smart/rilis/v2.10.8/`. ✅ Diuji di HP 28 Okt 23.23 WIB: `zram0: zstd`, hook `load-bpf-programs matching`. Belum dirilis.
- v2.10.6 (hook init berjalan) dan v2.10.5 (deteksi DRAM) sudah di `main` dan terkonfirmasi di HP.
- Rilis kernel hanya membawa modul SUSFS sidex15 (PR #76).
- Baca `CLAUDE.md` dan `checkpoint.md`, lalu tunggu instruksi owner.

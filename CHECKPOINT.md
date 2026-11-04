# Checkpoint

## 4 Nov 2026 (checkpoint owner)

**Sedang berjalan**
- Tidak ada PR/run/draf berjalan. Diagnosa CoganSU r36 selesai (di bawah); perbaikannya menunggu izin owner (repo CoganSU).

**Run #36 dicek: build lolos, manager CoganSU "Tidak terpasang" (bug sertifikat)**
- Run #36 ([41773264948](https://github.com/cogan17/Cogan-Kernel/actions/runs/41773264948)) lolos: artifact `1-KERNEL_…CoganSU+SuSFS…v26.11.04-r36`, `2-MANAGER_CoganSU_v26.11.04-r1.apk`, NoMount v2.2.0, modul SUSFS sidex15. Owner flash r36 di HP 4 Nov ±11.55 WIB: boot dan root/su jalan.
- **Tapi manager CoganSU "Tidak terpasang".** Bukti (APK + Image r36 + dmesg owner): kernel menemukan APK (`Found manager com.cogan.su …, is_manager: 0`) lalu menolaknya. APK benar — paket `com.cogan.su`, sertifikat ukuran `0x04ed` hash `b0fb06ca…` (= `cogansu.mk`). Kernel r36 memuat nama paket benar, tetapi `b0fb06ca` tidak ada di Image: identitas sertifikat yang dikompilasi bukan dari `cogansu.mk`, masih sertifikat KernelSU bawaan.
- Akar: di `Kbuild` CoganSU `KSU_PACKAGE_NAME ?=` berlaku (paket benar), tetapi `KSU_EXPECTED_SIZE/HASH ?=` tidak — keduanya sudah ter-set dari environment `make` sebelum `?=`. Sumber env belum ketemu di tiga repo secara static; perlu dilihat saat build jalan.
- Perbaikan diusulkan: paksa `cogansu.mk` otoritatif (`override KSU_EXPECTED_SIZE/HASH := …` di `Kbuild` CoganSU), lalu Build CoganSU r37 untuk uji. **Menunggu izin owner** (repo `cogan17/CoganSU`).

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
- Perbaiki identitas sertifikat CoganSU (di atas), lalu Build CoganSU r37 untuk uji HP. Menunggu izin owner.
- Penyebab NoMount menolak aturan di SukiSU (telusuri kode, tanpa HP).
- CoganSU di kombinasi root bila owner mau.
- Rilis r8 (run #20) hanya atas permintaan owner.

**Langkah pertama berikutnya**
- Setelah izin owner: perbaiki `Kbuild` CoganSU agar `EXPECTED_SIZE/HASH` memakai `cogansu.mk`, jalankan Build CoganSU r37, lalu minta owner cek manager jadi "Berfungsi". Lanjut hanya setelah owner meminta.

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

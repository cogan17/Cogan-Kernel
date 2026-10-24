# 📝 Catatan Rilis

[← Kembali ke README](README.md) · <img src="https://flagcdn.com/24x18/gb.png" width="22" alt=""> [English](CHANGELOG.en.md)

Versi teratas = build terbaru. Build yang lolos uji HP terbit sebagai **Pre-release** di [Releases](https://github.com/cogan17/Xiomi_14T_Pro/releases); belum ada rilis resmi.

> 📦 r2–r8 dan percobaan awal dibuat di repo pendahulu [cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro). Rilis r5, r6 dan r8 disalin ke Releases repo ini sebagai arsip dengan file yang sama. Di repo ini namanya **arsip r5, arsip r6, arsip r8** dan tagnya berawalan `arsip-` (mis. `arsip-v26.10.22-r5`), supaya tidak bentrok dengan nomor rilis repo ini sendiri.

## r2 — 24 Okt 2026 · `6.1.176-Cogan-Rothko-ACK-r2` · [Pre-release](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/v26.10.24-r2)

**KernelSU Next + SUSFS** di ACK resmi Google 6.1.176 (`android14-6.1-2026-09_r4`), sama seperti r1, ditambah Unicode fix.

### ✨ Baru
- **Unicode fix** (WildKernel `fa76c90`): nama file dengan karakter tak terlihat (mis. *zero-width*) di penyimpanan internal tidak lagi dianggap sama dengan nama tanpanya. Centang opsional di Builder, mati secara default; r2 dibangun dengan centang ini.

Komponen lain sama dengan r1: KernelSU Next `d21e0a6` (33405), SUSFS v2.3.0 (`c27ebe9`), NoMount v2.2.0.

Status: ✅ lolos uji HP owner (24 Okt): kernel `6.1.176-Cogan-Rothko-ACK-r2-35f0a136c` berjalan dengan Unicode fix terpasang. Gate KMI: 0 simbol berbeda.

## r1 — 24 Okt 2026 · `6.1.176-Cogan-Rothko-ACK-r1` · [Pre-release](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/v26.10.23-r1)

Rilis pertama repo ini: **KernelSU Next + SUSFS** di ACK resmi Google 6.1.176 (`android14-6.1-2026-09_r4`), dengan komponen versi terbaru saat build.

### ✨ Baru
- Root **KernelSU Next** (`d21e0a6`, 33405) + **SUSFS v2.3.0** (`c27ebe9`). Manager biasa dan *spoofed* versi 33405.
- **NoMount v2.2.0**: driver di kernel dan modul di rilis versi yang sama.

### 🔧 Diperbaiki
- Alat flasher AnyKernel3 kini versi **arm64**. ZIP r1 dari build pertama tidak dirilis: alatnya 32-bit (`magiskboot: syntax error`), flash berhenti sebelum `boot` ditulis.

Status: ✅ lolos uji HP owner (KernelSU Next berfungsi, SUSFS v2.3.0, NoMount v2.2.0, SELinux Enforcing; 24 Okt). Gate KMI: 0 simbol berbeda.

## arsip r8 — 23 Okt 2026 · `6.1.176-Cogan-Rothko-ACK-r8` · [Pre-release](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/arsip-v26.10.23-r8)

Varian **BakaSU + SUSFS** di ACK resmi Google 6.1.176. Varian KernelSU Next tetap arsip r6.

### ✨ Baru
- Root **BakaSU** `v4.2.0-rc3-5b76b884` (35222) + **SUSFS v2.3.0** (`2474336`). Versi driver kernel dan manager sama, 35222.

### ⏳ Menunggu BakaSU
- Pengembang BakaSU memblokir build SUSFS sejak 10 Okt. Kernel ini memakai versi sebelum blokir sampai blokirnya dibuka; setelah itu build berikutnya pindah ke BakaSU terbaru.
- r7 tidak dirilis: manager-nya ternyata masih bernama ReSukiSU (rc3, sebelum proyek berganti nama).

Status: ✅ lolos uji HP owner (BakaSU berfungsi, SUSFS v2.3.0, SELinux Enforcing; 23 Okt). Gate KMI: 0 simbol berbeda.

## arsip r6 — 22 Okt 2026 · `6.1.176-Cogan-Rothko-ACK-r6` · [Pre-release](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/arsip-v26.10.22-r6)

Dibangun dari **ACK resmi Google `android14-6.1-2026-09_r4` (6.1.176)**, rilis ACK terbaru, bukan lagi 6.1.138 bawaan HP.

### ✨ Baru
- Kernel **6.1.176**. Builder kini bisa memilih semua rilis ACK resmi android14-6.1 sejak kernel bawaan HP: 138, 141, 145, 157, 162, 172 dan 176.

### 🔧 Diperbaiki
- Simbol kernel kini **sama persis** dengan yang dipakai modul vendor HP: gate KMI mencatat 0 simbol berbeda (arsip r5: 2, r3: 538). BBRv3 tetap aktif.

Status: ✅ boot dan cek HP owner aman (22 Okt).

## arsip r5 — 22 Okt 2026 · `6.1.138-Cogan-Rothko-ACK-r5` · [Pre-release](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/arsip-v26.10.22-r5)

### 🔧 Diperbaiki
- Versi KernelSU Next di kernel kini **33405**, sama dengan manager CI resmi `v3.4.2-50-gb427a3f9`, jadi manager tidak lagi meminta update (r4: 33418).
- Paket rilis berisi manager biasa dan *spoofed* versi 33405, serta modul NoMount v2.1.1.

Status: ✅ lolos uji HP (KernelSU Next berfungsi, SUSFS v2.3.0, SELinux Enforcing). Cadangan 6.1.138 yang sudah terbukti.

## r4 — 22 Okt 2026 · `6.1.138-Cogan-Rothko-ACK-r4`

### ✨ Baru
- SUSFS dan KernelSU Next (fork pershoot `dev-susfs`) versi terbaru.
- ZIP kernel bertanda tangan (GitHub attestation).

### 🔧 Diperbaiki
- Simbol yang berbeda dari kernel bawaan turun dari 538 ke 2: perubahan struktur oleh BBRv3 tidak lagi terlihat oleh modul vendor.

Status: ✅ lolos uji HP (Wi-Fi, kamera, SUSFS; "Tidak ada bug").

## r3 — 22 Okt 2026 · `6.1.138-Cogan-Rothko-ACK-r3`

### ✨ Baru
- **Cogan Bridge** di dalam kernel (`/sys/kernel/cogan`): identitas kernel asli di balik penyamaran SUSFS, target perangkat (`rothko`) dan SoC dari device tree, detak modul Cogan Smart, dan batas CPU yang dilepas otomatis bila modul berhenti.
- Perangkat, kernel dan modul **Cogan Smart Kernel** saling mengenal: WebUI menampilkan "✓ kernel dibuat untuk HP ini".

Status: 🔄 uji 3 hari di HP maintainer.

## r2 — 17 Okt 2026 · `6.1.138-Cogan-Rothko-ACK-r2`

Build pertama dari **kernel bawaan rothko** (ACK `android14-6.1-2025-06_r11`), untuk HyperOS `OS3.0.301.0.WNNIDXM`.

### ✨ Baru
- **KernelSU Next** bawaan kernel + **SUSFS** v2.3.0.
- **NoMount**, **Baseband Guard**, **BBRv3** sebagai TCP bawaan, Full LTO.
- Gate KMI: tiap build dicek terhadap ABI kernel bawaan; gagal = tidak ada ZIP.
- ZIP AnyKernel3 dengan cek perangkat (`rothko` saja).

### 🔧 Diketahui
- Modul vendor dimuat lewat *force-load* (banyak baris `disagrees about version of symbol` di `dmesg`). Diperbaiki di revisi berikutnya.

Status: ✅ lolos uji HP 3 tahap (boot, root, semua hardware, cas 120W, game, reboot, semalam).

## Percobaan awal — 16 Okt 2026 · GKID `6.1.177`

Kernel dari GKI-Duchamp (GKID) berhasil boot di rothko. Lalu diganti ke sumber kernel bawaan agar paling cocok dengan modul vendor HyperOS.

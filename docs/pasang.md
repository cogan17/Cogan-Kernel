# 📥 Pasang Kernel

[← Kembali ke README](../README.md) · <img src="https://flagcdn.com/24x18/gb.png" width="22" alt=""> [English](pasang.en.md)

Kernel Cogan hanya mengganti partisi **`boot`**. Data, `init_boot` dan `vendor_boot` tidak disentuh.

---

## Sebelum mulai

- Bootloader sudah **unlock**.
- HyperOS **`OS3.0.301.0.WNNIDXM`** (Android 16), versi yang dipakai uji. Kernel dibangun dari ACK resmi Google android14-6.1: arsip r8 dan r6 dari 6.1.176 (`2026-09_r4`), arsip r5 dari 6.1.138 (sama dengan kernel bawaan HyperOS versi ini).
- ZIP kernel `1-KERNEL_Cogan-Rothko-ACK-…zip`. ZIP berisi cek perangkat, jadi di HP selain `rothko` flash berhenti sebelum `boot` disentuh.

## 1. Cadangkan `boot` dulu

Pilih salah satu cara:

- **Kernel Flasher** → slot aktif → **Backup** → `boot`.
- **TWRP** → **Backup** → centang **Boot**.

Salin hasilnya ke **PC atau flashdisk**, jangan hanya di HP. Simpan juga `boot.img` **stok** dari ROM HyperOS versi yang sama.

## 2. Flash

**Dengan Kernel Flasher (butuh root):**

1. Buka [Kernel Flasher](https://github.com/fatalcoder524/KernelFlasher) → slot aktif → **Flash** → **Flash AK3 Zip**.
2. Pilih ZIP kernel, tunggu selesai, lalu **Reboot**.

**Dengan TWRP:**

1. Masuk TWRP, lalu **Install** → pilih ZIP kernel → geser.
2. **Reboot → System.**

## 3. Setelah menyala

1. Pasang aplikasi root manager dari paket rilis yang sama (**KernelSU Next** atau **BakaSU**, sesuai ZIP kernel), lalu metamodule **NoMount**.
2. *Opsional:* modul **[Cogan Smart Kernel](https://github.com/cogan17/Xiomi_14T_Pro/blob/main/modules/cogan-smart/README.md)**. Pengembangannya sedang diparkir (hanya perbaikan bug); kernel berjalan normal tanpanya. Bila dipasang, reboot sekali, lalu cek di WebUI modul: **"Identitas asli · terverifikasi"** dan **"✓ kernel dibuat untuk HP ini"**.

> 💡 Versi kernel di Setelan bisa tampil lain (mis. `6.1.170`). Itu SUSFS yang menyamarkan `uname`. Identitas asli dibaca modul Cogan Smart lewat Cogan Bridge.

---

Bootloop? Lihat **[Kembali ke Stok](kembali-ke-stok.md)**.

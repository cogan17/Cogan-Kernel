# ↩️ Kembali ke Stok

[← Kembali ke README](../README.md) · <img src="https://flagcdn.com/24x18/gb.png" width="22" alt=""> [English](kembali-ke-stok.en.md)

Mau kembali ke kernel bawaan, atau HP bootloop setelah flash? **Data tidak dihapus.** Cukup kembalikan partisi **`boot`**.

---

## HP masih menyala

- **Kernel Flasher** → slot aktif → **Restore** → pilih cadangan `boot`, lalu reboot.
- Atau **TWRP** → **Install → Install Image** → pilih `boot.img` cadangan/stok → **boot** → geser → **Reboot → System**.

## HP bootloop (muter di logo Mi)

**Penyebabnya modul, bukan kernel?** Coba ini dulu:

1. Paksa mati: tahan **Power ~15 detik**.
2. Nyalakan. Setelah layar boot pertama muncul, tekan **Volume Bawah lebih dari 3 kali** (tekan-lepas, bukan ditahan).
3. KernelSU masuk *safe mode*: semua modul nonaktif. Copot modul bermasalah di aplikasi root manager (KernelSU Next atau BakaSU), lalu reboot.

**Penyebabnya kernel** (atau safe mode tidak menolong):

1. Tahan **Power + Volume Bawah** → **FASTBOOT**.
2. Colok ke PC, lalu jalankan:
   ```
   fastboot flash boot boot.img
   fastboot reboot
   ```
   `boot.img` = cadangan sebelum flash, atau `boot.img` stok dari ROM HyperOS versi yang **sama persis**.
3. Punya TWRP? Bisa juga **Install → Install Image → boot** tanpa PC.

Bootloader tidak pernah disentuh kernel ini, jadi FASTBOOT selalu bisa diakses.

---

## ⛔ Jangan pernah

- Menjalankan **`flash_all_lock`** dari ROM fastboot. Bootloader terkunci dengan partisi yang sudah diubah bisa membuat HP mati total.
- Mem-flash ROM **lebih lama** dari versi terpasang. Anti-rollback Xiaomi bisa membuat HP mati total.
- Mem-flash `boot.img` ke partisi lain (`init_boot`, `vendor_boot`, …).
- Memakai SP Flash Tool / mode BROM. Bisa menghapus kalibrasi modem/IMEI.

Masih bootloop setelah `boot.img` stok? Flash ROM fastboot resmi versi yang sama dengan **`flash_all_except_storage`** (data tetap ada).

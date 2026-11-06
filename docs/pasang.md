# 📥 Pasang Kernel

[← Kembali ke README](../README.md) · <img src="https://flagcdn.com/24x18/gb.png" width="22" alt=""> [English](pasang.en.md)

Kernel Cogan hanya mengganti partisi **`boot`**. Data, `init_boot` dan `vendor_boot` tidak disentuh.

---

## Sebelum mulai

- Bootloader sudah **unlock**.
- **Catat versi kernel bawaan HP-mu sebelum flash**: Setelan → Tentang ponsel → Versi kernel. Setelah flash, nilai ini berganti dan dipakai lagi di langkah 3 (samarkan kernel).
- Kernel ini untuk Xiaomi 14T Pro (`rothko`) **dari wilayah mana pun** (Indonesia, Global, EEA, Turki, …), asalkan versi kernel bawaannya salah satu dari ini:

  | Versi kernel bawaan | HyperOS |
  |---|---|
  | `6.1.157-android14-11-g0baf70f2581d-ab15659624` | `OS3.0.302` (Android 16) |
  | `6.1.138-android14-11-g6ab8c9a86a33-ab14396278` | `OS3.0.301` |

  Setiap build dicek terhadap kedua kernel bawaan itu. Uji HP dilakukan di ROM Indonesia (`OS3.0.302.0.WNNIDXM` dan `OS3.0.301.0.WNNIDXM`). ROM wilayah lain memakai kernel bawaan yang sama bila versinya sama persis. **Bila versi kernel bawaanmu berbeda, jangan flash dulu**: kirim versinya ke grup Telegram, supaya kernel bawaan itu ditambahkan ke pengecekan build.
- Kernel dibangun dari ACK resmi Google android14-6.1.
- ZIP kernel `1-KERNEL_Cogan-Rothko-ACK-…zip`. ZIP berisi cek perangkat, jadi di HP selain `rothko` flash berhenti sebelum `boot` disentuh.

## 0. Pasang root dulu (bila belum punya root)

Kernel Cogan di-flash lewat **Kernel Flasher** yang butuh root, jadi **root harus ada lebih dulu**. Baru buka bootloader (UBL) belum berarti sudah root. Lewati bagian ini bila HP sudah punya root (mis. pindah dari kernel lain).

Root dipasang di partisi **`init_boot`**, bukan `boot`. Kernel Cogan dan KernelSU Next/CoganSU bertipe **GKI** (root menyatu di kernel), jadi caranya mem-*patch* `init_boot`, bukan modul LKM.

Siapkan di PC: **platform-tools** (`adb`/`fastboot`) resmi Google dan kabel USB.

1. Pasang aplikasi root manager (**KernelSU Next** atau **CoganSU**) dari paket rilis.
2. Ambil `init_boot.img` **stok** dari ROM HyperOS versi yang sama dengan HP. Simpan juga salinannya sebagai cadangan.
3. Di aplikasi root manager → menu **Install / Pasang** → **Pilih dan patch file** → pilih `init_boot.img`. Hasilnya `init_boot_patched.img` (atau nama sejenis) di folder `Download`.
4. Salin `init_boot_patched.img` ke PC. Masuk mode fastboot: `adb reboot bootloader` (atau matikan HP lalu tahan **Volume Bawah + Power**).
5. Flash: `fastboot flash init_boot init_boot_patched.img`, lalu `fastboot reboot`.
6. Setelah menyala, buka aplikasi root manager → pastikan statusnya **terpasang / working** dan versi kernel terbaca. Root sudah aktif.

> ⚠️ Jangan `fastboot flash boot` dengan file `init_boot`, dan sebaliknya. Salah partisi bisa bootloop.
> Gagal atau bootloop? Flash `init_boot` **stok** balik: `fastboot flash init_boot init_boot.img`. Partisi `boot` dan data tidak tersentuh di langkah ini.

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
   Bila ZIP kernel bernama `…+SuSFS…` dan ingin mengatur SUSFS, pasang juga **modul SUSFS** `5-SUSFS-MODULE-SIDEX15_…zip`: modul sidex15 dengan WebUI (build CI terbarunya), memasang alat `ksu_susfs`. Rilis 26–28 Okt 2026 juga berisi modul simonpunk (`5-…SIMONPUNK`) dan menomori modul sidex15 `6-`; pasang salah satunya saja. Modul [BRENE](https://github.com/rrr333nnn333/BRENE) juga modul SUSFS: pasang sidex15 **atau** BRENE, jangan keduanya (BRENE mematikan modul SUSFS lain).
2. *Opsional:* modul **[Cogan Smart Kernel](https://github.com/cogan17/Cogan-Kernel/blob/main/modules/cogan-smart/README.md)**. Pengembangannya sedang diparkir (hanya perbaikan bug); kernel berjalan normal tanpanya. Bila dipasang, reboot sekali, lalu cek di WebUI modul: **"Identitas asli · terverifikasi"** dan **"✓ kernel dibuat untuk HP ini"**.
3. *Opsional, untuk menyamarkan kernel dari aplikasi pendeteksi:* buka WebUI modul SUSFS → **Kernel Uname**, lalu isi nilai yang sama dengan versi kernel bawaan yang kamu catat sebelum flash (dibaca dari `boot.img` stok rothko). Centang kotak di sebelah **Spoof Kernel Version** dan **Spoof Kernel Build**.
   - **Kernel bawaan `6.1.157`** (HyperOS `OS3.0.302`):
     - Spoof Kernel Version:
       ```
       6.1.157-android14-11-g0baf70f2581d-ab15659624
       ```
     - Spoof Kernel Build:
       ```
       #1 SMP PREEMPT Tue Jun 16 21:49:26 UTC 2026
       ```
   - **Kernel bawaan `6.1.138`** (HyperOS `OS3.0.301`):
     - Spoof Kernel Version:
       ```
       6.1.138-android14-11-g6ab8c9a86a33-ab14396278
       ```
     - Spoof Kernel Build (ada **dua spasi** sebelum `5`):
       ```
       #1 SMP PREEMPT Wed Nov  5 15:47:39 UTC 2025
       ```
   - Biarkan **Spoof on boot** dan **Execute on post-fs-data** tercentang, lalu reboot.
   - Cek di Termux **tanpa** `su`: `uname -a` harus menampilkan kedua nilai di atas persis.

   Aplikasi biasa hanya bisa membaca `uname`, jadi kernel tampil persis seperti kernel bawaan. Terbukti di HP owner (2 Nov 2026): Duck Detector **Kernel Check: No suspicious kernel markers**. Nilai ini milik kernel bawaan HyperOS saat ini; bila HyperOS diperbarui dan kernel bawaannya berubah, nilainya ikut diganti. Ini tidak menyembunyikan jejak KernelSU itu sendiri (mis. tipe SELinux `ksu`), yang tetap bisa terdeteksi.

   **Cara melihat kernel yang asli** (Termux; ketik satu per satu, izinkan root bila diminta):

   | Perintah | Yang tampil |
   |---|---|
   | `su -c cat /sys/kernel/cogan/banner` | Identitas Cogan asli: versi kernel, nomor rilis (mis. `r33`), pembuat dan tanggal build. Paling pasti, tidak ikut disamarkan |
   | `su -c cat /proc/version` | Versi kernel yang benar-benar berjalan (mis. `6.1.176`, bukan nilai samaran) |
   | `uname -a` (tanpa `su`) | Yang dilihat aplikasi biasa: nilai samaran di atas (mis. `6.1.157-android14-11-g0baf70f2581d-ab15659624`) |

   Bila perintah pertama menunjukkan Cogan, perintah kedua versi aslinya, dan `uname -a` menunjukkan nilai samaran itu, semuanya bekerja benar: kernel aslinya Cogan, aplikasi melihat kernel bawaan.

> 💡 Versi kernel di Setelan bisa tampil lain (mis. `6.1.157`). Itu SUSFS yang menyamarkan `uname`. Identitas asli dibaca modul Cogan Smart lewat Cogan Bridge.

---

Bootloop? Lihat **[Kembali ke Stok](kembali-ke-stok.md)**.

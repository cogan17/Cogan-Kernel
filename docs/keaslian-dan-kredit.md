# 🔏 Keaslian & Kredit

[← Kembali ke README](../README.md) · <img src="https://flagcdn.com/24x18/gb.png" width="22" alt=""> [English](keaslian-dan-kredit.en.md)

Kernel Cogan untuk Xiaomi 14T Pro (`rothko`) dibangun otomatis oleh GitHub Actions di **[cogan17/Xiomi_14T_Pro](https://github.com/cogan17/Xiomi_14T_Pro)**. ZIP kernel **ditandatangani secara digital** (artifact attestation) oleh workflow build repo ini, jadi siapa pun bisa membuktikan asal-usulnya.

Repo ini lanjutan dari **[cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro)**. Rilis lama dari repo itu disalin ke sini sebagai **arsip** (lihat [Arsip rilis](#-arsip-rilis)). File arsip tidak berubah satu bit pun: SHA256-nya sama, dan tanda tangannya tetap atas nama repo asalnya.

> Yang dibuktikan adalah **build kernel rothko ini** dibuat oleh Cogan17. Kernel Linux, Android Common Kernel dan fitur-fitur di dalamnya adalah karya para kontributor di [Kredit](#-kredit).

---

## Cara cek keaslian

1. **Halaman bukti:** [github.com/cogan17/Xiomi_14T_Pro/attestations](https://github.com/cogan17/Xiomi_14T_Pro/attestations) untuk build repo ini; [github.com/cogan17/Kernel-14t-pro/attestations](https://github.com/cogan17/Kernel-14t-pro/attestations) untuk rilis arsip.
2. **Lewat GitHub CLI:**
   ```
   gh attestation verify <zip> --repo cogan17/Xiomi_14T_Pro     # build repo ini
   gh attestation verify <zip> --repo cogan17/Kernel-14t-pro    # rilis arsip r5, r6, r8 (tag arsip-…)
   ```
   Hanya ZIP asli yang lolos.
3. **Halaman run di [Actions](https://github.com/cogan17/Xiomi_14T_Pro/actions):** tiap build menampilkan hasil gate KMI, versi setiap komponen, daftar fitur, dan sha256 ZIP-nya.
4. **Di HP** (Termux / terminal root manager):
   ```
   su -c cat /sys/kernel/cogan/banner
   ```
   Menampilkan versi asli, pembuat dan tanggal build. File ini dibuat **Cogan Bridge** di dalam kernel, jadi tidak ikut tersamar oleh SUSFS.
5. **Modul Cogan Smart Kernel:** tab mana pun → kartu Kernel → **"Identitas asli · terverifikasi"** dan **"✓ kernel dibuat untuk HP ini"**.
6. **File lain di rilis** (manager, NoMount, modul Cogan Smart Kernel) tidak ditandatangani. Cocokkan SHA256-nya dengan `checksums.txt` di rilis itu atau daftar di bawah.

## Apa yang dibuktikan, dan tidak

| Kalau ada yang… | Hasilnya |
|---|---|
| menyebar ulang ZIP lalu mengaku buatannya | ✅ terbantah: sidik jarinya cocok dengan tanda tangan repo Cogan17 |
| mengubah ZIP sedikit (mis. nama di banner AnyKernel3) | ✅ ketahuan: jadi file lain, tidak lolos verifikasi |
| fork repo lalu build sendiri | ✅ tanda tangan mereka menyebut **repo mereka**; riwayat commit bertanggal di repo ini membuktikan siapa yang lebih dulu |
| menyalin kodenya | tidak dicegah (proyek terbuka), tapi asal-usulnya tetap bisa dibuktikan |
| mengganti manager, NoMount atau modul di rilis tiruan | ✅ ketahuan: SHA256-nya tidak cocok |

---

## 📦 Arsip rilis

Disalin dari [cogan17/Kernel-14t-pro/releases](https://github.com/cogan17/Kernel-14t-pro/releases) pada 23 Okt 2026, dengan file yang sama. Di [Releases](https://github.com/cogan17/Xiomi_14T_Pro/releases) repo ini judulnya diawali **📦 Arsip**, dan tag kernelnya berawalan `arsip-` (24 Okt 2026) supaya r5, r6 dan r8 tidak bentrok dengan nomor rilis repo ini. Di repo asal tagnya tetap tanpa awalan.

### Kernel (ditandatangani repo asal)

| Rilis | Kernel | Root | Diuji | Tanda tangan |
|---|---|---|---|---|
| [arsip-v26.10.23-r8](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/arsip-v26.10.23-r8) | ACK 6.1.176 (`android14-6.1-2026-09_r4`) | BakaSU `5b76b884` (35222) + SUSFS v2.3.0 | owner di HP | ✅ run [39899556040](https://github.com/cogan17/Kernel-14t-pro/actions/runs/39899556040) |
| [arsip-v26.10.22-r6](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/arsip-v26.10.22-r6) | ACK 6.1.176 (`android14-6.1-2026-09_r4`) | KernelSU Next (fork pershoot `d21e0a6`, 33405) + SUSFS | owner di HP | ✅ run [39807276281](https://github.com/cogan17/Kernel-14t-pro/actions/runs/39807276281) |
| [arsip-v26.10.22-r5](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/arsip-v26.10.22-r5) | ACK 6.1.138 (sama dengan kernel bawaan HP) | KernelSU Next (33405) + SUSFS | owner di HP | ✅ run [39760534547](https://github.com/cogan17/Kernel-14t-pro/actions/runs/39760534547) |

Semuanya juga membawa BBRv3, Baseband Guard, NoMount, Cogan Bridge dan Full LTO. Cek dengan `gh attestation verify <zip> --repo cogan17/Kernel-14t-pro`.

### Ikut di rilis kernel (bukan buatan Cogan17)

| File | Asal |
|---|---|
| `2-MANAGER_BakaSU_ci-5b76b884c75f.apk` (arsip r8) | Manager BakaSU `v4.2.0-rc3-5b76b884` (35222) milik owner, versi yang sama dengan driver di kernel |
| `2-MANAGER_KernelSU-Next_v3.4.2-50-gb427a3f9_33405.apk` (arsip r5, r6) | Build CI resmi [KernelSU Next](https://github.com/KernelSU-Next/KernelSU-Next) commit `b427a3f9` (33405) |
| `3-MANAGER-SPOOFED_KernelSU-Next_v3.4.2-50-gb427a3f9_33405.apk` (arsip r5, r6) | Build CI resmi KernelSU Next, varian spoofed (nama paket disamarkan) |
| `4-NOMOUNT-MODULE_v2.1.1.zip` (arsip r5, r6, r8) | Rilis resmi [NoMount](https://github.com/maxsteeel/nomount/releases) v2.1.1 (`NoMount-v2.1.1-release-7046c7a-555.zip`), hanya diganti nama |
| `checksums.txt` | Daftar SHA256 semua file di rilis itu |

### Modul Cogan Smart Kernel (dibuat Cogan17)

| Rilis | versionCode | Diuji |
|---|---|---|
| [cogan-smart-v2.8.2](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/cogan-smart-v2.8.2) | 16 | owner di HP dengan r1 (24 Okt) dan arsip r6, termasuk pengisian HyperCharge |
| [cogan-smart-v2.8.1](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/cogan-smart-v2.8.1) | 15 | owner di HP |

ZIP-nya dibuat Cogan17 dan diterbitkan **apa adanya** (byte per byte). Salinannya ada di [`modules/cogan-smart/rilis/`](../modules/cogan-smart/rilis) dan sumber terbukanya di [`modules/cogan-smart`](../modules/cogan-smart). Belum ditandatangani (attestation).

### SHA256 semua file arsip

Format `sha256sum`: di Termux, `sha256sum <file>` harus menghasilkan angka yang sama.

```
2f630d65694c3585336d9a2e6cb0d8514737f3aa5d4170612fc388d4f6f944a2  1-KERNEL_Cogan-Rothko-ACK-6.1.176_BakaSU+SuSFS_v26.10.23-r8.zip
f3bba663d07e583c4355ae4e7888018fd15b030ecdddb705855c09611070a1f0  1-KERNEL_Cogan-Rothko-ACK-6.1.176_KernelSU-Next+SuSFS_v26.10.22-r6.zip
b69446d4a1bed0b1abe87945091a902310d63d8c28565d4764aa2797cc7e5d74  1-KERNEL_Cogan-Rothko-ACK-6.1.138_KernelSU-Next+SuSFS_v26.10.22-r5.zip
c4c461d77d2043a25531e32fdba77848acbdc4764a23ac1ab824fa477947874c  2-MANAGER_BakaSU_ci-5b76b884c75f.apk
43acb0587741b845712a12c1ea08cacb8aede72118f4895312745a6769a45fda  2-MANAGER_KernelSU-Next_v3.4.2-50-gb427a3f9_33405.apk
608d167f580dc0d5094f07eb9d0ff48118e068506e52ffc22d6425404e786e05  3-MANAGER-SPOOFED_KernelSU-Next_v3.4.2-50-gb427a3f9_33405.apk
aeae97436cf3c83f032d4d2a837581cd51b56c93eaf952e459f358d20ce39931  4-NOMOUNT-MODULE_v2.1.1.zip
73f6d9c9a167d1528057ff84c65d6db371a5cde63e1435ca6e5e4f14bfc367d5  Cogan-Smart-Kernel-v2.8.2.zip
441e0780d77480f6642a84f5478ce61d659110a640ca6b025f51d2c718ce594f  Cogan-Smart-Kernel-v2.8.1.zip
```

---

## 🙏 Kredit

| Siapa | Kontribusi |
|---|---|
| **Cogan17** | Maintainer: kernel Cogan Rothko, Cogan Bridge, modul Cogan Smart Kernel, mesin build, CI dan rilis |
| **[Google](https://android.googlesource.com/kernel/common/)** | Android Common Kernel `android14-6.1` (sumber kernel bawaan rothko), BBRv3 |
| **Xiaomi & MediaTek** | Sumber BSP rothko (acuan simbol dan konfigurasi), modul vendor dan firmware; hak milik masing-masing |
| **[KernelSU](https://github.com/tiann/KernelSU)** (tiann) | Dasar root di dalam kernel |
| **[KernelSU Next](https://github.com/KernelSU-Next/KernelSU-Next)** (rifsxd) | Root manager varian KernelSU Next; aplikasi manager di rilis adalah build CI resmi |
| **[pershoot](https://github.com/pershoot/KernelSU-Next)** | Fork KernelSU Next `dev-susfs` yang menyatukan KernelSU Next dengan SUSFS |
| **[BakaSU](https://github.com/Baka-SU/BakaSU)** | Root manager varian BakaSU (dulu ReSukiSU) |
| **[SUSFS](https://gitlab.com/simonpunk/susfs4ksu)** (simonpunk) | Menyembunyikan jejak root |
| **[NoMount](https://github.com/maxsteeel/nomount)** (maxsteeel) | Metamodule tanpa mount, tertanam di kernel; modul di rilis adalah rilis resminya |
| **[Baseband Guard](https://github.com/vc-teahouse/Baseband-guard)** (vc-teahouse) | Perlindungan partisi |
| **[AnyKernel3](https://github.com/osm0sis/AnyKernel3)** (osm0sis) | Installer ZIP kernel |
| **[Neutron Clang](https://github.com/Neutron-Toolchains)** | Compiler kernel |
| **[Kernel Flasher](https://github.com/fatalcoder524/KernelFlasher)** (fatalcoder524) | Aplikasi flash dan cadangan `boot` |
| **[WildKernels](https://github.com/WildKernels/GKI_KernelSU_SUSFS)** | Inspirasi tampilan form workflow build dan Validate; patch Unicode fix opsional dari [kernel_patches](https://github.com/WildKernels/kernel_patches) |
| **GKI-Duchamp · AK3-GKID** (Ahmed Al-Nassif) | Dasar percobaan kernel awal (tidak dipakai lagi) |
| **[cogan17/Cogan](https://github.com/cogan17/Cogan)** | Asal mesin build |

Proyek saudara: **[TWRP Xiaomi 14T Pro](https://github.com/cogan17/TWRP-14T-PRO)** · repo pendahulu: **[Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro)**.

# 🔏 Keaslian & Kredit

[← Kembali ke README](../README.md) · <img src="https://flagcdn.com/24x18/gb.png" width="22" alt=""> [English](keaslian-dan-kredit.en.md)

Kernel Cogan untuk Xiaomi 14T Pro (`rothko`) dibangun otomatis oleh GitHub Actions di **[cogan17/Cogan-Kernel](https://github.com/cogan17/Cogan-Kernel)** (sampai 24 Okt 2026 bernama `Xiomi_14T_Pro`; tautan lama dialihkan GitHub). ZIP kernel **ditandatangani secara digital** (artifact attestation) oleh workflow build repo ini, jadi siapa pun bisa membuktikan asal-usulnya.

Repo ini lanjutan dari **[cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro)**. Rilis lama dari repo itu disalin ke sini sebagai **arsip** (lihat [Arsip rilis](#-arsip-rilis)). File arsip tidak berubah satu bit pun: SHA256-nya sama, dan tanda tangannya tetap atas nama repo asalnya.

> Yang dibuktikan adalah **build kernel rothko ini** dibuat oleh Cogan17. Kernel Linux, Android Common Kernel dan fitur-fitur di dalamnya adalah karya para kontributor di [Kredit](#-kredit).

---

## Cara cek keaslian

1. **Halaman bukti:** [github.com/cogan17/Cogan-Kernel/attestations](https://github.com/cogan17/Cogan-Kernel/attestations) untuk build repo ini; [github.com/cogan17/Kernel-14t-pro/attestations](https://github.com/cogan17/Kernel-14t-pro/attestations) untuk rilis arsip.
2. **Lewat GitHub CLI:**
   ```
   gh attestation verify <zip> --repo cogan17/Cogan-Kernel     # build repo ini setelah ganti nama (24 Okt 2026)
   gh attestation verify <zip> --repo cogan17/Xiomi_14T_Pro    # r1, r2 dan build lain sebelum ganti nama
   gh attestation verify <zip> --repo cogan17/Kernel-14t-pro   # rilis arsip r5, r6, r8 (tag arsip-…)
   ```
   Hanya ZIP asli yang lolos. Tanda tangan menyimpan nama repo saat build, jadi r1 dan r2 tetap menyebut `Xiomi_14T_Pro` (repo yang sama, sebelum ganti nama). `--owner cogan17` menerima ketiganya.
3. **Halaman run di [Actions](https://github.com/cogan17/Cogan-Kernel/actions):** tiap build menampilkan hasil gate KMI, versi setiap komponen, daftar fitur, dan sha256 ZIP-nya.
4. **Di HP** (Termux / terminal root manager):
   ```
   su -c cat /sys/kernel/cogan/banner
   ```
   Menampilkan versi asli, pembuat dan tanggal build. File ini dibuat **Cogan Bridge** di dalam kernel, jadi tidak ikut tersamar oleh SUSFS.
5. **Modul Cogan Smart Kernel:** tab mana pun → kartu Kernel → **"Identitas asli · terverifikasi"** dan **"✓ kernel dibuat untuk HP ini"**.
6. **File lain di rilis** (manager, NoMount, modul Cogan Smart Kernel) tidak ditandatangani. Cocokkan SHA256-nya dengan `checksums.txt` di rilis itu (modul Cogan Smart: tabel di [README modul](../modules/cogan-smart/README.md)).

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

Rilis lama dari [cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro/releases) (arsip r5, r6, r8) disalin apa adanya ke [Releases](https://github.com/cogan17/Cogan-Kernel/releases) repo ini: judulnya diawali **📦 Arsip** dan tag kernelnya berawalan `arsip-`. Setiap rilis membawa catatan, `checksums.txt` dan tanda tangan repo asalnya sendiri. Rilis dan SHA256 modul Cogan Smart Kernel ada di [README modul](../modules/cogan-smart/README.md).

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

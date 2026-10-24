<h1 align="center">Cogan Kernel · Xiaomi 14T Pro</h1>

<p align="center">
  <code>rothko</code> &nbsp;·&nbsp; HyperOS &nbsp;·&nbsp; Android 16 &nbsp;·&nbsp; Linux 6.1 GKI
</p>

<p align="center">
  <b><img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> Bahasa Indonesia</b> &nbsp;·&nbsp; <a href="README.en.md"><img src="https://flagcdn.com/24x18/gb.png" width="22" alt=""> English</a>
</p>

<p align="center">
  <a href="https://github.com/cogan17/Cogan-Kernel/releases"><b>⬇️ Unduh Kernel</b></a>
  &nbsp;·&nbsp;
  <a href="docs/pasang.md"><b>📖 Panduan</b></a>
  &nbsp;·&nbsp;
  <a href="CHANGELOG.md"><b>📝 Catatan Rilis</b></a>
  &nbsp;·&nbsp;
  <a href="modules/cogan-smart/README.md"><b>🧠 Modul Cogan Smart</b></a>
  &nbsp;·&nbsp;
  <a href="https://t.me/coganTWRP"><b>💬 Komunitas Telegram</b></a>
</p>

> [!WARNING]
> **Masih tahap uji.** Build yang lolos uji di HP maintainer terbit sebagai **Pre-release** di [Releases](https://github.com/cogan17/Cogan-Kernel/releases); belum ada rilis resmi. Flash hanya bila kamu sudah punya cadangan `boot` dan paham cara [kembali ke stok](docs/kembali-ke-stok.md).

---

### 📖 Panduan Pengguna

|   |   |
|---|---|
| 📥 **[Pasang Kernel](docs/pasang.md)** | Cadangkan `boot`, lalu flash lewat Kernel Flasher atau TWRP |
| 🧠 **[Modul Cogan Smart](modules/cogan-smart/README.md)** | Mode daya, suhu, penjaga modul |
| ↩️ **[Kembali ke Stok](docs/kembali-ke-stok.md)** | Batalkan kernel / perbaiki bootloop |
| 🩺 **[Masalah & Log](docs/masalah-dan-log.md)** | Kalau ada kendala |

---

<details>
<summary>📱 <b>Spesifikasi perangkat</b></summary>

| Item | Detail |
|---|---|
| Chipset | MediaTek Dimensity 9300+ (MT6989) |
| CPU | 4× Cortex-X4 hingga 3,4 GHz |
| GPU | Immortalis-G720 MC12 |
| RAM | 12 / 16 GB |
| Layar | 1220 × 2712 |
| Rilis | September 2024 (Android 14) |
| Kernel bawaan | `6.1.138-android14-11` (HyperOS `OS3.0.301.0.WNNIDXM`) |

</details>

<details>
<summary>✨ <b>Isi kernel</b></summary>

- ✅ Sumber kernel resmi Google (Android Common Kernel `android14-6.1`), sekeluarga dengan kernel bawaan HP. Modul vendor Xiaomi/MediaTek tetap cocok
- ✅ Selalu versi terbaru: rilis ACK, root manager, SUSFS dan NoMount diambil terbaru saat build. Bila ada yang belum cocok, ringkasan build menyebut pengembang mana yang perlu ditunggu
- ✅ Root bawaan kernel + **SUSFS**, dua varian: **KernelSU Next** atau **BakaSU**
- ✅ **NoMount** (modul tanpa mount, tertanam di kernel), **Baseband Guard**
- ✅ **BBRv3** sebagai TCP bawaan (`bbr` dan `bbr3`)
- ✅ **Cogan Bridge**: kernel dan modul Cogan Smart saling mengenal (`/sys/kernel/cogan`)
- ✅ Full LTO, cek perangkat di ZIP (hanya `rothko`)
- ⚙️ Opsional, mati secara default: **Unicode fix** (WildKernel). Nama file berisi karakter tak terlihat (mis. zero-width) di penyimpanan internal tidak lagi dianggap sama dengan nama tanpa karakter itu (celah *unicode bypass* untuk menemukan path yang disembunyikan)
- ✅ Tiap build dicek otomatis terhadap ABI kernel bawaan (gate KMI); gagal = tidak ada ZIP

</details>

<details>
<summary>🧩 <b>Sublevel yang didukung</b></summary>

Builder memakai rilis ACK resmi `android14-6.1` sejak kernel bawaan HP; `lts` = yang terbaru. Tombol workflow **Cek sublevel baru** mencatat hasil build terakhir di tabel ini (✅ lolos build dan gate KMI, ⏳ menunggu pembaruan hulu), lalu membangun rilis ACK baru dengan semua fitur bila ada.

<!-- sublevel:start -->
| Sublevel | Rilis ACK | Status |
|---|---|---|
| **176** (`lts`) | `2026-09_r4` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498) · r1 dan r2 diuji di HP |
| 172 | `2026-06_r14` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498) |
| 162 | `2026-03_r24` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498) |
| 157 | `2025-12_r32` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498) |
| 145 | `2025-09_r36` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40061712549) |
| 138 | `2025-06_r17` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40061712549) · kernel bawaan HP; arsip r5 diuji di HP |
<!-- sublevel:end -->

Unicode fix (opsional) lolos build + gate KMI di 157, 162, 172 dan 176, dan terpasang bersih di 138 dan 145 ([CI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498)). Bila patch WildKernel belum cocok, build berhenti: lepas centang Unicode fix untuk tetap build.

</details>

<details>
<summary>🧪 <b>Status uji</b></summary>

| Build | Hasil |
|---|---|
| `r2` (ACK 6.1.176 · KernelSU Next · Unicode fix) | ✅ Diuji di HP 24 Okt: Unicode fix bekerja (nama dengan *zero-width space* tidak lagi cocok dengan file aslinya) |
| `r1` (ACK 6.1.176 · KernelSU Next) | ✅ Diuji di HP 24 Okt: KernelSU Next berfungsi, SUSFS v2.3.0, NoMount v2.2.0, SELinux Enforcing |
| `arsip r8` (ACK 6.1.176 · BakaSU) | ✅ Diuji di HP 23 Okt: BakaSU berfungsi, SUSFS v2.3.0, SELinux Enforcing |
| `arsip r6` (ACK 6.1.176 · KernelSU Next) | ✅ Diuji di HP 22 Okt |
| `arsip r5` (ACK 6.1.138 · KernelSU Next) | ✅ Diuji di HP; cadangan yang terbukti |

`r1` dan `r2` rilis repo ini; tiga lainnya rilis arsip dari repo pendahulu. Riwayat lengkap: [Catatan Rilis](CHANGELOG.md).

</details>

---

<p align="center">
  Maintainer <b>Cogan17</b> &nbsp;·&nbsp; sumber <b>Android Common Kernel</b> &nbsp;·&nbsp; <b>KernelSU Next</b> &nbsp;·&nbsp; <b>BakaSU</b> &nbsp;·&nbsp; <b>SUSFS</b>
  <br><a href="docs/keaslian-dan-kredit.md">🔏 Keaslian & kredit lengkap</a>
</p>

<sub>Repo pendahulu (riwayat pengembangan, sumber BSP Xiaomi): [cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro)</sub>

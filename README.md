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
> Jika terjadi bootloop atau brick, bukan tanggung jawab maintainer/developer. Pemilik device bertanggung jawab atas devicenya sendiri! Harap cadangkan datamu.

> [!TIP]
> TWRP sudah tersedia untuk Xiaomi 14T Pro. Kamu bisa mendownload [TWRP](https://github.com/cogan17/TWRP-14T-PRO).

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
- ✅ Root bawaan kernel + **SUSFS**, dua varian: **KernelSU Next** atau **BakaSU**. SUSFS dicentang secara default; bila centangnya dilepas, kernel memakai root manager biasa tanpa SUSFS (nama ZIP tanpa `+SuSFS`, tanpa modul SUSFS)
- ✅ **NoMount** (modul tanpa mount, tertanam di kernel), **Baseband Guard**
- ✅ **BBRv3** sebagai TCP bawaan (`bbr` dan `bbr3`)
- ✅ **Cogan Bridge**: kernel dan modul Cogan Smart saling mengenal (`/sys/kernel/cogan`)
- ✅ Tanpa LTO sebagai bawaan (build lebih cepat; Thin/Full LTO tetap bisa dipilih), cek perangkat di ZIP (hanya `rothko`)
- ⚙️ Opsional, dicentang secara default: **Unicode fix** (WildKernel). Nama file berisi karakter tak terlihat (mis. zero-width) di penyimpanan internal tidak lagi dianggap sama dengan nama tanpa karakter itu (celah *unicode bypass* untuk menemukan path yang disembunyikan)
- ⚙️ Opsional, **mati secara default**: **Samarkan identitas kernel**. `uname` dan `/proc/version` memakai format GKI bawaan (`6.1.176-android14-11-g…-ab…`), bukan nama `Cogan`. Hanya tampilan, bukan penyembunyian berbasis perilaku
- ✅ Tiap build dicek otomatis terhadap ABI kernel bawaan (gate KMI); gagal = tidak ada ZIP

</details>

<details>
<summary>🧩 <b>Sublevel yang didukung</b></summary>

Builder memakai rilis ACK resmi `android14-6.1` sejak kernel bawaan HP; `lts` = yang terbaru; isian Kernel Sublevel dikosongkan = semua sublevel. Tombol workflow **Catat sublevel** mencatat hasil build terakhir di tabel ini (✅ lolos build dan gate KMI, ⏳ menunggu pembaruan hulu); ia tidak mengecek dan tidak membangun.

Tombol **Cek pembaruan** satu-satunya yang mengecek, dan tidak membangun: versi terbaru setiap komponen (ACK, KernelSU Next, BakaSU, SUSFS simonpunk dan modul SUSFS sidex15, NoMount, Baseband Guard, AnyKernel3, Neutron clang, Unicode fix) dibandingkan dengan build terakhir, dengan tanggal rilis stabil dan CI, yang baru dan perbaikannya, dan siapa yang ditunggu bila belum bisa dibangun. Bila ada yang baru, ringkasannya menyarankan menjalankan Builder.

**[Riwayat build](kernel/history/)** disimpan otomatis oleh Builder dalam dokumen Markdown. **Build terakhir** dan **Status** tetap bisa dibandingkan setelah log, artifact atau run Actions dihapus; **Hapus log run lama** bekerja seperti sebelumnya.

<!-- sublevel:start -->
| Sublevel | Rilis ACK | Status |
|---|---|---|
| **176** (`lts`) | `2026-09_r5` | ✅ KernelSU Next · BakaSU: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40853374637) · r1 dan r2 diuji di HP |
| 172 | `2026-06_r14` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498) |
| 162 | `2026-03_r24` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498) |
| 157 | `2025-12_r32` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498) |
| 145 | `2025-09_r36` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40061712549) |
| 138 | `2025-06_r17` | ✅ KernelSU Next: [build + gate KMI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40061712549) · kernel bawaan HP; arsip r5 diuji di HP |
<!-- sublevel:end -->

Unicode fix (dicentang otomatis sejak 1 Nov 2026) lolos build + gate KMI di 157, 162, 172 dan 176, dan terpasang bersih di 138 dan 145 ([CI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498)). Bila patch WildKernel belum cocok, build berhenti: lepas centang Unicode fix untuk tetap build.

🛡️ **CVE-2026-53163** dipasang otomatis di setiap build: perbaikan resmi Linux 6.1.177 (commit `40a25d59e85b`) untuk crash kernel lewat futex yang muncul sejak perbaikan CVE-2026-43499 di 6.1.175. ACK yang belum punya perbaikan CVE-2026-43499 (di bawah 175) tidak punya bug ini, dan ACK yang sudah berisi perbaikannya dilewati.

🫥 **Samarkan identitas kernel** (centang, mati secara default): `uname` dan `/proc/version` meniru kernel bawaan HP (diambil dari boot.img stok rothko): format GKI `6.1.176-android14-11-g<commit ACK>-ab…`, pembuat `build-user@build-host`, dan teks Android clang 17.0.2 / LLD 17.0.2 milik Google, bukan nama `Cogan` dan Neutron clang. Versinya tetap versi asli (mis. 6.1.176). Ini hanya mengubah tampilan, tidak mengubah kode kernel, jadi gate KMI tidak terpengaruh. Cogan Bridge dan modul Cogan Smart tetap jalan; nama `Cogan` dan nomor rilis tetap ada di nama file ZIP dan catatan rilis. Ini **tidak** melawan deteksi berbasis perilaku (jejak root, mount, properti) maupun pengecekan lewat chip keamanan HP (Play Integrity). Uji HP dulu.

Untuk menerbitkan build yang sudah selesai, jalankan **Rilis dari run** dengan ID run Builder yang hijau. Run yang berisi KernelSU Next dan BakaSU diterbitkan menjadi **satu rilis** dengan kedua ZIP kernel dan APK manager masing-masing, tanpa kompilasi ulang. Centang **diuji di HP** hanya bila semua varian dalam run itu sudah diuji owner. Bila tag yang sama sudah ada (mis. `v26.11.02-r21`: nomor rN owner dan nomor run build CI bisa bertemu di hari yang sama), rilis berhenti; centang **timpa** untuk mengganti rilis lama itu beserta file-nya dengan build dari run ini. Hanya rilis kernel `vYY.MM.DD-rN` yang bisa ditimpa; arsip dan Cogan Smart tidak.

Catatan rilis memuat **What's New & Fixes**, dibandingkan dengan rilis sebelumnya dari root manager yang sama. Di halaman **Summary** run, **satu Teks Telegram siap salin** tersedia untuk seluruh rilis (KernelSU Next dan BakaSU dalam satu teks) dalam Bahasa Indonesia dan English, masing-masing dalam kotak kode dengan tombol salin. Perubahan dari pengembang root manager dan SUSFS ditulis dengan kata-kata biasa (mis. "memperbaiki penyembunyian SELinux"), tanpa kode commit. Centang **teks_saja** bila hanya ingin membuat catatan dan teks Telegram, termasuk untuk versi yang sudah terbit; mode ini tidak menerbitkan atau mengubah rilis.

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

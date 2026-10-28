# Checkpoint — 28 Okt 2026, 09.21 WIB

Owner meminta checkpoint: hentikan pekerjaan dan simpan keadaan terakhir. Sesi berikutnya membaca file ini serta CLAUDE.md, lalu menunggu instruksi owner. Jangan otomatis menjalankan workflow, login, build, atau pemeriksaan tugas lama.

File ini memakai nama checkpoint.md sesuai permintaan owner. CHECKPOINT.md tetap menjadi pintu masuk dan menaut ke file ini.

## Keadaan terakhir

- Semua perubahan README yang diminta dalam sesi ini sudah digabung dan diverifikasi pada branch tujuan.
- Tidak ada tugas README yang masih menunggu dikerjakan.
- **Cogan Smart Kernel v2.9.1 sudah rilis:** [halaman rilis](https://github.com/cogan17/Cogan-Kernel/releases/tag/cogan-smart-v2.9.1). Status dan kedua aset sudah dikonfirmasi lewat API GitHub saat pembaruan checkpoint.
- Setelah permintaan checkpoint, pekerjaan dibatasi pada penyimpanan catatan ini lewat PR dan validasi otomatisnya.

## Repository dan commit acuan

| Repository | Branch tujuan | Commit terakhir yang diverifikasi sebelum checkpoint |
|---|---|---|
| cogan17/Cogan-Kernel | main | 8761a7ae3ede3af385498cb1a9330184446c2149 |
| cogan17/TWRP-14T-PRO | twrp-14.1_a16 | 5f84b90f26f02c553049904ecf07f918c42a1a72 |

Repository kernel dahulu bernama Xiomi_14T_Pro. Gunakan URL Cogan-Kernel untuk pekerjaan berikutnya.

## Selesai: README Cogan-Kernel

README.md dan README.en.md sudah sesuai permintaan owner:

1. PR [#60](https://github.com/cogan17/Cogan-Kernel/pull/60), merge e44f0b69a70edda088987d1d3c3ae13bbdfdd276: ganti peringatan lama dengan tanggung jawab pengguna atas bootloop/brick dan pengingat mencadangkan data.
2. PR [#61](https://github.com/cogan17/Cogan-Kernel/pull/61), merge 8761a7ae3ede3af385498cb1a9330184446c2149: pisahkan informasi ketersediaan TWRP dari Warning ke Tip.

Susunan akhir versi Indonesia:

> [!WARNING]
> Jika terjadi bootloop atau brick, bukan tanggung jawab maintainer/developer. Pemilik device bertanggung jawab atas devicenya sendiri! Harap cadangkan datamu.

> [!TIP]
> TWRP sudah tersedia untuk Xiaomi 14T Pro. Kamu bisa mendownload [TWRP](https://github.com/cogan17/TWRP-14T-PRO).

Versi Inggris memiliki susunan dan arti yang sama. Informasi unduhan TWRP berada di Tip. Tulisan TWRP langsung membuka repository tujuan; URL panjang tidak ditampilkan sebagai teks tautan.

Validasi GitHub lolos untuk PR #60 ([40614410378](https://github.com/cogan17/Cogan-Kernel/actions/runs/40614410378)) dan PR #61 ([40616637499](https://github.com/cogan17/Cogan-Kernel/actions/runs/40616637499)). Isi kedua README pada main sudah dibaca ulang dan cocok dengan perubahan yang dimaksud.

## Selesai: README TWRP-14T-PRO

README.md dan README.en.md sudah diperbarui pada twrp-14.1_a16:

1. PR [#60](https://github.com/cogan17/TWRP-14T-PRO/pull/60), merge b9ac06baf87989732d1302151c8c0d960e155682: tambahkan Caution khusus penggunaan recovery, dengan kata-kata berbeda dari peringatan kernel.
2. PR [#61](https://github.com/cogan17/TWRP-14T-PRO/pull/61), merge 5f84b90f26f02c553049904ecf07f918c42a1a72: tambahkan Tip tentang kernel yang terintegrasi SUSFS.

Caution Indonesia:

> [!CAUTION]
> **Kenali risikonya sebelum menggunakan recovery.** Kesalahan saat flashing, wipe, atau restore dapat menyebabkan kehilangan data hingga perangkat tidak dapat digunakan. Simpan cadangan data penting di luar perangkat dan pelajari [cara kembali ke stok](https://github.com/cogan17/TWRP-14T-PRO/blob/twrp-14.1_a16/docs/kembali-ke-stok.md). Keputusan menjalankan setiap tindakan di TWRP ada di tanganmu; maintainer/developer tidak menanggung kerusakan atau kehilangan data yang timbul.

Tip Indonesia:

> [!TIP]
> Sudah tersedia kernel patch yang terintegrasi dengan **SUSFS** dan beberapa fitur lainnya. [Cek di sini](https://github.com/cogan17/Cogan-Kernel).

Versi Inggris sudah ditambahkan. Tautan kembali ke stok pada setiap README memakai panduan dalam bahasa yang sesuai. Kedua README pada branch tujuan sudah diverifikasi setelah merge. Tidak menjalankan build atau publikasi TWRP untuk perubahan dokumentasi ini.

## Selesai: rilis Cogan Smart Kernel v2.9.1

- Rilis: [Cogan Smart Kernel v2.9.1](https://github.com/cogan17/Cogan-Kernel/releases/tag/cogan-smart-v2.9.1).
- Tag: cogan-smart-v2.9.1.
- Terbit: 27 Okt 2026, 01.32 WIB.
- Jenis GitHub: Release (draft=false, prerelease=false).
- Target commit: 30405b3155682c041b192ff34afa322644ff7298.
- ZIP dan catatan rilis tersedia; ukuran serta SHA256 keduanya cocok dengan paket yang disiapkan.

Persiapan sudah selesai melalui PR [#58](https://github.com/cogan17/Cogan-Kernel/pull/58), merge 30405b3155682c041b192ff34afa322644ff7298. Jangan mengulang pengemasan atau tes yang sudah lolos.

- Modul: id=cogan_smart, version=v2.9.1, versionCode=18.
- Sumber paket: commit 8362b2b6bfbcef86de65867374a4bd238f2b70ad.
- ZIP: modules/cogan-smart/rilis/v2.9.1/Cogan-Smart-Kernel-v2.9.1.zip, 124815 byte, 35 berkas.
- SHA256 ZIP: 64631a42c9133c2d91568ceb88c9582f5c5a95b1b6535c64cb27551fb502e29c.
- Catatan: modules/cogan-smart/rilis/v2.9.1/Cogan-Smart-v2.9.1-Whats-New-and-Fixes.txt, 13312 byte.
- SHA256 catatan: 3ab756c9ea0c2594dcc5be74ec0113cfe493f558cf0bc17bb0e95e3eda37a396.
- README modul sudah memuat paket dan catatan v2.9.1.
- [Validate 40371370105](https://github.com/cogan17/Cogan-Kernel/actions/runs/40371370105): 218 tes lolos, YAML dan sintaks shell lolos.
- Integritas ZIP, kesesuaian isi dengan sumber, izin berkas, dan langkah pemeriksaan paket dari workflow sudah lolos.
- Status rilis GitHub sudah dikonfirmasi. Pengukuran optimasi terakhir di HP tidak ditinjau ulang dalam pembaruan checkpoint ini; catat bukti uji fisik berdasarkan laporan owner.

Owner memberikan tautan rilis pada 28 Okt 2026. Pemeriksaan API GitHub mengonfirmasi rilis telah terbit pada waktu di atas dan kedua aset sesuai. Publikasi v2.9.1 selesai; tidak ada langkah penerbitan ulang. Hambatan login pada upaya lama tidak lagi menjadi tugas tertunda.

## Aturan yang perlu dipertahankan

- Identitas commit: Cogan <79615344+cogan17@users.noreply.github.com>; tanpa atribusi AI.
- Perubahan Cogan-Kernel masuk ke main lewat PR. Ikuti CLAUDE.md.
- Waktu untuk owner memakai WIB. Komunikasi utama Bahasa Indonesia; README Indonesia dan Inggris tetap selaras.
- Flash dan uji pada HP adalah keputusan owner. Bedakan bukti lokal, CI dan uji fisik.
- Hemat workflow: tidak menambah trigger/jadwal, tidak mengulang build atau tes hijau tanpa alasan baru, dan investigasi kegagalan sebelum retry.
- Tidak mengubah status rilis kernel/modul hanya karena teks Warning diperbarui.
- Workspace lokal lama dapat tertinggal dari remote dan pernah berisi paket v2.9.1 yang sudah digabung. Periksa status sebelum memakai checkout lama; jangan menimpa perubahan lokal.

## Catatan historis

[Checkpoint 26 Okt 2026](https://github.com/cogan17/Cogan-Kernel/blob/8761a7ae3ede3af385498cb1a9330184446c2149/CHECKPOINT.md) tetap tersedia dalam riwayat git. Di dalamnya ada catatan ambang bawaan 40 °C, konfirmasi dua kotak Teks Telegram, dan bukti run satu build/Catat sublevel. Status butir lama tersebut tidak diperiksa ulang dalam sesi ini. Instruksi lama untuk menyiapkan folder rilis v2.9.1 sudah terlewati oleh PR #58.

## Langkah pertama sesi berikutnya

Baca checkpoint.md dan CLAUDE.md, lalu tunggu permintaan owner. Semua tugas README yang diminta selesai dan rilis v2.9.1 sudah dikonfirmasi. Tidak ada pekerjaan baru yang perlu dimulai hanya karena checkpoint ini dibaca.

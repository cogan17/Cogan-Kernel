# Checkpoint — 28 Okt 2026, 09.19 WIB

Owner meminta checkpoint: hentikan pekerjaan dan simpan keadaan terakhir. Sesi berikutnya membaca file ini serta CLAUDE.md, lalu menunggu instruksi owner. Jangan otomatis melanjutkan publikasi, login, build, atau pemeriksaan tugas lama.

File ini memakai nama checkpoint.md sesuai permintaan owner. CHECKPOINT.md tetap menjadi pintu masuk dan menaut ke file ini.

## Keadaan terakhir

- Semua perubahan README yang diminta dalam sesi ini sudah digabung dan diverifikasi pada branch tujuan.
- Tidak ada tugas README yang masih menunggu dikerjakan.
- Publikasi Cogan Smart Kernel v2.9.1 belum berhasil diselesaikan dari sesi ini. Status rilis publik belum diperiksa ulang saat checkpoint; jangan menyatakan pasti belum ada rilis tanpa pemeriksaan baru.
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

## Tertunda: publikasi Cogan Smart Kernel v2.9.1

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
- Pengukuran di HP untuk optimasi terakhir belum dibuktikan; jangan memberi label seluruh perubahan sudah diuji di HP.

Publikasi terhambat autentikasi browser. Browser terakhir berada di login Google untuk GitHub; upaya autentikasi dan pemeriksaan berikutnya terputus/dibatalkan. Tidak ada workflow publikasi baru yang berhasil dijalankan oleh sesi ini. Konektor GitHub dapat membaca, mengubah berkas, membuat PR, dan merge; saat upaya publikasi itu, tool dispatch workflow baru atau create release tidak tersedia.

Jika owner nanti meminta melanjutkan publikasi:

1. Periksa dahulu apakah release/tag cogan-smart-v2.9.1 sudah ada. Jika sudah ada, verifikasi aset dan jangan menerbitkan duplikat.
2. Jika belum ada dan akses tersedia, jalankan workflow [Cogan Smart Release](https://github.com/cogan17/Cogan-Kernel/actions/workflows/cogan-smart-release.yml) sekali pada main, dengan input berikut:

| Input | Nilai |
|---|---|
| versi | v2.9.1 |
| aksi | Terbitkan |
| release_type | Pre-release |
| kernel_uji | Biarkan bawaan; tidak dipakai untuk penerbitan |

3. Tag yang diharapkan: cogan-smart-v2.9.1. Judul: Cogan Smart Kernel v2.9.1. Aset harus cocok dengan nama, ukuran dan SHA256 di atas.
4. Jangan rerun run gagal 40368437802 atau 40368120654: input versi lamanya memakai tag lengkap dan salah. Input versi hanya v2.9.1.
5. Jika akses tetap terblokir, jelaskan hambatannya segera. Jangan mengulang proses login yang macet atau meminta rahasia lewat chat.

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

Baca checkpoint.md dan CLAUDE.md, lalu tunggu permintaan owner. Semua tugas README yang diminta sudah selesai. Jangan melanjutkan publikasi v2.9.1 atau pekerjaan historis hanya karena checkpoint ini dibaca.

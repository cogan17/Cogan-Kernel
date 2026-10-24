# Aturan untuk asisten AI di repo ini

Repo ini lanjutan dari [cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro) (owner, 23 Okt 2026). Riwayat pengembangan, keputusan lama (D-001 … D-031) dan sumber BSP Xiaomi tetap di repo itu.

## Tanpa atribusi AI

- Author dan committer memakai identitas owner: `git config user.name Cogan` dan `git config user.email 79615344+cogan17@users.noreply.github.com`.
- Pesan commit **tanpa** `Co-Authored-By: Claude …`, `Claude-Session: …` atau atribusi AI lain.
- Deskripsi PR **tanpa** footer "Generated with Claude Code" atau tautan sesi.
- Branch kerja memakai nama biasa: `feat/…`, `fix/…`, `docs/…`, `chore/…`. Perubahan masuk ke `main` lewat PR.

## Waktu

- Waktu untuk owner selalu ditulis dalam **WIB** (Jakarta, UTC+7), misalnya "17.29 WIB". Kalau sumbernya UTC (GitHub, log), ubah dulu ke WIB.

## Isi repo (owner, 23 Okt 2026)

- **Satu branch `main`**: README simpel (ID + EN), dokumen, workflow, mesin build, modul Cogan Smart Kernel.
- **Kernel hanya dari ACK** (Android Common Kernel `android14-6.1`). GKID tidak dipakai.
- **Root manager dua**: KernelSU Next dan BakaSU, masing-masing dengan SUSFS, versi kernel dan manager selalu sama.
- **Tidak ada sistem kunci, lock atau freeze.** Setiap build memakai versi terbaru (rilis ACK, root manager, SUSFS, NoMount, BBG, AnyKernel3). Bila yang terbaru belum cocok, build berhenti dan summary menyebut siapa yang ditunggu, misalnya "Tunggu simonpunk memperbarui SUSFS" atau "Tunggu pengembang BakaSU membuka blokir SUSFS". Jangan membuat pin, mirror, atau tree beku untuk menghindarinya.
- **Gate KMI tetap** dan tidak termasuk "kunci": ia melindungi HP dari modul vendor yang tidak cocok.
- **Fitur dari WildKernel** masuk satu per satu sebagai centang yang mati secara default, dipasang ketat, lewat gate KMI, dan diuji HP sebelum dirilis (owner 24 Okt 2026). Sejauh ini: Unicode fix (patch terbaru `WildKernels/kernel_patches`; terbukti di ACK 6.1.138 (lokal) dan 6.1.176 (CI), rilis ACK lain diharapkan cocok dan build berhenti bila tidak). Ptrace (hanya kernel < 5.16), BTF (sudah aktif di kernel bawaan) dan FUSE-BPF (6.12) tidak berlaku untuk rothko.
- **Summary workflow selalu dua bahasa** (Indonesia, lalu English) dan menampilkan yang berhasil maupun yang gagal, ringkas seperti README (owner 24 Okt 2026). Builder: satu tabel hasil di akhir run (`kernel/run_summary.py`); dengan satu build, plus **Teks Telegram** ID/EN dalam kotak kode siap salin (`kernel/telegram.py`: Baru diukur dari rilis sebelumnya, Perbaikan dari commit `fix(kernel…)`). Rilis dari run menampilkan teks yang sama untuk rilis yang terbit.
- **Workflow ditulis sederhana**, tampilannya terinspirasi WildKernel. Cara kerja GKI WildKernel tidak disalin, dan workflow repo lama tidak disalin begitu saja.
- **Rilis lama** (r5, r6, r8, Cogan Smart v2.8.1/v2.8.2) disalin dari repo pendahulu sebagai arsip, dengan file dan SHA256 yang sama. Kernel arsip bernama **arsip r5, arsip r6, arsip r8** dengan tag berawalan `arsip-` (mis. `arsip-v26.10.22-r5`; owner 24 Okt 2026), supaya nomor rN repo ini tidak bentrok. Jangan memakai nama atau tag tanpa awalan itu untuk arsip.

## Pelajaran yang tetap berlaku

- **Paket harus mengikuti struktur stok.** ZIP kernel hanya mengganti kernel di partisi `boot` (AnyKernel3 `split_boot` + `flash_boot`: header dan ramdisk HP tetap, `device.name1=rothko`). Jangan menyentuh `vendor_boot`, `init_boot`, `vbmeta` atau `dtbo`.
- **Diagnosa dengan bukti, bukan keyakinan.** Bandingkan artefak yang berhasil dengan yang rusak sebelum mengubah kode. Tulis jelas mana yang terukur lokal, mana yang sudah dibuktikan CI, dan mana yang sudah dibuktikan di HP.
- **Gate gagal, bukan lolos diam-diam.** Gate KMI dan patch yang tidak bisa dipasang menghentikan build. Jangan pernah mengubahnya jadi peringatan.
- **Jalur darurat tetap aman.** Tidak pernah wipe data, tidak pernah `flash_all_lock`. Bootloop dipulihkan lewat TWRP atau `boot` stok ([kembali ke stok](docs/kembali-ke-stok.md)). Flash selalu keputusan owner.
- **Setiap versi punya rilis sendiri dan tidak dihapus.** Artifact Actions hanya bertahan 7 hari. Changelog ID dan EN memakai versi yang sama.
- **Instruksi yang bisa dibaca dua arah: tanya dulu.**

## Hemat run workflow (owner, 23 Okt 2026)

- **Jangan boros Actions.** Jalankan workflow hanya bila sudah yakin hasilnya akan benar: kode sudah dicek lokal (tes, lint, uji dengan repo hulu sungguhan bila bisa).
- **Gagal = investigasi dulu, bukan coba-coba.** Baca log, temukan penyebabnya, perbaiki sekali dengan benar, baru jalankan ulang. Jangan berputar-putar dengan run berulang.
- **Investigasi secukupnya.** Jangan terlalu lama; cari bukti yang menentukan, lalu putuskan.
- **Cepat bukan berarti teledor.** Kerjakan dengan bijaksana.

## Uji sublevel: bukti compile, bukan satu per satu di HP

- Owner **tidak** menguji sublevel satu per satu di HP. Jangan pernah meminta owner mem-flash sublevel hanya untuk mengecek kompatibilitasnya.
- Kompatibilitas dibuktikan di CI. Claude boleh menjalankan build tanpa rilis, karena tidak membuat rilis dan tidak menyentuh HP.
- **Uji HP hanya untuk build yang akan dirilis**, satu build saja. Label "diuji di HP" hanya untuk build yang benar-benar diuji owner.

## Checkpoint

- Bila owner menulis **checkpoint**: hentikan semua pekerjaan saat itu juga, tanpa mengecek apa pun satu per satu.
- Simpan keadaan terakhir ke [`CHECKPOINT.md`](CHECKPOINT.md): apa yang sedang berjalan, apa yang sudah selesai, apa yang tertunda, dan langkah pertama berikutnya. Commit dan push ke `main` lewat PR.
- Sesi berikutnya **mulai dari `CHECKPOINT.md`**, lalu lanjut hanya setelah owner meminta.

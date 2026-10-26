# Aturan untuk asisten AI di repo ini

Repo ini lanjutan dari [cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro) (owner, 23 Okt 2026). Riwayat pengembangan, keputusan lama (D-001 … D-031) dan sumber BSP Xiaomi tetap di repo itu.

Nama repo **`cogan17/Cogan-Kernel`** sejak 24 Okt 2026 (owner; sebelumnya `cogan17/Xiomi_14T_Pro`). GitHub mengalihkan tautan lama, asalkan nama lama tidak dipakai repo baru. Tanda tangan build sebelum ganti nama (r1, r2) tetap menyebut `Xiomi_14T_Pro`; build sesudahnya menyebut `Cogan-Kernel`.

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
- **Root manager dua**: KernelSU Next dan BakaSU, masing-masing dengan SUSFS, versi kernel dan manager selalu sama. BakaSU diambil dari rilis terbarunya; selama rilis itu belum cocok dengan SUSFS terbaru, dari commit `main` terbaru yang sudah punya build CI manager resmi (owner 24 Okt 2026, Baka-SU/BakaSU#214). Kernel dan manager selalu dari commit yang sama.
- **Tidak ada sistem kunci, lock atau freeze.** Setiap build memakai versi terbaru (rilis ACK, root manager, SUSFS, NoMount, BBG, AnyKernel3). Bila yang terbaru belum cocok, build berhenti dan summary menyebut siapa yang ditunggu, misalnya "Tunggu simonpunk memperbarui SUSFS" atau "Tunggu pengembang BakaSU membuka blokir SUSFS". Jangan membuat pin, mirror, atau tree beku untuk menghindarinya.
- **Gate KMI tetap** dan tidak termasuk "kunci": ia melindungi HP dari modul vendor yang tidak cocok.
- **SUSFS di rilis ACK lama** (owner 24 Okt 2026): patch SUSFS terbaru ditulis untuk ACK terbaru. Baris yang hanya menjadi patokan konteks dan belum ada di ACK lama dibuang dari konteks oleh `kernel/scripts/susfs_context.py` (sejauh ini `#include <trace/hooks/blk.h>` di `fs/namespace.c`, ada sejak 6.1.157; perlu untuk 138 dan 145; terbukti CI run 40061712549: 138 `2025-06_r17` dan 145 `2025-09_r36` lolos build + gate KMI, CRC beda 0). Isi SUSFS tidak diubah dan tetap versi terbaru, jadi ini bukan pin. Ketidakcocokan lain tetap berhenti "Tunggu simonpunk". Baris baru masuk daftar hanya bila terbukti sekadar konteks.
- **Satu cek, satu pencatat** (owner 26 Okt 2026, "ganda cek"): versi terbaru, termasuk rilis ACK baru, hanya dicek oleh *Cek pembaruan*. Workflow *Catat sublevel* (dulu *Cek sublevel baru*) hanya mencatat hasil run Builder terakhir dari `main` (atau `run_id`) di `kernel/sublevels.json` dan tabel README (`kernel/sublevels.py`, langsung di `main`); ia tidak mengecek dan tidak memulai build. Keduanya hanya lewat tombol, tanpa jadwal atau pemicu otomatis (hemat run); jangan menambahkannya. Catatan itu bukan kunci: tidak ada build yang membacanya. Jangan mengedit tabel di antara penanda `sublevel:start/end` dengan tangan.
- **Cek pembaruan hanya mengecek** (owner 26 Okt 2026, "workflow yg bisa Check saja, hanya bisa check"): tombol manual, tanpa jadwal atau pemicu otomatis. `kernel/updates.py` membandingkan versi terbaru setiap komponen (termasuk SUSFS simonpunk dan modul sidex15) dengan build terakhir (snapshot run Builder dari `main`): versi dan tanggal rilis stabil maupun CI, yang baru dan perbaikan, kesiapan BakaSU dan manager CI KernelSU Next, dua bahasa. Ia tidak membangun, tidak menerbitkan dan tidak menulis apa pun; jangan menambahkan aksi lain ke workflow itu.
- **Modul SUSFS ikut di artifact dan rilis, dari dua pengembang** (owner 26 Okt 2026: "SusFS ada 2 pengembang, sidex dan simonpunk"): file 5 `5-SUSFS-MODULE-SIMONPUNK_<versi>_<commit>.zip`, modul resmi simonpunk (`ksu_module_susfs`) dari commit SUSFS yang sama dengan kernel run itu, alat `ksu_susfs` di-compile dengan NDK runner seperti `build_ksu_susfs_tool.sh` (harus arm64); file 6 `6-SUSFS-MODULE-SIDEX15_<versi>.zip`, modul sidex15 dengan WebUI dari build CI terbarunya (`build.yml`, cabang `v1.5.2+`; sidex15 tidak membuat rilis). Pengguna memasang salah satu. Rilis tidak terbit bila salah satu modul gagal; tanpa build CI sidex15 yang masih ada, summary menyebut "Tunggu sidex15".
- **Fitur dari WildKernel** masuk satu per satu sebagai centang yang mati secara default, dipasang ketat, lewat gate KMI, dan diuji HP sebelum dirilis (owner 24 Okt 2026). Sejauh ini: Unicode fix (patch terbaru `WildKernels/kernel_patches`; lolos build + gate KMI di CI pada 6.1.157, 162, 172 dan 176, terpasang bersih di 138 dan 145 (run 40048269498; 138 juga lolos compile lokal); build berhenti bila patch terbaru tidak cocok; diuji bekerja di HP pada r2, 24 Okt). Ptrace (hanya kernel < 5.16), BTF (sudah aktif di kernel bawaan) dan FUSE-BPF (6.12) tidak berlaku untuk rothko.
- **Summary workflow selalu dua bahasa** (Indonesia, lalu English) dan menampilkan yang berhasil maupun yang gagal, ringkas seperti README (owner 24 Okt 2026). Builder: satu tabel hasil di akhir run (`kernel/run_summary.py`); dengan satu build, plus **Teks Telegram** ID/EN dalam kotak kode siap salin (`kernel/telegram.py`: Baru diukur dari rilis sebelumnya, Perbaikan dari commit `fix(kernel…)`). Rilis dari run menampilkan teks yang sama untuk rilis yang terbit.
- **Workflow ditulis sederhana**, tampilannya terinspirasi WildKernel. Cara kerja GKI WildKernel tidak disalin, dan workflow repo lama tidak disalin begitu saja.
- **Isi tiap bahasa harus sesuai bahasanya** (owner 26 Okt 2026): bagian English pada catatan rilis dan teks Telegram tidak boleh menyalin judul commit Indonesia. Commit `fix(kernel…)` baru menyertakan trailer `Release-Fix-EN: <ringkasan dalam English>`; `Release-Fix-ID:` opsional untuk judul yang bukan Indonesia. Terjemahan empat commit lama ada di `kernel/telegram.py`. Catatan owner memakai kolom Indonesia dan English terpisah. Bila terjemahan commit belum tersedia, tampilkan rujukan sumber dengan keterangan English, jangan salin teks Indonesia atau mengarang terjemahan.
- **Rilis lama** (r5, r6, r8, Cogan Smart v2.8.1/v2.8.2) disalin dari repo pendahulu sebagai arsip, dengan file dan SHA256 yang sama. Kernel arsip bernama **arsip r5, arsip r6, arsip r8** dengan tag berawalan `arsip-` (mis. `arsip-v26.10.22-r5`; owner 24 Okt 2026), supaya nomor rN repo ini tidak bentrok. Jangan memakai nama atau tag tanpa awalan itu untuk arsip.

## Pelajaran yang tetap berlaku

- **Paket harus mengikuti struktur stok.** ZIP kernel hanya mengganti kernel di partisi `boot` (AnyKernel3 `split_boot` + `flash_boot`: header dan ramdisk HP tetap, `device.name1=rothko`). Jangan menyentuh `vendor_boot`, `init_boot`, `vbmeta` atau `dtbo`.
- **Diagnosa dengan bukti, bukan keyakinan.** Bandingkan artefak yang berhasil dengan yang rusak sebelum mengubah kode. Tulis jelas mana yang terukur lokal, mana yang sudah dibuktikan CI, dan mana yang sudah dibuktikan di HP.
- **Gate gagal, bukan lolos diam-diam.** Gate KMI dan patch yang tidak bisa dipasang menghentikan build. Jangan pernah mengubahnya jadi peringatan.
- **Jalur darurat tetap aman.** Tidak pernah wipe data, tidak pernah `flash_all_lock`. Bootloop dipulihkan lewat TWRP atau `boot` stok ([kembali ke stok](docs/kembali-ke-stok.md)). Flash selalu keputusan owner.
- **Setiap versi punya rilis sendiri dan tidak dihapus.** Artifact Actions bertahan 90 hari (batas GitHub untuk repo publik, owner 24 Okt 2026); yang permanen hanya file rilis. Changelog ID dan EN memakai versi yang sama.
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

# Checkpoint — 28 Okt 2026, 14.46 WIB

Owner meminta checkpoint. Semua pekerjaan fitur dihentikan; sesi ini hanya menyimpan keadaan terakhir lewat PR ke main dan menunggu validasi otomatis PR tersebut. Sesi berikutnya membaca file ini serta CLAUDE.md, lalu menunggu instruksi owner. Jangan otomatis menjalankan build, menerbitkan Release, login, atau mengulang pemeriksaan tugas lama.

File utama memakai nama checkpoint.md sesuai permintaan owner. CHECKPOINT.md menjadi pintu masuk yang menaut ke file ini.

## Keadaan terakhir

- Tab Manager dan pembaruan modul Cogan Smart v2.10.0 sampai v2.10.3 sudah digabung ke main. Tidak ada PR fitur sesi ini yang masih menunggu merge.
- Paket uji terbaru: **v2.10.3, versionCode 22**, perbaikan kontrol RAM. [Unduh ZIP](https://raw.githubusercontent.com/cogan17/Cogan-Kernel/8cc3ad372dcb7e5c8d243b1304a2a6945eee0701/modules/cogan-smart/rilis/v2.10.3/Cogan-Smart-Kernel-v2.10.3.zip).
- Commit acuan sebelum checkpoint: **8cc3ad372dcb7e5c8d243b1304a2a6945eee0701**, hasil PR [#66](https://github.com/cogan17/Cogan-Kernel/pull/66). Tree yang diuji, diunggah dan digabung sama: c077766909edfc8662e866bd6262b523005b5fcd.
- [Validate 40651289311](https://github.com/cogan17/Cogan-Kernel/actions/runs/40651289311): **245 tes lolos**, YAML dan sintaks shell lolos. Tidak membangun kernel.
- Integritas, reproduksibilitas, daftar/isi dan izin file ZIP v2.10.3 sudah diperiksa. Aset dan tree pada main sudah diverifikasi sebelum owner meminta checkpoint; jangan mengulang tanpa alasan baru.
- **v2.10.0–v2.10.3 adalah paket uji di repository, bukan GitHub Release baru.** Semua paket sebelumnya dipertahankan. Rilis publik v2.9.1 tetap seperti pada checkpoint sebelumnya.
- **Belum ada konfirmasi hasil v2.10.3 pada HP owner.** Keberhasilan CI tidak disamakan dengan keberhasilan fitur, tampilan, atau peningkatan performa pada HP.
- Tidak melanjutkan pengembangan atau meminta uji HP hanya karena checkpoint ini dibaca.

## Riwayat perubahan modul sesi ini

| Versi / versionCode | PR dan commit merge | Validate | Perubahan utama |
|---|---|---|---|
| v2.10.0 / 19 | [#63](https://github.com/cogan17/Cogan-Kernel/pull/63), 3341c628eb7779824f5b105209153e8fd1667807 | [40643517647](https://github.com/cogan17/Cogan-Kernel/actions/runs/40643517647), 241 tes | Tab Manager, CPU/RAM, pemindai aplikasi dan pemindahan tombol Daya/Suhu |
| v2.10.1 / 20 | [#64](https://github.com/cogan17/Cogan-Kernel/pull/64), f3934fd14c2f005f31ed8988e7655bc06d0851c4 | [40646876488](https://github.com/cogan17/Cogan-Kernel/actions/runs/40646876488), 242 tes | Perbaikan pengambilan data aplikasi dan pesan error |
| v2.10.2 / 21 | [#65](https://github.com/cogan17/Cogan-Kernel/pull/65), b25f730992b1df50ac97c88541a2d4d724b12fbc | [40647922175](https://github.com/cogan17/Cogan-Kernel/actions/runs/40647922175), 242 tes | Navigasi sejajar pada kelima halaman |
| v2.10.3 / 22 | [#66](https://github.com/cogan17/Cogan-Kernel/pull/66), 8cc3ad372dcb7e5c8d243b1304a2a6945eee0701 | [40651289311](https://github.com/cogan17/Cogan-Kernel/actions/runs/40651289311), 245 tes | Pisahkan ZRAM/DRAM, tolak BW tanpa dukungan, status RAM dan swap yang sesuai bacaan |

Paket dan catatan ID/EN berada di modules/cogan-smart/rilis/<versi>/; README modul menaut ke keduanya.

| ZIP | Ukuran | SHA256 |
|---|---:|---|
| Cogan-Smart-Kernel-v2.10.0.zip | 139086 byte | 981caad71dfb458c39e0d8283cf37c895caf9990ce3936a4b4c15c55da8d955e |
| Cogan-Smart-Kernel-v2.10.1.zip | 140479 byte | 42281ceab4fac3704f778955d93cdb59e73213ef77ed8e3990a0248de1008de4 |
| Cogan-Smart-Kernel-v2.10.2.zip | 141253 byte | 27286981665a4998fefeb2e88a1a2f84d5c3766ed6b0a1c3e19ea6dfde224e3c |
| Cogan-Smart-Kernel-v2.10.3.zip | 143705 byte, 39 file | d8198a30e3a059318b8049d2f54451aff3fb518f3ff1a7f8e5274af750daa45e |

Catatan terbaru: modules/cogan-smart/rilis/v2.10.3/Cogan-Smart-v2.10.3-Whats-New-and-Fixes.txt.

## Manager: yang sudah dikerjakan

- Empat tab: Daya, Suhu, Manager dan Modul; Tentang tetap tersedia. Navigasi pada kelima halaman memakai satu CSS di webroot/theme.css: ikon di atas, judul satu baris di bawah, tinggi dan area ikon sama. Font besar dapat menggulir navigasi. Tidak ada verifikasi visual melalui WebView/HP untuk paket terakhir.
- Dropdown Prosesor menawarkan default, sugov_ext dan schedutil sesuai dukungan seluruh policy. Penulisan CPU/RAM tetap memerlukan rothko, mt6989 dan Cogan Bridge ABI 1 yang cocok. Nilai SoC bridge menerima mt6989 atau DT compatible mediatek,MT6989.
- Tombol Simpan/Terapkan/Reset/Mulai-Hentikan dari Daya dan Suhu, serta Hapus riwayat suhu, berada di Manager. Formulir tetap di tab semula; hanya kolom yang diedit dibawa sebagai draf localStorage. Simpan log tetap di Suhu.
- client.js memakai nomor callback native bersama agar tiga API Manager tidak saling menimpa. Cache terbaru memakai namespace v2103.
- Tidak menambah daemon, dependensi, jadwal workflow atau pengubahan batas termal. CPU governor tidak dianggap terkunci permanen; pengendali lain masih bisa mengubah nilainya.
- Pemindai aplikasi hanya dijalankan manual, untuk aplikasi user pada pengguna Android aktif. Bukti terakhir dipakai minimal tujuh hari, tanggal instalasi cukup lama, dan tidak sedang berjalan diperlukan; data tidak cukup tidak menjadi saran hapus.
- Pemindai memakai dumpsys usagestats -c, bukan --checkin. Tinjau aplikasi hanya membuka info aplikasi Android; tidak melakukan uninstall/nonaktifkan massal.

## Bug pemindai aplikasi dan hasil perbaikan

Owner mengirim SS v2.10.0 dengan error “Data pemakaian aplikasi belum dapat dibaca.” Audit menemukan dan mereproduksi:

1. Tiga kegagalan pengambilan data disatukan dalam satu error dan stderr dibuang. Dari SS lama, perintah yang gagal di HP tidak dapat dipastikan.
2. dumpsys dapat timeout dan menghasilkan output terpotong sambil keluar dengan kode 0; hasil semacam itu dahulu diterima.
3. Gagal membaca proses dianggap daftar kosong, sehingga aplikasi berjalan bisa masuk saran.

v2.10.1 memperbaiki jalur bersama pengambilan data: menolak kegagalan, timeout/penolakan izin di output dan respons kosong; pembacaan proses wajib berhasil; memilih /system/bin/ps bila tersedia; deadline dumpsys 20 detik dengan batas luar 25 detik. Error menyebut tahap/kode/rincian singkat dan tetap terlihat pada halaman setelah toast hilang. Pemindaian gagal membersihkan hasil lama serta file sementara/lock.

Tes mencakup 16 subkasus kegagalan/timeout/izin/respons kosong pada empat tahap, pengulangan setelah gagal, serta UI agar error tidak hilang. **Owner belum mengirim hasil pemindaian baru yang mengidentifikasi tahap error setelah perbaikan. Jangan mengklaim penyebab perintah awal di HP sudah diketahui atau pemindaian sudah terbukti berhasil di HP.**

## Laporan RAM owner dan solusi v2.10.3

SS 146809.jpg menunjukkan:

- policy0, policy4 dan policy7 terbaca sugov_ext;
- zram0 terpilih lz4;
- UI menyebut bw_hwmon tidak tersedia;
- opsi penerapan CPU/RAM saat boot dicentang.

Versi modul yang terpasang tidak terlihat pada potongan SS tersebut. Bacaan lz4 tidak membuktikan modul yang menggantinya, dan SS lama belum menampilkan apakah swap aktif. SS 146810.jpg berisi analisis asisten lain, bukan pengukuran tambahan; klaim “berhasil diubah ke LZ4” tidak dapat disimpulkan dari SS saja.

Masalah yang diperbaiki: profil lama menggabungkan bw_hwmon + LZ4/ZSTD walaupun bw_hwmon tidak terdeteksi sebagai pilihan yang bisa ditulis pada jalur devfreq yang dibaca modul. Tidak ada dump lengkap driver DRAM HP; jangan menganggap semua MediaTek pasti mendukung atau pasti tidak mendukung governor tertentu.

v2.10.3:

- Pilihan **Kompresi ZRAM**: Ikuti sistem, Snappy & Daily Driver (LZ4), Heavy Multitasker / Space Saver (ZSTD).
- Pilihan **Governor DRAM** terpisah: DRAM Sistem atau bw_hwmon bila tersedia. Memilih kompresor tidak lagi diam-diam menulis devfreq. Permintaan BW yang tidak didukung ditolak sebelum CPU/config berubah.
- Config baru menambah BW=default|bw_hwmon. Config lama tanpa BW mengikuti sistem. API tiga argumen lama tetap diterima; argumen keempat memilih BW. Kepemilikan devfreq lama dipulihkan lewat jurnal ketika mengikuti sistem, tanpa menimpa nilai berbeda dari pengendali lain.
- Status RAM: system, matching, ready, needs_boot, pending_boot, blocked, unsupported, unavailable. matching hanya berarti bacaan sesuai pilihan; UI menjelaskan bahwa nilai itu dapat sudah menjadi bawaan sistem.
- Status swap per ZRAM dibaca terpisah dari /proc/swaps: 1 aktif, 0 tidak aktif, -1 tidak diketahui. File kosong/tidak terbaca tidak dianggap bukti swap tidak aktif.
- Hasil percobaan boot dicatat dalam run/ram_boot_attempted, dibatasi identitas boot dan algoritme. Bila boot belum menghasilkan kompresor yang diminta dan ZRAM sudah diinisialisasi, status blocked menjelaskan keterbatasan; tidak menyuruh restart berulang tanpa hasil.
- ZRAM aktif tetap tidak di-reset, tidak swapoff, tidak mkswap dan tidak diubah ukuran. Tidak menebak OPP/tegangan/node DRAM MediaTek dan tidak menambahkan driver kernel baru.

Solusi yang sudah disampaikan untuk kondisi SS: **DRAM Sistem + LZ4**. Restart tidak menambahkan governor yang tidak disediakan driver. Kompresor ZRAM Linux 6.1 tidak dapat diganti setelah inisialisasi; percobaan boot bersifat best effort. Bila ZSTD tetap blocked, diperlukan integrasi init/kernel yang sesuai atau mengikuti algoritme aktif. Ini bukan klaim bahwa dukungan driver atau timing init sudah diperbaiki pada HP.

Rujukan primer:
- [ZRAM Linux 6.1](https://www.kernel.org/doc/html/v6.1/admin-guide/blockdev/zram.html).
- [Devfreq dan dukungan driver/governor](https://www.kernel.org/doc/html/latest/driver-api/devfreq.html).

## Validasi dan batas bukti

- v2.10.3: 14 tes Manager dan 2 tes WebUI lolos lokal; 245 tes seluruh suite, YAML dan shell lolos di CI. Pemeriksaan mencakup kontrol terpisah, migrasi config, penolakan BW tanpa perubahan kontrol lain, status boot, status swap, pesan UI dan regresi pemindai.
- Pada pemeriksaan suite lokal sebelumnya, delapan kasus deteksi proses/PID gagal juga pada baseline bersih (6 failures, 2 errors). Kasus yang sama lolos pada GitHub Validate. Tidak mengendurkan pemeriksaan PID atau gate agar hijau.
- Paket v2.10.3: 39 file; skrip dan update-binary 0755, lainnya 0644; isi cocok dengan sumber, path aman dan build ZIP reproduktif. README dan rilis/ tidak ikut ZIP.
- **Belum ada hasil uji HP v2.10.3**, pengukuran RAM/performa, keberhasilan ZSTD pada boot owner, atau konfirmasi pemindai aplikasi setelah v2.10.1.
- Tidak mengubah kernel, root manager, SUSFS, KMI, batas termal atau firmware untuk memperbaiki UI/RAM modul ini. Tidak menjalankan Builder atau menerbitkan rilis kernel/modul pada rangkaian pembaruan Manager.

## Pekerjaan sebelumnya tetap selesai

[Checkpoint 09.21 WIB](https://github.com/cogan17/Cogan-Kernel/blob/25c6fe84e6c3e10e42644c93aaecf45a206b8384/checkpoint.md) menyimpan rincian README kernel/TWRP dan rilis v2.9.1. Status tersebut tidak diperiksa ulang ketika owner meminta checkpoint ini:

- README kernel: Warning tanggung jawab pengguna dan cadangan data; informasi [TWRP](https://github.com/cogan17/TWRP-14T-PRO) berada pada Tip terpisah, ID/EN (PR #60/#61).
- TWRP-14T-PRO branch twrp-14.1_a16: Caution khusus recovery dan Tip menuju Cogan-Kernel (PR #60/#61; commit terakhir yang diverifikasi pada sesi itu 5f84b90f26f02c553049904ecf07f918c42a1a72).
- [Cogan Smart v2.9.1](https://github.com/cogan17/Cogan-Kernel/releases/tag/cogan-smart-v2.9.1) sudah Release publik (bukan draft/pre-release), terbit 27 Okt 2026 01.32 WIB. Target 30405b3155682c041b192ff34afa322644ff7298; ZIP 124815 byte, SHA256 64631a42c9133c2d91568ceb88c9582f5c5a95b1b6535c64cb27551fb502e29c. Tidak perlu mengemas atau menerbitkannya lagi.
- Upaya login/token/GitHub App lama bukan pekerjaan tertunda. Jangan mengulang putaran autentikasi tersebut.

## Workspace dan cara melanjutkan

- Checkout aktif perubahan RAM: /workspace/scratch/0b17408b3d47/Cogan-Kernel-ram. HEAD lokal masih base b25f730992b1df50ac97c88541a2d4d724b12fbc, dengan hasil PR #66 di staging; tree sama dengan main sebelum checkpoint. Commit/merge remote dilakukan melalui connector GitHub, bukan git push lokal.
- Checkout lain Cogan-Kernel-manager, Cogan-Kernel-manager-fix dan Cogan-Kernel-tabs juga dapat memiliki perubahan staging yang sudah digabung remote. Jangan langsung meng-commit ulang, reset, atau menimpa checkout lama.
- Checkout Cogan-Kernel lebih lama pernah berisi perubahan v2.9.1 yang sudah selesai. Gunakan main remote terbaru dan periksa status ketika pekerjaan baru memang diminta.
- Gunakan konektor GitHub untuk read/write/PR. Tidak perlu browser/login untuk operasi yang sudah didukung. Untuk ZIP, unggah sebagai blob base64 dan pastikan SHA blob serta tree cocok dengan hasil lokal.
- Identitas author/committer Cogan <79615344+cogan17@users.noreply.github.com>, tanpa atribusi AI; branch feat/fix/docs/chore dan perubahan ke main melalui PR.
- Ponytail aktif sesuai permintaan owner: perubahan sederhana, pakai fungsi/pola yang tersedia, tanpa dependensi baru. Jangan menghapus validasi atau pengamanan. Tidak memakai subagen.
- Hemat Actions, pertahankan seluruh aset lama, bedakan bukti lokal/CI/HP dan ikuti CLAUDE.md. Tidak menjalankan pemeriksaan hijau berulang tanpa alasan baru.

## Langkah pertama sesi berikutnya

Baca CHECKPOINT.md, checkpoint.md dan CLAUDE.md, lalu tunggu instruksi owner. Jangan otomatis merilis v2.10.3, memulai port driver, meminta flash/kernel baru, mengubah RAM aktif, atau menyelidiki ulang pekerjaan yang sudah selesai. Jika owner meminta lanjut, gunakan laporan atau instruksi barunya; konfirmasi hasil HP/pesan status terbaru hanya bila diperlukan untuk tugas tersebut.

## English state summary

Manager and v2.10.0–v2.10.3 test packages are merged into main; the latest pre-checkpoint commit is 8cc3ad372dcb7e5c8d243b1304a2a6945eee0701. v2.10.3 (versionCode 22) separates ZRAM compression from optional DRAM governors, rejects unavailable bw_hwmon, migrates old settings through the ownership journal, distinguishes pending/unsuccessful boot attempts and reports swap activity separately. All 245 CI tests pass. No live ZRAM reset or new kernel driver was added, and this update is not phone-tested. The old app-scan failure's exact phone command remains unknown. These are repository test packages, not newly published GitHub Releases; v2.9.1 remains the previously confirmed public release. Work is stopped. Read this checkpoint and CLAUDE.md next session, then wait for the owner.

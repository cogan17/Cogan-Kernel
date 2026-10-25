# Checkpoint — 25 Okt 2026, 15.55 WIB · Cogan Smart v2.9.0 terbit, v2.9.1 dalam uji HP

Sesi berikutnya mulai dari sini. Aturannya ada di `CLAUDE.md`. Semua waktu dalam WIB. Checkpoint sebelumnya (24 Okt 09.55 WIB, r2) ada di riwayat git file ini.

## Sedang berjalan
- Tidak ada run workflow.
- **PR #42** (`feat/cogan-smart-v2.9.1`) terbuka dan **ditahan sampai uji HP owner**. Isi: modul hemat CPU, satu angka Badan HP dari HyperOS, lonjakan suhu, penyebab "Pembaruan aplikasi" dan "HP baru dinyalakan", nama aplikasi asli, batas CPU dan beban modul di log, sensor macet, CSV berkutip. Commit terakhir `608925e`.
- Owner memakai **ZIP uji v2.9.1 hemat CPU** (`ee4008fa…b46d`, isi sampai commit `27f80a7`) sejak restart 12.06 WIB. Perbaikan `608925e` (kecepatan jaringan negatif setelah restart) belum masuk ZIP.

## Sudah selesai (sejak checkpoint 24 Okt)
- **Cogan Smart v2.9.0** (PR #36): mode mengikuti Badan HP 39/41/44 °C, langkah halus, CPU hanya diturunkan saat prosesor bekerja, penyebab panas per bagian, kartu Rem HyperOS (kedipan diperbaiki), kredit dirampingkan.
  - Pre-release [`cogan-smart-v2.9.0`](https://github.com/cogan17/Cogan-Kernel/releases/tag/cogan-smart-v2.9.0), terbit 12.03 WIB lewat Cogan Smart Release (run 40164162891, diserahkan owner ke Claude). ZIP `7d15a729…7522` sama byte per byte dengan `rilis/v2.9.0`. "Latest" tetap kernel r3.
  - Label "diuji di HP + HyperCharge, kernel r2 + r3 (6.1.176)" (run 40164196494). Dasar: log owner, restart 17.37 WIB 24 Okt (6 menit setelah ZIP final dikirim), HyperCharge sampai 9,4 A 19.24–20.05 WIB, r3 sejak 20.40 WIB. Owner belum menyebut sendiri ZIP mana yang terpasang; bila keliru, label diganti.
- **Artifact** disimpan 90 hari (PR #39).
- **BakaSU** dari commit `main` terbaru yang punya build CI manager resmi bila rilisnya belum cocok dengan SUSFS (PR #40, #41; Baka-SU/BakaSU#214). Owner membangun dan menguji di HP: bekerja.
- **v2.9.1, temuan dari log owner:**
  - Beban modul (pencatat + pengendali) build uji pertama: **4,8% CPU** seluruh HP, sama di semua aplikasi dan saat layar mati (log 6 jam, 05.25–11.24 WIB). Penyebab: puluhan proses kecil per putaran.
  - Build hemat CPU (log 3 jam, 12.06–14.49 WIB): **2,9%** (pencatat 1,5%, pengendali 1,4%). Di HP tiruan: pencatat ±94 → ±12 proses per sampel, pengendali 62 → 15 per putaran.
  - Lonjakan suhu yang dijelaskan: Play Store 06.56–06.59 WIB (unduh + pasang, CPU 70–85%), restart setelah pasang modul 07.23–07.28 WIB, Morphe 09.50 WIB.
  - Instagram lebih panas daripada YouTube (log 3 jam dan 6 jam): CPU 52% vs 40%, GPU 24% vs 7%, arus 670 vs 497 mA. YouTube memakai dekoder video perangkat keras; Instagram terus menggambar ulang layar dan memuat banyak video. Bukan karena jaringan atau modul.
  - Saat Instagram, pengendali hanya menurunkan CPU di 4 dari 107 sampel: prosesor rata-rata 56 °C, di bawah syarat CPU_WORK 60 °C.
- Tes lokal: 174 tes lulus (mksh + One True Awk), 97 tes Cogan Smart lulus dengan dash + mawk dan dash + One True Awk. Validate hijau di `27f80a7`; `608925e` belum dicek.

## Tertunda / menunggu owner
1. Lanjutkan pengurangan beban pengendali? Usul: pengendali hanya membaca sensor CPU/GPU dan angka Badan HP HyperOS (±20 dari 60 sensor), tanpa `awk`. Dugaan (belum terukur): sisa beban berasal dari pembacaan ±60 sensor 3 kali per 20 detik dan pengolahan daftar proses.
2. Turunkan syarat "prosesor bekerja" (CPU_WORK) dari 60 ke 55 °C supaya Kernel Default ikut bekerja di beban seperti Instagram?
3. Ambang bawaan 40 °C (data 6 jam: panas 18% → 22% waktu, CPU penuh 91% → 88%). Belum diubah.
4. Hasil uji HP v2.9.1 (nilai "⚙️ Beban Cogan Smart … (pengendali …)" dan CSV) untuk memutuskan merge PR #42.

## Langkah pertama berikutnya
- Baca jawaban owner atas butir 1–3. Kerjakan yang dipilih di `feat/cogan-smart-v2.9.1`, uji lokal (mksh + One True Awk, dash + mawk), kemas ZIP baru (sekaligus membawa `608925e`), kirim ke owner, perbarui PR #42.
- Bila owner menyatakan v2.9.1 baik di HP: merge PR #42, siapkan `modules/cogan-smart/rilis/v2.9.1/` (ZIP + What's New & Fixes ID/EN), lalu Cogan Smart Release (owner menyerahkannya ke Claude).

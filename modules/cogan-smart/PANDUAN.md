# 📖 Panduan Cogan Smart Kernel

[English](PANDUAN.en.md) · [README modul](README.md)

Cogan Smart Kernel menjaga HP tetap adem dan mencatat suhunya. Panduan ini menjelaskan tiap tab dan tombol dengan bahasa sederhana.

## 🚀 Mulai cepat

1. Pilih mode di tab **Daya**: 🌿 Hemat, 🧠 Kernel Default atau 🎮 Performa.
2. Lihat **Ringkasan** di Manager: pengendali dan pencatat harus *aktif* / *mencatat*.
3. HP terasa panas? Buka tab **Suhu**: penyebabnya tercatat di sana.

## 🛠️ Manager: pusat kendali

- **Ringkasan**: suhu Badan HP, baterai, prosesor, status pengendali dan pencatat, grafik suhu 1 jam, penyebab panas, dan hasil pindai modul terakhir (pindai di tab Modul).
- **📱 Aplikasi**: jumlah aplikasi berbahaya dan status blokir APK dari tab Aplikasi.
- **Mode daya**: menampilkan mode yang dipilih di tab Daya. Manager hanya memantau; ganti mode di tab Daya.
- **Prosesor**: cara CPU mengatur kecepatannya (governor). Kernel Default cocok untuk harian.
- **RAM**: kompresi ZRAM. LZ4 lebih cepat, ZSTD lebih hemat RAM. Centang *Terapkan CPU/RAM saat boot*, tekan **Simpan**, lalu restart HP.
- **Kontrol Daya** dan **Kontrol Suhu**: semua tombol untuk menerapkan setelan dari tab Daya dan Suhu.

## 🔘 Arti tombol

- **💾 Simpan**: menyimpan setelan. Berlaku pada pemeriksaan berikutnya.
- **⚡ Paksa / Terapkan** dan **Terapkan sekarang**: menyimpan, menyalakan, lalu langsung berlaku.
- **↺ Reset default / Ikuti kernel**: kembali ke setelan bawaan. Riwayat suhu tidak dihapus.
- **⏹ Hentikan / ▶ Mulai**: mematikan atau menyalakan pengendali atau pencatat.
- **🗑 Hapus riwayat**: menghapus catatan suhu. Log yang sudah disimpan di Download tetap ada.

## ⚡ Daya

- **🌿 Hemat**: CPU besar dibatasi 60%, Badan HP dijaga ≤ 39 °C.
- **🧠 Kernel Default**: Badan HP dijaga ≤ 41 °C. Pilihan harian.
- **🎮 Performa**: tenaga penuh, baru direm saat Badan HP 44 °C.
- **🔌 Cas**: berhenti mengecas di 95% dan lanjut di 90% (bisa diubah). *Cari saklar cas* cukup sekali, saat charger tercolok.
- **⚙️ Setelan mode**: ubah angka suhu tiap mode. Simpan dari Manager.
- **📝 Aktivitas**: catatan apa saja yang dilakukan modul.

## 🌡️ Suhu

- **Sekarang**: suhu Badan HP dan bagian HP lain saat ini.
- **📊 Ringkasan**: grafik, berapa lama HP panas, penyebab panas, dan suhu per aplikasi dan per mode.
- **💾 Simpan log**: menyimpan ringkasan (.txt) dan semua data (.csv) ke folder *Download/CoganThermal*.
- **⚙️ Setelan**: kapan HP dianggap panas (bawaan 41 °C), lama riwayat (7 hari) dan notifikasi (bawaan mati).

## 🧩 Modul

- Memeriksa modul root lain: ✅ aman, ⚠️ perlu dicek, ⛔ berbahaya. Ini dugaan; baca *Bukti* sebelum bertindak.
- **🛡️ Percaya**: modul tidak ditandai lagi dan terlindung dari hapus tidak sengaja.
- **⏸ Nonaktifkan / ▶ Aktifkan**: berlaku setelah reboot.
- **🗑 Hapus sampai akar**: menghapus modul beserta skrip boot dan prosesnya. Bisa dibatalkan sebelum reboot.
- **📜 Skrip boot di luar modul**: skrip yang jalan saat boot tapi tidak terlihat di daftar modul.

## 📱 Aplikasi

- Memeriksa semua aplikasi yang kamu pasang: ✅ aman, ⚠️ perlu dicek, ⛔ berbahaya. Tandanya dari sumber pasang dan izin aplikasi, bukan antivirus.
- **Sumber**: dari toko aplikasi, file APK kiriman chat atau sosmed, atau file APK dari browser dan file manager. APK kiriman WhatsApp atau sosmed paling sering dipakai penipuan.
- **Izin berbahaya**: baca SMS (kode OTP), aksesibilitas (bisa membaca dan menekan layar), admin perangkat (sulit dihapus), baca notifikasi, tampil di atas aplikasi lain, ikon disembunyikan.
- **👁️ Gerak-gerik**: kapan terakhir aplikasi memakai kamera, mikrofon, lokasi, SMS, kontak, telepon atau clipboard, pemakaian internet 7 hari dan baterai sejak cas penuh.
- **⚠️ Perlu dicek / Semua / 💤 Jarang dipakai**: pilih daftar yang ditampilkan. Jarang dipakai artinya tidak dibuka 7 hari atau lebih.
- **🔍 Cari** (di atas daftar): ketik nama aplikasi atau nama paket. Pencarian mencakup semua aplikasi, apa pun daftar yang dipilih.
- **🛡️ Percaya**: aplikasi tidak ditandai lagi dan tidak bisa terhapus tanpa sengaja.
- **🗑 Hapus sampai akar**: melepas admin perangkat, menghentikan dan menghapus aplikasi dari semua pengguna (termasuk Aplikasi Ganda dan Ruang Kedua), lalu menghapus sisa data dan file APK yang sama di penyimpanan. Tidak bisa dibatalkan. Aplikasi sistem dan root manager tidak bisa dihapus dari sini.
- **🛡️ Blokir APK dari chat & sosmed**: bawaan aktif. Aplikasi chat, sosmed, email dan SMS (WhatsApp, Telegram, Signal, Instagram, Facebook, Threads, TikTok, X, Gmail, Outlook, Pesan dan lainnya) tidak bisa memasang aplikasi. Bila izinnya dinyalakan lagi di Pengaturan, modul mencabutnya dalam beberapa detik dan memberi notifikasi. Browser dan file manager tetap bisa.

## ℹ️ Tentang

- Pilih **bahasa** (ID/EN), **tema** (Otomatis, Terang hangat, Gelap OLED) dan **Mode Dev**.

## 🛠️ Mode Dev

- Bawaan mati: tampilan ringkas untuk pemakaian sehari-hari.
- Nyala: muncul detail teknis, misalnya node kernel, hasil baca ulang, hook boot ZRAM, semua sensor, dan data mentah modul.

## ❓ Tanya jawab

- **Tidak bisa memasang APK dari WhatsApp atau Telegram?** Itu blokir APK dari tab Aplikasi. Bila kamu yakin APK-nya aman, matikan blokir dulu atau buka file-nya dari file manager.
- **Terlanjur memasang APK penipuan?** Tekan Hapus sampai akar di tab Aplikasi, lalu ganti kata sandi dan PIN bank, dan hubungi bank bila ada transaksi aneh. Menghapus aplikasi tidak membatalkan data yang sudah dicuri.
- **Prosesor 50–60 °C saat santai, wajar?** Ya. Panas dihitung dari suhu Badan HP, yang terasa di tangan.
- **Kolom GPU di log kosong?** GPU sedang tidur (layar mati atau tidak dipakai), jadi sensornya tidak terbaca. Normal.
- **Arus cas sampai 10–16 A?** Itu HyperCharge 120 W saat mengecas cepat. Normal.
- **ZRAM tetap LZ4 setelah restart?** Centang *Terapkan CPU/RAM saat boot*, tekan Simpan, lalu restart. Butuh modul v2.10.8 atau lebih baru.
- **HP gagal masuk sistem?** Safe mode KernelSU mematikan semua modul sementara. Nyalakan lagi di root manager → Modul, lalu reboot.

Halaman yang sama ada di modul: **ℹ️ Tentang → 📖 Panduan**.

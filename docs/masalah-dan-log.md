# 🩺 Masalah & Log

[← Kembali ke README](../README.md) · <img src="https://flagcdn.com/24x18/gb.png" width="22" alt=""> [English](masalah-dan-log.en.md)

Ada kendala? Kumpulkan log di bawah, lalu laporkan di **[Issues](https://github.com/cogan17/Xiomi_14T_Pro/issues)** atau **[Komunitas Telegram](https://t.me/coganTWRP)** beserta versi kernel (`r…`), versi HyperOS, dan apa yang terjadi.

---

## Ambil log

Jalankan di Termux atau terminal root manager (KernelSU Next atau BakaSU):

| Log | Perintah |
|---|---|
| Log kernel sekarang | `su -c dmesg > /sdcard/Download/dmesg.txt` |
| Identitas kernel asli | `su -c cat /sys/kernel/cogan/release /sys/kernel/cogan/features` |
| Log kernel boot gagal sebelumnya (kalau ada) | `su -c 'cat /sys/fs/pstore/console-ramoops* > /sdcard/Download/last_kmsg.txt'` |

Untuk log boot gagal: pulihkan HP dulu ([Kembali ke Stok](kembali-ke-stok.md)), lalu ambil log di atas **sebelum** reboot lagi.

Modul **Cogan Smart Kernel**:

- Tab **🌡️ Suhu** → **Simpan log** (tersimpan di `Download/CoganThermal`).
- Tab **🧩 Modul** → screenshot daftar modul dan penandanya.

## Masalah umum

| Gejala | Penjelasan |
|---|---|
| Versi kernel di Setelan bukan `6.1.138` (mis. `6.1.170`) | Normal: SUSFS menyamarkan `uname`. Identitas asli ada di WebUI Cogan Smart atau `/sys/kernel/cogan/release` |
| Flash berhenti dengan *Unsupported device* | ZIP hanya untuk `rothko`; HP lain ditolak sebelum `boot` disentuh |
| Banyak baris `disagrees about version of symbol` di `dmesg` | Sudah diketahui: modul vendor dimuat lewat *force-load*. Diperbaiki di revisi kernel berikutnya |
| Modul KernelSU mati semua setelah bootloop | Safe mode KernelSU. Nyalakan lagi di aplikasi root manager → Modul, lalu reboot |

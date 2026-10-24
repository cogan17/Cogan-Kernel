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

## Rilis dari run gagal HTTP 403

Jika langkah **Terbitkan / publish** menampilkan `HTTP 403: Resource not accessible by integration`, periksa izin token rilis. `contents: write` saja belum cukup bila commit build lama memiliki file `.github/workflows/` yang berbeda dari `main` saat rilis dibuat. `GITHUB_TOKEN` bawaan tidak bisa diberi izin tambahan untuk kasus ini ([GitHub Docs](https://docs.github.com/en/rest/releases/releases#create-a-release)).

Pengaturan sekali oleh owner:

1. Buka [pembuatan fine-grained token](https://github.com/settings/personal-access-tokens/new). Pilih resource owner **cogan17**, **Only select repositories** → **Xiomi_14T_Pro**, dan masa berlaku sesuai kebutuhan.
2. Pada **Repository permissions**, beri **Contents: Read and write** dan **Workflows: Read and write**. Generate token.
3. Buka [Actions secrets repo](https://github.com/cogan17/Xiomi_14T_Pro/settings/secrets/actions) → **New repository secret**. Nama: `RELEASE_TOKEN`; isi: token tadi. Simpan hanya di secret, jangan di source, issue, atau chat.
4. Setelah perbaikan workflow masuk ke `main`, jalankan **Rilis dari run → Run workflow** dari `main` dengan ID build hijau yang sama. Jangan memilih **Re-run jobs** pada run lama: GitHub memakai workflow dari commit lama untuk rerun.

Untuk kegagalan [run 40052126936](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/40052126936), gunakan `run_id` **40046361218**, **Pre-Release**, serta pilihan uji HP dan catatan yang sama seperti sebelumnya. Kernel tidak perlu dibangun ulang selama artefaknya masih tersedia (7 hari).

Workflow memakai `RELEASE_TOKEN` hanya pada langkah publikasi; langkah baca dan unduh tetap memakai token bawaan. Tanpa secret, token bawaan tetap dipakai dan dapat menerbitkan build yang tidak membutuhkan izin Workflows tambahan. Tag tetap menuju commit build asli, dan rilis yang sudah ada tetap ditolak. Jika secret sudah tersedia tetapi 403 masih terjadi, periksa masa berlaku, pilihan repo dan kedua izinnya.

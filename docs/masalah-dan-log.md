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

**Rilis dari run memakai GitHub App**, sesuai keputusan owner 24 Okt 2026. App membuat token singkat setiap kali owner menekan **Run workflow**; tidak perlu memperbarui PAT berkala. Action resmi GitHub mencabut token saat job selesai. Pendaftaran App dan penyimpanan kredensial di bawah perlu diselesaikan sekali sebelum pemakaian pertama ([GitHub Docs](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/making-authenticated-api-requests-with-a-github-app-in-a-github-actions-workflow)).

### Pengaturan GitHub App sekali

1. Buka [New GitHub App](https://github.com/settings/apps/new) pada akun **cogan17**. Isi **GitHub App name**, misalnya `Cogan17 Rothko Release` (nama harus unik), dan **Homepage URL**: `https://github.com/cogan17/Xiomi_14T_Pro`.
2. Biarkan **Callback URL** kosong, **Request user authorization (OAuth) during installation** dan **Enable Device Flow** tidak dicentang. Pada **Webhook**, lepas centang **Active**: App ini hanya untuk autentikasi rilis, tanpa server atau pemicu otomatis.
3. Pada **Repository permissions**, beri **Contents: Read and write** dan **Workflows: Read and write**. Metadata read-only ikut otomatis. Izin lain tidak diperlukan. Pilih **Only on this account**, lalu **Create GitHub App**.
4. Pada halaman App, salin **Client ID** (bukan App ID atau Client secret). Buka [Actions variables repo](https://github.com/cogan17/Xiomi_14T_Pro/settings/variables/actions) → **New repository variable**:

   | Nama variable | Nilai |
   |---|---|
   | `RELEASE_APP_CLIENT_ID` | Client ID App tadi |

5. Kembali ke halaman App → **Private keys → Generate a private key**. File `.pem` akan diunduh. Buka [Actions secrets repo](https://github.com/cogan17/Xiomi_14T_Pro/settings/secrets/actions) → **New repository secret**:

   | Nama secret | Nilai |
   |---|---|
   | `RELEASE_APP_PRIVATE_KEY` | Seluruh isi file PEM, termasuk baris `BEGIN RSA PRIVATE KEY` dan `END RSA PRIVATE KEY` |

   Private key disimpan di secret GitHub; jangan unggah ke source, issue, atau chat. Client secret OAuth tidak dipakai.
6. Pada pengaturan App, buka **Install App** → **Install** pada akun cogan17 → **Only select repositories** → **Xiomi_14T_Pro** → **Install**. Pendaftaran App saja belum cukup; App harus terpasang di repo.
7. Jalankan **Rilis dari run → Run workflow** terbaru dari `main` dengan ID build hijau. Jangan memilih **Re-run jobs** pada run lama: GitHub memakai workflow dari commit lama untuk rerun.

Untuk kegagalan [run 40052126936](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/40052126936), gunakan `run_id` **40046361218**, **Pre-Release**, serta pilihan uji HP dan catatan yang sama seperti sebelumnya. Kernel tidak perlu dibangun ulang selama artefaknya masih tersedia (7 hari).

Workflow memeriksa kelengkapan variable/secret sebelum mengunduh artefak. Langkah baca dan unduh memakai `GITHUB_TOKEN` read-only; hanya langkah publikasi memakai token App dengan akses khusus repo ini. SHA sumber diambil dari run yang sudah divalidasi, sehingga App tidak membutuhkan izin Actions. Tag tetap menuju commit build asli, dan rilis yang sudah ada tetap ditolak. Secret PAT `RELEASE_TOKEN` dari pengaturan sebelumnya tidak dipakai lagi.

Jika pembuatan token atau publikasi gagal, periksa Client ID, private key aktif, instalasi App pada repo ini, dan izin Contents + Workflows. Bila izin App diubah, setujui pembaruan izin pada instalasinya. Token dibuat ulang otomatis setiap run selama instalasi dan private key tetap aktif. Tahap pendaftaran dan uji rilis sungguhan belum dapat dianggap selesai hanya karena workflow dan tes CI lolos.

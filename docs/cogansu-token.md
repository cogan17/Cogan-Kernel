# 🔑 Token CoganSU (COGANSU_TOKEN)

[← Kembali ke README](../README.md) · <img src="https://flagcdn.com/24x18/gb.png" width="22" alt=""> [English](cogansu-token.en.md)

Dengan token ini, **Cogan Kernel Builder** varian CoganSU jadi **satu langkah**. Kalau rilis CoganSU terbaru belum memuat KernelSU `main` terbaru, atau belum cocok dengan SUSFS, Builder menjalankan **Build CoganSU** di repo `cogan17/CoganSU` sendiri. Build CoganSU menggabung KernelSU terbaru secara otomatis. Builder menunggu sampai selesai, lalu membangun kernel dengan rilis CoganSU yang baru.

Token dibutuhkan karena workflow di satu repo tidak boleh menjalankan workflow repo lain dengan token bawaan GitHub.

> [!IMPORTANT]
> Token ini hanya boleh menjalankan workflow di `cogan17/CoganSU`. Jangan beri akses ke repo lain atau izin lain. Jangan bagikan isinya ke siapa pun, termasuk ke chat.

---

## 1. Buat token (fine-grained)

Buka **https://github.com/settings/personal-access-tokens/new** (login sebagai `cogan17`). Dari menu: foto profil → **Settings** → paling bawah **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**. Isi dari atas ke bawah:

1. **Token name**: `Cogan Kernel - Build CoganSU`
2. **Description** (boleh kosong): `Dipakai Cogan Kernel Builder untuk menjalankan Build CoganSU`
3. **Resource owner**: biarkan **cogan17**.
4. **Expiration**: ketuk **No expiration** → **Custom…** → pilih tanggal setahun lagi, lalu catat tanggalnya. *No expiration* juga jalan, tetapi GitHub menyarankan tanggal.
5. **Repository access**: pilih **Only select repositories** (bukan *Public repositories* atau *All repositories*) → ketuk **Select repositories** → ketik `CoganSU` → centang **cogan17/CoganSU** saja.
6. **Permissions**:
   - Setelah repo dipilih, kotak Permissions punya bagian **Repositories** di samping **Account**. Buka **Repositories**.
   - Ketuk **Add permissions** → centang **Actions** → tutup daftarnya.
   - Di baris **Actions**, ubah *Read-only* menjadi **Read and write**.
   - **Metadata** (*Read-only*) ikut otomatis, biarkan.
   - Bagian **Account** tetap **0**, jangan ditambah.
7. Ketuk **Generate token**. Bila muncul ringkasan, cek isinya: repo `cogan17/CoganSU`, *Actions: Read and write*, *Metadata: Read-only*. Lalu ketuk **Generate token** lagi.
8. **Salin** token yang muncul (diawali `github_pat_…`). Token hanya ditampilkan sekali.

## 2. Simpan sebagai secret di Cogan-Kernel

1. Buka **https://github.com/cogan17/Cogan-Kernel/settings/secrets/actions**.
   Dari menu: repo **Cogan-Kernel** → **Settings** → **Secrets and variables** → **Actions**. Di HP, kalau menu Settings tidak muncul, aktifkan **Situs desktop** di browser.
2. Ketuk **New repository secret**.
3. **Name**: ketik `COGANSU_TOKEN` (huruf besar, tanpa spasi).
   **Secret**: tempel token dari langkah 1.
4. Ketuk **Add secret**.

## 3. Pakai

Jalankan **Cogan Kernel Builder** seperti biasa dengan Root Flavor `CoganSU` atau kombinasinya. Tidak perlu menjalankan Build CoganSU lebih dulu.

| Release Type kernel | Rilis CoganSU yang dibuat otomatis |
|---|---|
| `CI` | Pre-Release |
| `Pre-Release` | Pre-Release |
| `Release` | Release |

- Bila rilis CoganSU sudah memuat KernelSU terbaru dan cocok dengan SUSFS, Builder langsung membangun kernel, tanpa Build CoganSU.
- Bila perlu, ringkasan Builder menulis **🔄 CoganSU dibangun otomatis** dengan tautan run Build CoganSU-nya. Builder menunggu sekitar 10 menit lebih lama.
- **"Tunggu"** hanya muncul bila dev utama memang belum siap, misalnya *Tunggu simonpunk* saat patch SUSFS juga belum cocok dengan KernelSU `main`.

## Bila ada masalah

| Pesan di ringkasan Builder | Artinya |
|---|---|
| *Secret COGANSU_TOKEN belum ada* | Langkah 2 belum dilakukan. Varian lain tetap dibangun. |
| *COGANSU_TOKEN ditolak GitHub (HTTP 401/403/404)* | Token kedaluwarsa, salah salin, atau izinnya bukan *Actions: Read and write* untuk `cogan17/CoganSU`. Buat token baru (langkah 1), lalu **Update** secret-nya. |
| *Build CoganSU gagal (…): tautan* | Build CoganSU-nya sendiri gagal. Buka tautan itu dan baca log-nya. |

Saat token hampir kedaluwarsa, GitHub mengirim email. Perpanjang dengan **Regenerate token** di halaman token itu, lalu **Update** secret `COGANSU_TOKEN`.

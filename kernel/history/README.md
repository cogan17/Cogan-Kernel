# Riwayat build / Build history

Setiap hasil **Cogan Kernel Builder** dari `main` disimpan otomatis dalam satu dokumen
`run-<ID>-<attempt>.md`: tabel singkat untuk dibaca dan metadata aslinya untuk **Cek pembaruan**.
KernelSU Next dan BakaSU dicatat terpisah di dalam dokumen run yang sama. Build gagal atau
menunggu tidak menggantikan build terakhir yang berhasil.

Dokumen ini disimpan dalam git, sehingga tetap ada setelah log, artifact atau seluruh run Actions
dihapus. Workflow **Hapus log run lama** tidak diubah. **Cek pembaruan** hanya membaca; ia tidak
menulis riwayat, membangun atau menerbitkan. Catatan ini juga tidak dipakai untuk memilih versi
build berikutnya. Tabel sublevel README tetap dicatat lewat tombol **Catat sublevel**.

**Build terakhir:** buka dokumen `run-*.md` di folder ini. Dokumen run #11 dipulihkan dari rilis
`v26.10.26-r4` dan hasil Cek pembaruan yang masih tersedia; sumbernya dicantumkan di dokumen.
Data yang tidak tersedia tidak ditebak. Log asli yang sudah terhapus tidak dipulihkan.

---

Each **Cogan Kernel Builder** run on `main` automatically saves one `run-<ID>-<attempt>.md`
document: a short readable table and its original metadata for **Check for updates**. KernelSU
Next and BakaSU have separate results within the same document. Failed or waiting builds never
replace the last successful build.

These documents are stored in git and survive deletion of Actions logs, artifacts or entire runs.
**Delete old run logs** is unchanged. **Check for updates** only reads; it never records, builds
or publishes. These records never select the next build's versions. The README sublevel table
is still recorded through the **Record sublevels** button.

**Last build:** open the `run-*.md` documents in this folder. Run #11 was restored from release
`v26.10.26-r4` and a retained Check for updates result; its document lists the sources. Unavailable
data is not guessed. Deleted original logs are not recovered.

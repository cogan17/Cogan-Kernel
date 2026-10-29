# Checkpoint — 29 Okt 2026 (WIB)

**CHECKPOINT owner 29 Okt ±11.15 WIB: semua pekerjaan dihentikan.** Sesi berikutnya baca `CLAUDE.md`, file ini dan `CHECKPOINT.md`, lalu lanjut **hanya setelah owner meminta**. Jangan otomatis menguji HP, menjalankan build atau menerbitkan rilis.

## Bug Mulai berhenti → v2.11.2 (owner 29 Okt ±11.26 WIB, rilis DITAHAN)

- **Laporan owner** (screenshot Manager v2.11.1 dan berkas investigasi read-only): Mulai di Kontrol Daya/Suhu kembali "berhenti" setelah keluar dari root manager lalu masuk lagi. Di HP terbaca AUTOSTART=1, power `run/pid` dan `daemon.lock/pid` = 26305, thermal = 27125, tanpa flag disable/remove. Cmdline kedua PID tidak tercetak. Owner: **"Untuk rilis tahan dulu!"**
- **Penyebab (dari kode, belum dibuktikan di HP):** pekerja yang dimulai dari WebUI (`start_controller`/`start_sampler` lewat `setsid`/`nohup`) tetap berada di cgroup v2 aplikasi root manager (`uid_N/pid_M`). Saat proses aplikasi mati, system_server menulis `cgroup.kill` (AOSP `libprocessgroup/processgroup.cpp` `sendSignalToProcessGroup`, dicek 29 Okt) sehingga semua proses di cgroup itu mati, termasuk proses root. SIGKILL melewati trap EXIT, jadi PID dan lock tertinggal, sesuai bukti owner. Pekerja dari `service.sh` saat boot tidak terkena.
- **Perbaikan v2.11.2 (versionCode 30):** `bridge.sh leave_app_cgroup` memindahkan pekerja ke `/sys/fs/cgroup/cgroup.procs`, hanya bila `/proc/$$/cgroup` berisi `::/uid_`. Dipanggil di awal `power/controller.sh` dan `thermal/sampler.sh`. Tes baru ada di `test_cogan_smart_bridge`. [Paket uji](modules/cogan-smart/rilis/v2.11.2/Cogan-Smart-Kernel-v2.11.2.zip) 164759 byte, SHA256 `559d113d1e56e4b6ad48d601d567923897e8ba064839ba564abaa0d403ebc10b` (dua kali dikemas, sama). Belum diuji di HP.
- **Bukti di HP setelah pasang (read-only):** `su -c 'for f in /data/adb/cogan_smart/power/run/pid /data/adb/cogan_smart/thermal/run/sampler.pid; do p=$(cat $f); echo $f $p; cat /proc/$p/cgroup | grep "^0::"; done'` harus menampilkan `0::/`, bukan `0::/uid_…`. Lalu tutup root manager, buka lagi, dan status harus tetap aktif.
- **Dampak ke PR #80 (v2.12.0):** merge `main` ke branch itu, naikkan versionCode v2.12.0 menjadi 31, dan tambahkan `leave_app_cgroup` di awal `apps/block.sh` (blokir yang dinyalakan dari WebUI punya bug yang sama).

## Sedang berjalan

- **[PR #80](https://github.com/cogan17/Cogan-Kernel/pull/80) terbuka**, branch `feat/cogan-smart-tab-aplikasi`: Cogan Smart **v2.12.0** (versionCode 30), tab baru 📱 Aplikasi (pantau gerak-gerik, hapus sampai akar, blokir APK). Rincian lengkap ada di bagian v2.12.0 `checkpoint.md` di branch itu.
  - Commit 1 (sudah di-push): tab Aplikasi lengkap. Paket uji dan SHA256 `c1bd3f9f40ada48451d6a1f188e8aa41e4bcdbe3ce550c7335345a56a478b6a5` dibuat untuk commit ini. Hasil Validate belum dicek.
  - Commit 2 `5130ca8` (WIP checkpoint, sudah di-push): atas pilihan owner, blokir APK ditambah Signal, Threads, TikTok Lite, MiChat, Plus Messenger, Gmail, Outlook, Email Xiaomi, Yahoo Mail, Google Messages dan Pesan Xiaomi (total 33 paket di `apps/common.sh`). Gmail dan Pesan adalah aplikasi sistem, jadi daftar "Terpasang" kini dibaca dari semua paket. Teks WebUI, i18n, Panduan, README, CHANGELOG, catatan rilis dan tes ikut diperbarui. Terukur lokal sebelum checkpoint: 257 tes lolos, termasuk BusyBox ash/awk, dan cek WebUI Node lolos.
- Owner sudah ditanya apakah blokir berlaku untuk sosmed selain WA. Jawabannya: tambah sosmed lain, email dan SMS (commit 2).

## Belum selesai (PR #80)

1. **ZIP `rilis/v2.12.0/` belum dikemas ulang** setelah commit 2. SHA di README dan `checkpoint.md` branch PR masih SHA lama `c1bd3f9f…b6a5`.
2. Validate PR #80 belum dicek, PR belum di-merge, dan ZIP belum dikirim ke owner.
3. v2.12.0 belum diuji di HP. Yang belum terbukti: format dump HyperOS 3 (appops, netstats, batterystats), dan apakah pemasang paket Xiaomi menghormati izin sumber yang dicabut.

## Langkah pertama berikutnya (setelah owner meminta)

- `git checkout feat/cogan-smart-tab-aplikasi`.
- `python3 scripts/package_module.py modules/cogan-smart modules/cogan-smart/rilis/v2.12.0` dua kali, dan pastikan SHA keduanya sama.
- Ganti SHA lama di `modules/cogan-smart/README.md` dan `checkpoint.md` (beserta ukuran byte).
- Jalankan `python3 -m unittest discover -s tests -b` dan `node tests/cogan_smart_client_check.js`.
- Commit sebagai owner, push, cek Validate PR #80, squash-merge, lalu kirim ZIP ke owner.

## Sudah selesai (sesi 28–29 Okt)

- [PR #79](https://github.com/cogan17/Cogan-Kernel/pull/79) `381e848`: v2.11.1 (Manager hanya memantau, keluar WebUI sekali usap). ✅ Owner 29 Okt: "Semuanya lolos uji disisi saya".
- v2.11.1 (lihat bagian v2.11.1): revisi owner atas v2.11.0 dan perbaikan usap kembali.
- [PR #77](https://github.com/cogan17/Cogan-Kernel/pull/77) `61dbf3cfefc3b3942289b5c25734964ea8e18ee5`, digabung 29 Okt 09.55 WIB: v2.11.0 (lihat bagian v2.11.0). [Validate 40809071342](https://github.com/cogan17/Cogan-Kernel/actions/runs/40809071342) lolos 09.54 WIB. ZIP uji dikirim ke owner.
- [PR #76](https://github.com/cogan17/Cogan-Kernel/pull/76) `2291616df26941b6393c071a2f7c9bfb43382da1`, digabung 29 Okt 07.11 WIB: artifact dan rilis kernel hanya membawa modul SUSFS sidex15 (file 5); modul simonpunk tidak dibangun lagi, SUSFS simonpunk tetap dicek di Cek pembaruan (aturan di `CLAUDE.md`).
- PR #72–#75 (28 Okt): hook init ZRAM v2.10.6 → v2.10.7 → v2.10.8; v2.10.8 diuji owner di HP 23.23 WIB (`zram0: zstd`).
- PR #70–#71 (28 Okt): deteksi DRAM MediaTek v2.10.5 dan checkpoint.

## Tertunda (keputusan owner)

- Uji v2.12.0 di HP setelah PR #80 selesai: tab Aplikasi terisi, APK kiriman WhatsApp ditolak, dan izin yang dinyalakan lagi dicabut dengan notifikasi.
- Rilis Cogan Smart (v2.11.1 sudah lolos uji HP, atau v2.12.0 setelah diuji) lewat Cogan Smart Release: belum diminta.

## v2.10.4 — initrc ZRAM (versionCode 23)

- Integrasi init ZRAM Cogan Smart **v2.10.4 / versionCode 23** sudah masuk `main`: [PR #68](https://github.com/cogan17/Cogan-Kernel/pull/68), commit `0386eed3f4952a837a81c36da80a22644083c563`; [Validate 40693190837](https://github.com/cogan17/Cogan-Kernel/actions/runs/40693190837) dengan **251 tes lolos**. [Paket uji v2.10.4](modules/cogan-smart/rilis/v2.10.4/Cogan-Smart-Kernel-v2.10.4.zip) SHA256 `73abbc48992235ffcb7a2705eda6f561e892d09420713add514ed9651e262f90`. Tidak ada GitHub Release baru; rilis publik terakhir v2.9.1.
- v2.10.4 menggunakan dukungan `initrc` KernelSU Next/BakaSU pada Cogan r5 untuk memilih kompresor sebelum ZRAM diinisialisasi. Tidak menambah governor DRAM, tidak reset ZRAM dan tidak swapoff.
- Screenshot HP owner menunjukkan **v2.10.4 terpasang**, `zram0: lz4 · swap aktif`, opsi LZ4 terpilih, status “initrc tersiapkan untuk boot berikutnya”, dan `bw_hwmon` abu-abu. Bacaan LZ4/swap aktif terbukti, tetapi tidak membuktikan modul yang mengganti LZ4. Belum ada bukti hasil ZSTD atau hasil eksekusi hook initrc pada HP.
- Owner menjalankan pembacaan root `/sys/class/devfreq/*`. Hasilnya: `112b0000.ufshci` → driver `ufshcd-mtk`, governor `simple_ondemand`; `13000000.mali` → driver `mali`, governor `dummy`; **`mtk-dvfsrc-devfreq` → driver `mtk-dvfsrc-devfreq`, governor `userspace`**. Ketiganya menampilkan daftar sama: `dummy apupassive-pe apuconstrain apuuser apupassive userspace powersave performance simple_ondemand`. **Tidak ada `bw_hwmon`.** `available_governors` devfreq dapat bersifat global; daftar UFS/GPU bukan bukti dukungan DRAM. `userspace` adalah governor aktif DRAM, bukan bukti ZRAM gagal. Jangan mengganti ke `simple_ondemand` atau port governor Qualcomm dengan asumsi.

## v2.11.1 — Manager hanya memantau, keluar sekali usap (versionCode 29)

- **Revisi owner (29 Okt, dengan screenshot tombol mode dan Pindai modul di Manager):** mode diatur tab Daya dan pindai modul oleh tab Modul; Manager hanya memantau. "Sisanya tidak perlu diubah": kartu Prosesor, RAM, Kontrol Daya/Suhu dan Aplikasi di Manager tetap.
- **Manager:** tiga tombol mode diganti satu baris `#modeLine` (nama mode + keterangan dari setelan tab Daya); tombol Pindai modul dihapus, `#guardLine` membaca pindaian terakhir tab Modul (`guard.cached('scan')`, tab Modul memindai otomatis bila hasil > 2 menit).
- **Bug keluar WebUI (owner: harus usap berkali-kali):** tiap tab adalah halaman sendiri, jadi setiap pindah tab menambah riwayat WebView, dan usap kembali menelusuri riwayat itu dulu sebelum menutup WebUI. `i18n.js` (dimuat semua halaman) kini mengganti riwayat (`location.replace`) untuk tautan internal, kecuali `guide.html`, jadi kembali dari Panduan membuka tab sebelumnya. Terukur lokal (Playwright): 5 kali pindah tab → satu entri riwayat; kembali dari Panduan → tab Manager. Penyebab di HP disimpulkan dari cara kerja WebView, belum dibuktikan di HP.
- Panduan (WebUI, PANDUAN.md/.en.md), README, CHANGELOG disesuaikan. Tes Manager memeriksa `modeLine`.
- Terukur lokal: tes Python + cek WebUI lolos. [Paket uji](modules/cogan-smart/rilis/v2.11.1/Cogan-Smart-Kernel-v2.11.1.zip) 41 file, 163739 byte, SHA256 `8961d4c5d23c0f02a1a326b9f86ff87b524a7e8b40bdc38a1fd71b54d54d3175` (dua kali dikemas, sama).
- **Belum diuji di HP dan belum dirilis.**

## v2.11.0 — Manager pusat kendali, Mode Dev, Panduan (versionCode 28)

- **Permintaan owner (29 Okt):** Manager hierarkinya di atas tab lain (lihat semua statistik/grafik, terapkan/paksa perubahan); teks terlalu baku dan panjang, perlu versi user ringkas dan versi Dev/debug; buku panduan. Pilihan owner lewat pertanyaan: **pusat kendali** (Manager ringkasan + semua tombol, tab lain untuk detail dan pilihannya sendiri), **satu saklar Mode Dev** di Tentang, **panduan di modul + repo**, log **cukup dianalisa**.
- **Manager:** kartu 📊 Ringkasan (suhu Badan HP/baterai/prosesor, pengendali, pencatat, tombol mode, grafik 1 jam + waktu panas + penyebab utama, hasil pindai modul + tombol Pindai modul). Grafik dipindah ke `client.js` (`UI.chart`) dan dipakai tab Suhu juga. Aksi per modul (percaya, nonaktifkan, hapus) tetap di tab Modul karena per item.
- **Mode Dev:** `theme.css` menyembunyikan `.dev` kecuali `<html data-dev="1">` (`localStorage cogan.dev`); `.user` disembunyikan saat Mode Dev. Detail teknis di semua tab ditandai `.dev`; setelan lanjutan (interval cek, terapkan ulang, interval pencatat) hanya di Mode Dev.
- **Panduan:** `webroot/guide.html` (ID/EN), `PANDUAN.md` dan `PANDUAN.en.md` (isi sama, tidak ikut ZIP: `scripts/package_module.py` melewatinya seperti README).
- **Terjemahan:** perbaikan aturan i18n (isian tidak melewati pemisah " · " atau baris baru), entri baru, `tests/test_cogan_smart_webui.py` menjalankan cek WebUI Node dan memastikan mode English tanpa teks Indonesia (dijalankan Validate).
- **Log 16 jam owner (28 Okt 17.31 – 29 Okt 09.31 WIB):** Badan HP maks 43,6 °C, baterai maks 44,0 °C (mengecas), beban modul median 1,8% CPU. Arus 13–16 A berurutan saat HyperCharge dan kolom GPU kosong saat GPU tidur adalah normal; tidak ada perubahan pencatat, dijelaskan di Panduan.
- Terukur lokal: semua tes Python + cek WebUI lolos; halaman dimuat Playwright tanpa error di mode pengguna dan Dev. [Paket uji](modules/cogan-smart/rilis/v2.11.0/Cogan-Smart-Kernel-v2.11.0.zip) 41 file, 163348 byte, SHA256 `e39523e0fa0d8a311956ac3c111979dcd844cfb91d3e553ddc6a17175e13443c` (dua kali dikemas, sama).
- **Sudah di `main`:** PR #77, commit `61dbf3c`, 29 Okt 09.55 WIB. **Belum diuji di HP dan belum dirilis.**

## v2.10.8 — hook ZRAM sebelum system_perf_init (versionCode 27)

- **v2.10.7 di HP (28 Okt, 22.52 WIB):** `Hook boot ini: zstd boot-completed pending`, `zram0: lz4`. Saat boot selesai ZRAM sudah aktif; tahap boot-completed v2.10.7 terlambat.
- **Bukti di HP (root, 22.53–22.56 WIB):**
  - dmesg 0,35 dtk `ExtM: Added device: zram0`; 9,751 dtk KernelSU `exec '/system_ext/xbin/system_perf_init'`; 9,768 dtk `zram0: detected capacity change`; 9,776 dtk `Adding 12582908k swap on /dev/block/zram0. Priority:-2`; 9,789 dtk `INIT:zygote-start`. Prioritas -2 berarti bukan `swapon_all` fstab (`swapprio=10`).
  - `/system_ext/etc/init/init.miui.ext.rc`: `service system_perf_init /system_ext/xbin/system_perf_init` (class main, disabled), dan baris 226–228 `# system_perf_init: after load_persist_props_action && before zygote-start` → `on load-bpf-programs` → `start system_perf_init`. String biner memuat `swapon`, `mkswap`, `/sys/block/zram0/disksize`, `persist.sys.zram.disksize`, tanpa `comp_algorithm`: ia memakai algoritme yang sedang terpasang.
  - `/proc/swaps`: hanya `/dev/block/zram0`, prioritas -2. Modul lain (AshLooper, tcp_optimiser, dll.) tidak menyentuh ZRAM.
- **Perbaikan:** tahap hook terakhir menjadi `on load-bpf-programs` (boot-completed dihapus). AOSP `rootdir/init.rc`: `trigger post-fs-data` (520) → `trigger load-bpf-programs` (523) → `trigger zygote-start` (527); `init.cpp` membaca `/system/etc/init/hw/init.rc` sebelum `/system_ext/etc/init`. Jadi hook berjalan sesudah lz4 vendor dan sebelum `start system_perf_init`.
- Terukur lokal: tes Manager lolos. [Paket uji](modules/cogan-smart/rilis/v2.10.8/Cogan-Smart-Kernel-v2.10.8.zip) 40 file, 151578 byte, SHA256 `552fb6fecb65d60373289601d4ad0ae32d4be775a5fc76354e6ca47f495afbd8` (dua kali dikemas, sama).
- ✅ **Diuji di HP:** Uji HP owner 28 Okt, 23.23 WIB: `zram0: zstd · swap aktif` dan `Hook boot ini: zstd load-bpf-programs matching`. Pilihan ZSTD kini benar-benar dipakai saat ZRAM dinyalakan. Dampak ke performa/baterai belum diukur. **Belum dirilis**: GitHub Release lewat workflow Cogan Smart Release adalah keputusan owner.

## v2.10.7 — pilihan ZRAM bertahan sampai swap aktif (versionCode 26)

- **v2.10.6 di HP (28 Okt, 22.41 WIB):** `Hook boot ini: zstd post-fs matching`, jadi perbaikan hook v2.10.6 terbukti bekerja. Tetapi `zram0` kembali `lz4`.
- **Penyebab, terbaca di HP (root):** `/vendor/etc/init/hw/init.mt6989.rc` baris 192 `write /sys/block/zram0/comp_algorithm lz4` di `on post-fs-data` (baris 180), dan baris 1138 `swapon_all /vendor/etc/fstab.enableswap` di `on property:sys.boot_completed=1` (baris 1122). fstab: `/dev/block/zram0 none swap defaults zramsize=100%,swapprio=10`. `mmd.enabled_aconfig=false`. Hanya baris 192 yang menulis `comp_algorithm` di semua folder init.
- **Perbaikan:** hook juga berjalan pada `property:sys.boot_completed=1`. Menurut kode init AOSP (`import_parser.cpp` `EndFile`, `action_manager.cpp`), import vendor dibaca sesudah `init.rc` (tempat KernelSU menempel aturan modul), dan aksi dengan pemicu sama berjalan sesuai urutan baca. Jadi hook menulis pilihan sesudah lz4 vendor dan tepat sebelum `swapon_all`. Tes Manager memeriksa empat blok dan pemicu terakhirnya.
- Terukur lokal: tes Manager lolos. [Paket uji](modules/cogan-smart/rilis/v2.10.7/Cogan-Smart-Kernel-v2.10.7.zip) 40 file, 150996 byte, SHA256 `4546ec64b2d06fa32f39be4e789827f2a5f40fa1e5c8f6e87d85277ccec14720` (dua kali dikemas, sama).
- **Belum diuji di HP dan belum dirilis.** Uji: pasang v2.10.7, reboot, tunggu boot selesai, buka Manager. Harapan: `zram0: zstd` dan `Hook boot ini: zstd boot-completed matching`.

## v2.10.6 — perbaikan hook init ZRAM (versionCode 25)

- **Bukti HP owner, 28 Okt sekitar 22.18–22.26 WIB (v2.10.5 terpasang):** bagian DRAM tampil benar (`DRAM MediaTek · mtk-dvfsrc-devfreq: userspace`, tanpa dropdown BW). Setelah memilih ZSTD dan restart, `zram0` tetap `[lz4]` (zstd tersedia) dan penanda `/dev/.cogan_smart_zram_init` tidak ada. Root: rc modul punya 3 blok `on` dengan `exec u:r:ksu:s0`; cache `/metadata/vold/ksu/modules.rc` berisi aturan Cogan; dmesg `KernelSU: module rc: loaded 4024 bytes`; config `RAM=heavy BOOT=1`, `init.state=ready`. Kesimpulan: hook v2.10.4–v2.10.5 tidak pernah berjalan.
- **Penyebab, dari kode init AOSP (mirror GitHub `aosp-mirror/platform_system_core`, `init/tokenizer.cpp`, `action.cpp`, `service.cpp`, `util.cpp`):** di dalam `"..."` tokenizer init tidak mengenal escape, jadi `\"` di program menutup kutipan dan baris exec terpotong. Argumen `exec` diekspansi dua kali (`RunBuiltinFunction`, lalu `ExpandArgsAndExecv` saat proses dimulai), dan `$` tunggal sesudah ekspansi pertama memicu `LOG(FATAL)` "deprecated syntax". Bukti `dmesg` untuk pesan itu belum terbaca: perintahnya tertelan karena ditempel sebelum prompt root muncul.
- **Perbaikan:** program ditulis sebagai satu token init tanpa kutipan (`\\`, `\"`, `\ `) dan setiap `$` menjadi `$$$$`. Isi program dan pemeriksaannya tidak berubah. Tes Manager kini meniru tokenizer dan ekspansi init AOSP; tes itu gagal pada kode v2.10.5 dan lolos pada v2.10.6.
- [Paket uji](modules/cogan-smart/rilis/v2.10.6/Cogan-Smart-Kernel-v2.10.6.zip) 40 file, 150361 byte, SHA256 `585210b1d596853d8dc14dc1a4a20dbd676431e9e2c2cd85b22b865f83809ba7` (dua kali dikemas, sama).
- **Belum diuji di HP dan belum dirilis.** Risiko berikutnya: `zram.ko` adalah modul (GKI `CONFIG_ZRAM=m`); bila belum dimuat pada tahap init/early-fs/post-fs, penanda akan berbunyi `missing`, dan itu masalah waktu muat yang perlu langkah lain.
- Uji HP berikutnya (keputusan owner): pasang ZIP v2.10.6, reboot, buka Manager. Harapan: `zram0: zstd` dan baris `Hook boot ini: zstd post-fs matching`.

## v2.10.5 — paket uji deteksi DRAM MediaTek (versionCode 24)

- **Sudah di `main`:** [PR #70](https://github.com/cogan17/Cogan-Kernel/pull/70), commit `8b1fe721a22aa5ed1d4ec24c98794cad8489a8bd`, digabung 28 Okt sekitar 22.11 WIB. [Validate 40713132298](https://github.com/cogan17/Cogan-Kernel/actions/runs/40713132298) lolos (tes, YAML, shell; 22.10 WIB). Branch draf `fix/cogan-smart-dram-detection` tidak diperlukan lagi.
- Draf dari branch `fix/cogan-smart-dram-detection` diperiksa dan diselesaikan. DRAM dikenali dari ikatan driver `mtk-dvfsrc-devfreq`; Manager menampilkan governor aktual; UFS/GPU tidak lagi menjadi target BW walau daftar governor-nya sama; dropdown BW disembunyikan bila tidak ada pilihan yang bisa dipakai, kecuali untuk mengembalikan pilihan lama ke DRAM Sistem.
- Tambahan saat penyelesaian: teks DRAM di mode English kini diterjemahkan penuh (termasuk "belum terbaca" → "unavailable").
- Terukur lokal: 252 tes Python dan cek WebUI lolos; `sh -n` lolos. [Paket uji](modules/cogan-smart/rilis/v2.10.5/Cogan-Smart-Kernel-v2.10.5.zip) 40 file, 149444 byte, dapat dibuat ulang dengan SHA256 `a148ff25d146b7cb162622b1eb5c8c5c45609a4d75ed26ff70c918539336966d` (cara kemas dibuktikan dengan membuat ulang ZIP v2.10.4: SHA256 sama).
- **Belum ada uji HP v2.10.5 dan belum ada GitHub Release** (rilis publik terakhir v2.9.1). Ini perbaikan deteksi dan tampilan; tidak menambah `bw_hwmon`, tidak mengganti governor DRAM dan tidak butuh kernel baru.
- Uji HP berikutnya (keputusan owner): pasang ZIP sebagai pembaruan modul, reboot, buka Manager. Bagian DRAM seharusnya menampilkan `DRAM MediaTek · mtk-dvfsrc-devfreq: userspace` tanpa dropdown BW.

[Checkpoint sebelumnya](https://github.com/cogan17/Cogan-Kernel/blob/f8312e007c6cca8829aec01bc3d251334e467135/checkpoint.md) memuat riwayat v2.10.0–v2.10.3, pemindai aplikasi dan rilis v2.9.1. Gunakan identitas git Cogan, PR ke main, catatan ID/EN dan hemat Actions sesuai `CLAUDE.md`.

## English state summary

CHECKPOINT by the owner, 29 Oct around 11.15 WIB: all work stopped. v2.11.1 is merged (#79) and passed the owner's phone test. PR #80 (v2.12.0, the Apps tab) is open. Its WIP commit `5130ca8` extends the APK block to 33 chat, social, email and SMS apps. The test ZIP still has to be repackaged after that commit, and its SHA updated in the README and checkpoint. After that: run the tests, check Validate, merge and send the ZIP. Continue only when the owner asks.

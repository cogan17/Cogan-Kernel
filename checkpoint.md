# Checkpoint — 28 Okt 2026 (WIB)

Owner meminta draf v2.10.5 dilanjutkan (28 Okt). Paket uji v2.10.5 selesai dan sudah di `main` lewat [PR #70](https://github.com/cogan17/Cogan-Kernel/pull/70); lihat bagian v2.10.5. Sesi berikutnya baca `CLAUDE.md`, file ini dan `CHECKPOINT.md`, lalu tunggu instruksi owner. Jangan otomatis menguji HP, menjalankan build atau menerbitkan rilis.

## Sudah selesai

- Integrasi init ZRAM Cogan Smart **v2.10.4 / versionCode 23** sudah masuk `main`: [PR #68](https://github.com/cogan17/Cogan-Kernel/pull/68), commit `0386eed3f4952a837a81c36da80a22644083c563`; [Validate 40693190837](https://github.com/cogan17/Cogan-Kernel/actions/runs/40693190837) dengan **251 tes lolos**. [Paket uji v2.10.4](modules/cogan-smart/rilis/v2.10.4/Cogan-Smart-Kernel-v2.10.4.zip) SHA256 `73abbc48992235ffcb7a2705eda6f561e892d09420713add514ed9651e262f90`. Tidak ada GitHub Release baru; rilis publik terakhir v2.9.1.
- v2.10.4 menggunakan dukungan `initrc` KernelSU Next/BakaSU pada Cogan r5 untuk memilih kompresor sebelum ZRAM diinisialisasi. Tidak menambah governor DRAM, tidak reset ZRAM dan tidak swapoff.
- Screenshot HP owner menunjukkan **v2.10.4 terpasang**, `zram0: lz4 · swap aktif`, opsi LZ4 terpilih, status “initrc tersiapkan untuk boot berikutnya”, dan `bw_hwmon` abu-abu. Bacaan LZ4/swap aktif terbukti, tetapi tidak membuktikan modul yang mengganti LZ4. Belum ada bukti hasil ZSTD atau hasil eksekusi hook initrc pada HP.
- Owner menjalankan pembacaan root `/sys/class/devfreq/*`. Hasilnya: `112b0000.ufshci` → driver `ufshcd-mtk`, governor `simple_ondemand`; `13000000.mali` → driver `mali`, governor `dummy`; **`mtk-dvfsrc-devfreq` → driver `mtk-dvfsrc-devfreq`, governor `userspace`**. Ketiganya menampilkan daftar sama: `dummy apupassive-pe apuconstrain apuuser apupassive userspace powersave performance simple_ondemand`. **Tidak ada `bw_hwmon`.** `available_governors` devfreq dapat bersifat global; daftar UFS/GPU bukan bukti dukungan DRAM. `userspace` adalah governor aktif DRAM, bukan bukti ZRAM gagal. Jangan mengganti ke `simple_ondemand` atau port governor Qualcomm dengan asumsi.

## v2.10.5 — paket uji deteksi DRAM MediaTek (versionCode 24)

- **Sudah di `main`:** [PR #70](https://github.com/cogan17/Cogan-Kernel/pull/70), commit `8b1fe721a22aa5ed1d4ec24c98794cad8489a8bd`, digabung 28 Okt sekitar 22.11 WIB. [Validate 40713132298](https://github.com/cogan17/Cogan-Kernel/actions/runs/40713132298) lolos (tes, YAML, shell; 22.10 WIB). Branch draf `fix/cogan-smart-dram-detection` tidak diperlukan lagi.
- Draf dari branch `fix/cogan-smart-dram-detection` diperiksa dan diselesaikan. DRAM dikenali dari ikatan driver `mtk-dvfsrc-devfreq`; Manager menampilkan governor aktual; UFS/GPU tidak lagi menjadi target BW walau daftar governor-nya sama; dropdown BW disembunyikan bila tidak ada pilihan yang bisa dipakai, kecuali untuk mengembalikan pilihan lama ke DRAM Sistem.
- Tambahan saat penyelesaian: teks DRAM di mode English kini diterjemahkan penuh (termasuk "belum terbaca" → "unavailable").
- Terukur lokal: 252 tes Python dan cek WebUI lolos; `sh -n` lolos. [Paket uji](modules/cogan-smart/rilis/v2.10.5/Cogan-Smart-Kernel-v2.10.5.zip) 40 file, 149444 byte, dapat dibuat ulang dengan SHA256 `a148ff25d146b7cb162622b1eb5c8c5c45609a4d75ed26ff70c918539336966d` (cara kemas dibuktikan dengan membuat ulang ZIP v2.10.4: SHA256 sama).
- **Belum ada uji HP v2.10.5 dan belum ada GitHub Release** (rilis publik terakhir v2.9.1). Ini perbaikan deteksi dan tampilan; tidak menambah `bw_hwmon`, tidak mengganti governor DRAM dan tidak butuh kernel baru.
- Uji HP berikutnya (keputusan owner): pasang ZIP sebagai pembaruan modul, reboot, buka Manager. Bagian DRAM seharusnya menampilkan `DRAM MediaTek · mtk-dvfsrc-devfreq: userspace` tanpa dropdown BW.

[Checkpoint sebelumnya](https://github.com/cogan17/Cogan-Kernel/blob/f8312e007c6cca8829aec01bc3d251334e467135/checkpoint.md) memuat riwayat v2.10.0–v2.10.3, pemindai aplikasi dan rilis v2.9.1. Gunakan identitas git Cogan, PR ke main, catatan ID/EN dan hemat Actions sesuai `CLAUDE.md`.

## English state summary

v2.10.4 native ZRAM init integration is on main (PR #68). The owner's devfreq dump identifies DRAM as `mtk-dvfsrc-devfreq` with `userspace`; no device offers `bw_hwmon`. v2.10.5 (versionCode 24) finishes the DRAM detection/UI draft: driver-bound DRAM identification, actual governor readback, no UFS/GPU BW targets, hidden BW dropdown when unusable, full English text. 252 local tests and the WebUI check pass; the reproducible test ZIP has SHA256 `a148ff25…966d`. Merged to main via PR #70 (`8b1fe72`) after Validate 40713132298 passed. Not phone-tested and not released. Wait for the owner's instructions.

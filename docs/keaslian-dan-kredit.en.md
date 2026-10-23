# 🔏 Authenticity & Credits

[← Back to README](../README.en.md) · <img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> [Bahasa Indonesia](keaslian-dan-kredit.md)

The Cogan kernel for the Xiaomi 14T Pro (`rothko`) is built automatically by GitHub Actions in **[cogan17/Xiomi_14T_Pro](https://github.com/cogan17/Xiomi_14T_Pro)**. The build workflow of this repository **digitally signs** the kernel ZIP (artifact attestation), so anyone can prove where it came from.

This repository continues **[cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro)**. The old releases of that repository are copied here as an **archive** (see [Release archive](#-release-archive)). The archived files are unchanged to the bit: same SHA256, still signed in the name of their original repository.

> What is proven is that **this rothko kernel build** was made by Cogan17. The Linux kernel, the Android Common Kernel and the features inside are the work of the contributors under [Credits](#-credits).

---

## How to check authenticity

1. **Proof page:** [github.com/cogan17/Xiomi_14T_Pro/attestations](https://github.com/cogan17/Xiomi_14T_Pro/attestations) for builds of this repository; [github.com/cogan17/Kernel-14t-pro/attestations](https://github.com/cogan17/Kernel-14t-pro/attestations) for the archived releases.
2. **With the GitHub CLI:**
   ```
   gh attestation verify <zip> --repo cogan17/Xiomi_14T_Pro     # builds of this repository
   gh attestation verify <zip> --repo cogan17/Kernel-14t-pro    # archived releases r5, r6, r8
   ```
   Only a genuine ZIP passes.
3. **The run page in [Actions](https://github.com/cogan17/Xiomi_14T_Pro/actions):** every build shows the KMI gate result, the version of every component, the feature list and the sha256 of its ZIP.
4. **On the phone** (Termux / root manager terminal):
   ```
   su -c cat /sys/kernel/cogan/banner
   ```
   Shows the real version, the builder and the build date. The file comes from **Cogan Bridge** inside the kernel, so SUSFS does not mask it.
5. **Cogan Smart Kernel module:** any tab → Kernel card → **"Real identity · verified"** and **"✓ kernel built for this phone"**.
6. **Other files in a release** (manager, NoMount, Cogan Smart Kernel module) are not signed. Compare their SHA256 with the release's `checksums.txt` or the list below.

## What is proven, and what is not

| If someone… | Result |
|---|---|
| re-uploads the ZIP and claims it as theirs | ✅ disproved: its fingerprint matches the signature of Cogan17's repository |
| changes the ZIP slightly (e.g. the name in the AnyKernel3 banner) | ✅ detected: it becomes a different file and fails verification |
| forks the repository and builds it | ✅ their signature names **their repository**; the dated commit history here shows who came first |
| copies the code | not prevented (open project), but its origin can still be proven |
| swaps the manager, NoMount or module in a fake release | ✅ detected: the SHA256 no longer matches |

---

## 📦 Release archive

Copied from [cogan17/Kernel-14t-pro/releases](https://github.com/cogan17/Kernel-14t-pro/releases) on 23 Oct 2026, with the same tags and files. In this repository's [Releases](https://github.com/cogan17/Xiomi_14T_Pro/releases) their titles start with **📦 Arsip**.

### Kernels (signed by the original repository)

| Release | Kernel | Root | Tested | Signature |
|---|---|---|---|---|
| [v26.10.23-r8](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/v26.10.23-r8) | ACK 6.1.176 (`android14-6.1-2026-09_r4`) | BakaSU `5b76b884` (35222) + SUSFS v2.3.0 | by the owner on the phone | ✅ run [39899556040](https://github.com/cogan17/Kernel-14t-pro/actions/runs/39899556040) |
| [v26.10.22-r6](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/v26.10.22-r6) | ACK 6.1.176 (`android14-6.1-2026-09_r4`) | KernelSU Next (pershoot's fork `d21e0a6`, 33405) + SUSFS | by the owner on the phone | ✅ run [39807276281](https://github.com/cogan17/Kernel-14t-pro/actions/runs/39807276281) |
| [v26.10.22-r5](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/v26.10.22-r5) | ACK 6.1.138 (same as the phone's stock kernel) | KernelSU Next (33405) + SUSFS | by the owner on the phone | ✅ run [39760534547](https://github.com/cogan17/Kernel-14t-pro/actions/runs/39760534547) |

All of them also carry BBRv3, Baseband Guard, NoMount, Cogan Bridge and Full LTO. Check with `gh attestation verify <zip> --repo cogan17/Kernel-14t-pro`.

### Shipped with the kernels (not made by Cogan17)

| File | Origin |
|---|---|
| `2-MANAGER_BakaSU_ci-5b76b884c75f.apk` (r8) | The owner's BakaSU manager `v4.2.0-rc3-5b76b884` (35222), the same version as the driver in the kernel |
| `2-MANAGER_KernelSU-Next_v3.4.2-50-gb427a3f9_33405.apk` (r5, r6) | Official CI build of [KernelSU Next](https://github.com/KernelSU-Next/KernelSU-Next) commit `b427a3f9` (33405) |
| `3-MANAGER-SPOOFED_KernelSU-Next_v3.4.2-50-gb427a3f9_33405.apk` (r5, r6) | Official CI build of KernelSU Next, spoofed variant (hidden package name) |
| `4-NOMOUNT-MODULE_v2.1.1.zip` (r5, r6, r8) | Official [NoMount](https://github.com/maxsteeel/nomount/releases) v2.1.1 release (`NoMount-v2.1.1-release-7046c7a-555.zip`), renamed only |
| `checksums.txt` | SHA256 of every file in that release |

### Cogan Smart Kernel module (made by Cogan17)

| Release | versionCode | Tested |
|---|---|---|
| [cogan-smart-v2.8.2](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/cogan-smart-v2.8.2) | 16 | by the owner on the phone (kernel r6), HyperCharge charging too |
| [cogan-smart-v2.8.1](https://github.com/cogan17/Xiomi_14T_Pro/releases/tag/cogan-smart-v2.8.1) | 15 | by the owner on the phone |

Cogan17 made the ZIPs and they are published **as they are** (byte for byte). Copies are in [`modules/cogan-smart/rilis/`](../modules/cogan-smart/rilis) and the open source is [`modules/cogan-smart`](../modules/cogan-smart). Not signed (attestation) yet.

### SHA256 of every archived file

`sha256sum` format: in Termux, `sha256sum <file>` must print the same value.

```
2f630d65694c3585336d9a2e6cb0d8514737f3aa5d4170612fc388d4f6f944a2  1-KERNEL_Cogan-Rothko-ACK-6.1.176_BakaSU+SuSFS_v26.10.23-r8.zip
f3bba663d07e583c4355ae4e7888018fd15b030ecdddb705855c09611070a1f0  1-KERNEL_Cogan-Rothko-ACK-6.1.176_KernelSU-Next+SuSFS_v26.10.22-r6.zip
b69446d4a1bed0b1abe87945091a902310d63d8c28565d4764aa2797cc7e5d74  1-KERNEL_Cogan-Rothko-ACK-6.1.138_KernelSU-Next+SuSFS_v26.10.22-r5.zip
c4c461d77d2043a25531e32fdba77848acbdc4764a23ac1ab824fa477947874c  2-MANAGER_BakaSU_ci-5b76b884c75f.apk
43acb0587741b845712a12c1ea08cacb8aede72118f4895312745a6769a45fda  2-MANAGER_KernelSU-Next_v3.4.2-50-gb427a3f9_33405.apk
608d167f580dc0d5094f07eb9d0ff48118e068506e52ffc22d6425404e786e05  3-MANAGER-SPOOFED_KernelSU-Next_v3.4.2-50-gb427a3f9_33405.apk
aeae97436cf3c83f032d4d2a837581cd51b56c93eaf952e459f358d20ce39931  4-NOMOUNT-MODULE_v2.1.1.zip
73f6d9c9a167d1528057ff84c65d6db371a5cde63e1435ca6e5e4f14bfc367d5  Cogan-Smart-Kernel-v2.8.2.zip
441e0780d77480f6642a84f5478ce61d659110a640ca6b025f51d2c718ce594f  Cogan-Smart-Kernel-v2.8.1.zip
```

---

## 🙏 Credits

| Who | Contribution |
|---|---|
| **Cogan17** | Maintainer: Cogan Rothko kernel, Cogan Bridge, Cogan Smart Kernel module, build engine, CI and releases |
| **[Google](https://android.googlesource.com/kernel/common/)** | Android Common Kernel `android14-6.1` (source of the rothko stock kernel), BBRv3 |
| **Xiaomi & MediaTek** | rothko BSP source (symbol and config reference), vendor modules and firmware; property of their owners |
| **[KernelSU](https://github.com/tiann/KernelSU)** (tiann) | The base of in-kernel root |
| **[KernelSU Next](https://github.com/KernelSU-Next/KernelSU-Next)** (rifsxd) | The KernelSU Next root variant; the manager app in releases is the official CI build |
| **[pershoot](https://github.com/pershoot/KernelSU-Next)** | KernelSU Next fork `dev-susfs` that joins KernelSU Next with SUSFS |
| **[BakaSU](https://github.com/Baka-SU/BakaSU)** | The BakaSU root variant (formerly ReSukiSU) |
| **[SUSFS](https://gitlab.com/simonpunk/susfs4ksu)** (simonpunk) | Hides root traces |
| **[NoMount](https://github.com/maxsteeel/nomount)** (maxsteeel) | Mountless metamodule, built into the kernel; the module in releases is its official release |
| **[Baseband Guard](https://github.com/vc-teahouse/Baseband-guard)** (vc-teahouse) | Partition protection |
| **[AnyKernel3](https://github.com/osm0sis/AnyKernel3)** (osm0sis) | Kernel ZIP installer |
| **[Neutron Clang](https://github.com/Neutron-Toolchains)** | Kernel compiler |
| **[Kernel Flasher](https://github.com/fatalcoder524/KernelFlasher)** (fatalcoder524) | Flashing and `boot` backup app |
| **[WildKernels](https://github.com/WildKernels/GKI_KernelSU_SUSFS)** | Inspiration for the build workflow form |
| **GKI-Duchamp · AK3-GKID** (Ahmed Al-Nassif) | Base of the early kernel experiments (no longer used) |
| **[cogan17/Cogan](https://github.com/cogan17/Cogan)** | Origin of the build engine |

Sister project: **[TWRP Xiaomi 14T Pro](https://github.com/cogan17/TWRP-14T-PRO)** · predecessor repository: **[Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro)**.

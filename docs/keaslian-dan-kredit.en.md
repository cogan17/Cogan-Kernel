# 🔏 Authenticity & Credits

[← Back to README](../README.en.md) · <img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> [Bahasa Indonesia](keaslian-dan-kredit.md)

The Cogan kernel for the Xiaomi 14T Pro (`rothko`) is built automatically by GitHub Actions in **[cogan17/Cogan-Kernel](https://github.com/cogan17/Cogan-Kernel)** (named `Xiomi_14T_Pro` until 24 Oct 2026; GitHub redirects the old links). The build workflow of this repository **digitally signs** the kernel ZIP (artifact attestation), so anyone can prove where it came from.

This repository continues **[cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro)**. The old releases of that repository are copied here as an **archive** (see [Release archive](#-release-archive)). The archived files are unchanged to the bit: same SHA256, still signed in the name of their original repository.

> What is proven is that **this rothko kernel build** was made by Cogan17. The Linux kernel, the Android Common Kernel and the features inside are the work of the contributors under [Credits](#-credits).

---

## How to check authenticity

1. **Proof page:** [github.com/cogan17/Cogan-Kernel/attestations](https://github.com/cogan17/Cogan-Kernel/attestations) for builds of this repository; [github.com/cogan17/Kernel-14t-pro/attestations](https://github.com/cogan17/Kernel-14t-pro/attestations) for the archived releases.
2. **With the GitHub CLI:**
   ```
   gh attestation verify <zip> --repo cogan17/Cogan-Kernel     # builds of this repository after the rename (24 Oct 2026)
   gh attestation verify <zip> --repo cogan17/Xiomi_14T_Pro    # r1, r2 and other builds before the rename
   gh attestation verify <zip> --repo cogan17/Kernel-14t-pro   # archived releases r5, r6, r8 (arsip-… tags)
   ```
   Only a genuine ZIP passes. A signature keeps the repository name at build time, so r1 and r2 still name `Xiomi_14T_Pro` (the same repository, before the rename). `--owner cogan17` accepts all three.
3. **The run page in [Actions](https://github.com/cogan17/Cogan-Kernel/actions):** every build shows the KMI gate result, the version of every component, the feature list and the sha256 of its ZIP.
4. **On the phone** (Termux / root manager terminal):
   ```
   su -c cat /sys/kernel/cogan/banner
   ```
   Shows the real version, the builder and the build date. The file comes from **Cogan Bridge** inside the kernel, so SUSFS does not mask it.
5. **Cogan Smart Kernel module:** any tab → Kernel card → **"Real identity · verified"** and **"✓ kernel built for this phone"**.
6. **Other files in a release** (manager, NoMount, Cogan Smart Kernel module) are not signed. Compare their SHA256 with the release's `checksums.txt` (Cogan Smart module: the table in the [module README](../modules/cogan-smart/README.md)).

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

The old releases of [cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro/releases) (archive r5, r6, r8) are copied unchanged to this repository's [Releases](https://github.com/cogan17/Cogan-Kernel/releases): their titles start with **📦 Arsip** and the kernel tags with `arsip-`. Each release carries its own notes, `checksums.txt` and the signature of its original repository. Cogan Smart Kernel module releases and their SHA256 are in the [module README](../modules/cogan-smart/README.md).

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
| **[WildKernels](https://github.com/WildKernels/GKI_KernelSU_SUSFS)** | Inspiration for the build workflow form and Validate; the optional Unicode fix patch from [kernel_patches](https://github.com/WildKernels/kernel_patches) |
| **GKI-Duchamp · AK3-GKID** (Ahmed Al-Nassif) | Base of the early kernel experiments (no longer used) |
| **[cogan17/Cogan](https://github.com/cogan17/Cogan)** | Origin of the build engine |

Sister project: **[TWRP Xiaomi 14T Pro](https://github.com/cogan17/TWRP-14T-PRO)** · predecessor repository: **[Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro)**.

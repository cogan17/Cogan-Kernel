# 📝 Release Notes

[← Back to README](README.en.md) · <img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> [Bahasa Indonesia](CHANGELOG.md)

Topmost = newest build. Builds that pass the phone test are published as a **Pre-release** in [Releases](https://github.com/cogan17/Cogan-Kernel/releases); there is no official release yet.

> 📦 r2–r8 and the early experiments were made in the predecessor repository [cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro). Releases r5, r6 and r8 are copied to this repository's Releases as an archive with the same files. Here they are named **archive r5, archive r6, archive r8** and their tags start with `arsip-` (e.g. `arsip-v26.10.22-r5`), so they never clash with this repository's own release numbers.

## r2 — 24 Oct 2026 · `6.1.176-Cogan-Rothko-ACK-r2` · [Pre-release](https://github.com/cogan17/Cogan-Kernel/releases/tag/v26.10.24-r2)

**KernelSU Next + SUSFS** on the official Google ACK 6.1.176 (`android14-6.1-2026-09_r4`), as in r1, plus the Unicode fix.

### ✨ New
- **Unicode fix** (WildKernel `fa76c90`): file names with invisible characters (e.g. zero-width) on internal storage no longer count as the same name without them. An optional Builder box, off by default; r2 was built with it ticked.

Other components are the same as r1: KernelSU Next `d21e0a6` (33405), SUSFS v2.3.0 (`c27ebe9`), NoMount v2.2.0.

Status: ✅ passed the owner's phone test (24 Oct): kernel `6.1.176-Cogan-Rothko-ACK-r2-35f0a136c` runs with the Unicode fix installed. Test in `/data/media/0`: `UJI.txt` still finds `uji.txt` (case-insensitive storage), but `u`+U+200B+`ji.txt` now gives `No such file or directory`. KMI gate: 0 differing symbols.

## r1 — 24 Oct 2026 · `6.1.176-Cogan-Rothko-ACK-r1` · [Pre-release](https://github.com/cogan17/Cogan-Kernel/releases/tag/v26.10.23-r1)

This repository's first release: **KernelSU Next + SUSFS** on the official Google ACK 6.1.176 (`android14-6.1-2026-09_r4`), with the newest components at build time.

### ✨ New
- **KernelSU Next** root (`d21e0a6`, 33405) + **SUSFS v2.3.0** (`c27ebe9`). Regular and *spoofed* managers, version 33405.
- **NoMount v2.2.0**: the kernel driver and the module in the release are the same version.

### 🔧 Fixed
- The AnyKernel3 flasher tools are now **arm64**. The r1 ZIP from the first build was not released: its tools were 32-bit (`magiskboot: syntax error`), and flashing stopped before `boot` was written.

Status: ✅ passed the owner's phone test (KernelSU Next works, SUSFS v2.3.0, NoMount v2.2.0, SELinux Enforcing; 24 Oct). KMI gate: 0 differing symbols.

## archive r8 — 23 Oct 2026 · `6.1.176-Cogan-Rothko-ACK-r8` · [Pre-release](https://github.com/cogan17/Cogan-Kernel/releases/tag/arsip-v26.10.23-r8)

The **BakaSU + SUSFS** variant on the official Google ACK 6.1.176. The KernelSU Next variant stays archive r6.

### ✨ New
- **BakaSU** root `v4.2.0-rc3-5b76b884` (35222) + **SUSFS v2.3.0** (`2474336`). The kernel driver and the manager have the same version, 35222.

### ⏳ Waiting for BakaSU
- The BakaSU developer has blocked SUSFS builds since 10 Oct. This kernel uses the version from before the block until it is lifted; the next build then moves to the newest BakaSU.
- r7 was not released: its manager turned out to still be named ReSukiSU (rc3, before the project was renamed).

Status: ✅ passed the owner's phone test (BakaSU working, SUSFS v2.3.0, SELinux Enforcing; 23 Oct). KMI gate: 0 differing symbols.

## archive r6 — 22 Oct 2026 · `6.1.176-Cogan-Rothko-ACK-r6` · [Pre-release](https://github.com/cogan17/Cogan-Kernel/releases/tag/arsip-v26.10.22-r6)

Built from the **official Google ACK `android14-6.1-2026-09_r4` (6.1.176)**, the newest ACK release, instead of the phone's stock 6.1.138.

### ✨ New
- Kernel **6.1.176**. The builder can now pick every official android14-6.1 ACK release since the phone's stock kernel: 138, 141, 145, 157, 162, 172 and 176.

### 🔧 Fixed
- Kernel symbols now **match exactly** what the phone's vendor modules use: the KMI gate records 0 differing symbols (archive r5: 2, r3: 538). BBRv3 stays enabled.

Status: ✅ boots, and the owner's phone checks are fine (22 Oct).

## archive r5 — 22 Oct 2026 · `6.1.138-Cogan-Rothko-ACK-r5` · [Pre-release](https://github.com/cogan17/Cogan-Kernel/releases/tag/arsip-v26.10.22-r5)

### 🔧 Fixed
- The kernel's KernelSU Next version is now **33405**, the same as the official CI manager `v3.4.2-50-gb427a3f9`, so the manager no longer asks for an update (r4: 33418).
- The release package carries the regular and *spoofed* managers (33405) and the NoMount v2.1.1 module.

Status: ✅ passed the phone test (KernelSU Next working, SUSFS v2.3.0, SELinux Enforcing). The proven 6.1.138 fallback.

## r4 — 22 Oct 2026 · `6.1.138-Cogan-Rothko-ACK-r4`

### ✨ New
- Newest SUSFS and KernelSU Next (pershoot `dev-susfs` fork).
- Signed kernel ZIP (GitHub attestation).

### 🔧 Fixed
- Symbols that differ from the stock kernel dropped from 538 to 2: BBRv3's structure changes are no longer visible to the vendor modules.

Status: ✅ passed the phone test (Wi-Fi, camera, SUSFS; "no bugs").

## r3 — 22 Oct 2026 · `6.1.138-Cogan-Rothko-ACK-r3`

### ✨ New
- **Cogan Bridge** inside the kernel (`/sys/kernel/cogan`): the real kernel identity behind the SUSFS disguise, the target device (`rothko`) and the SoC from the device tree, the Cogan Smart module heartbeat, and CPU limits released automatically when the module stops.
- The device, the kernel and the **Cogan Smart Kernel** module recognise each other: the WebUI shows "✓ kernel dibuat untuk HP ini" (kernel built for this phone).

Status: 🔄 3-day test on the maintainer's phone.

## r2 — 17 Oct 2026 · `6.1.138-Cogan-Rothko-ACK-r2`

The first build from the **rothko stock kernel** (ACK `android14-6.1-2025-06_r11`), for HyperOS `OS3.0.301.0.WNNIDXM`.

### ✨ New
- Built-in **KernelSU Next** + **SUSFS** v2.3.0.
- **NoMount**, **Baseband Guard**, **BBRv3** as the default TCP, Full LTO.
- KMI gate: every build is checked against the stock kernel ABI; a failure means no ZIP.
- AnyKernel3 ZIP with a device check (`rothko` only).

### 🔧 Known
- Vendor modules load through *force-load* (many `disagrees about version of symbol` lines in `dmesg`). Fixed in a later revision.

Status: ✅ passed the 3-stage phone test (boot, root, all hardware, 120W charging, gaming, reboots, overnight).

## Early experiment — 16 Oct 2026 · GKID `6.1.177`

A kernel from GKI-Duchamp (GKID) booted on rothko. It was then replaced by the stock kernel source to match the HyperOS vendor modules as closely as possible.

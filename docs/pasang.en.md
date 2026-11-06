# 📥 Install the Kernel

[← Back to README](../README.en.md) · <img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> [Bahasa Indonesia](pasang.md)

The Cogan kernel replaces only the **`boot`** partition. Data, `init_boot` and `vendor_boot` are not touched.

---

## Before you start

- The bootloader is **unlocked**.
- HyperOS **`OS3.0.302.0.WNNIDXM`** (Android 16, tested with r12) or **`OS3.0.301.0.WNNIDXM`**, the versions used for testing. The kernel is built from the official Google android14-6.1 ACK: archive r8 and r6 from 6.1.176 (`2026-09_r4`), archive r5 from 6.1.138 (the same as this HyperOS version's stock kernel).
- The kernel ZIP `1-KERNEL_Cogan-Rothko-ACK-…zip`. It carries a device check, so on a phone other than `rothko` the flash stops before `boot` is touched.

## 1. Back up `boot` first

Pick one way:

- **Kernel Flasher** → active slot → **Backup** → `boot`.
- **TWRP** → **Backup** → tick **Boot**.

Copy the result to a **PC or USB drive**, not only the phone. Also keep the **stock** `boot.img` from the same HyperOS ROM version.

## 2. Flash

**With Kernel Flasher (needs root):**

1. Open [Kernel Flasher](https://github.com/fatalcoder524/KernelFlasher) → active slot → **Flash** → **Flash AK3 Zip**.
2. Pick the kernel ZIP, wait for it to finish, then **Reboot**.

**With TWRP:**

1. Enter TWRP, then **Install** → pick the kernel ZIP → swipe.
2. **Reboot → System.**

## 3. After it boots

1. Install the root manager app from the same release package (**KernelSU Next** or **BakaSU**, matching the kernel ZIP), then the **NoMount** metamodule.
   If the kernel ZIP is named `…+SuSFS…` and you want to configure SUSFS, also install the **SUSFS module** `5-SUSFS-MODULE-SIDEX15_…zip`: sidex15's module with WebUI (its newest CI build), which installs the `ksu_susfs` tool. Releases from 26–28 Oct 2026 also hold simonpunk's module (`5-…SIMONPUNK`) and number sidex15's module `6-`; install only one of them.
2. *Optional:* the **[Cogan Smart Kernel](https://github.com/cogan17/Cogan-Kernel/blob/main/modules/cogan-smart/README.md)** module. Its development is parked (bug fixes only); the kernel runs normally without it. If you install it, reboot once, then check the module WebUI: **"Identitas asli · terverifikasi"** (real identity, verified) and **"✓ kernel dibuat untuk HP ini"** (kernel built for this phone).
3. *Optional, to disguise the kernel from detector apps:* open the SUSFS module WebUI → **Kernel Uname**, then enter the stock kernel values for your HyperOS version (Settings → About phone; read from the rothko stock `boot.img`). Tick the boxes next to **Spoof Kernel Version** and **Spoof Kernel Build**.
   - **HyperOS `OS3.0.302.0.WNNIDXM`** (October 2026 security patch):
     - Spoof Kernel Version:
       ```
       6.1.157-android14-11-g0baf70f2581d-ab15659624
       ```
     - Spoof Kernel Build:
       ```
       #1 SMP PREEMPT Tue Jun 16 21:49:26 UTC 2026
       ```
   - **HyperOS `OS3.0.301.0.WNNIDXM`**:
     - Spoof Kernel Version:
       ```
       6.1.138-android14-11-g6ab8c9a86a33-ab14396278
       ```
     - Spoof Kernel Build (there are **two spaces** before `5`):
       ```
       #1 SMP PREEMPT Wed Nov  5 15:47:39 UTC 2025
       ```
   - Keep **Spoof on boot** and **Execute on post-fs-data** ticked, then reboot.
   - Check in Termux **without** `su`: `uname -a` must show both values above exactly.

   Normal apps can only read `uname`, so the kernel looks exactly like the stock kernel. Proven on the owner's phone (2 Nov 2026): Duck Detector **Kernel Check: No suspicious kernel markers**. These values belong to the current HyperOS stock kernel; if a HyperOS update changes the stock kernel, the values change too. This does not hide KernelSU's own traces (e.g. the SELinux `ksu` type), which can still be detected.

   **How to see the real kernel** (Termux; type them one by one, allow root when asked):

   | Command | What it shows |
   |---|---|
   | `su -c cat /sys/kernel/cogan/banner` | The real Cogan identity: kernel version, release number (e.g. `r33`), builder and build date. The surest check, never spoofed |
   | `su -c cat /proc/version` | The kernel version actually running (e.g. `6.1.176`, not the spoofed value) |
   | `uname -a` (without `su`) | What normal apps see: the spoofed value above (e.g. `6.1.157-android14-11-g0baf70f2581d-ab15659624`) |

   If the first shows Cogan, the second the real version, and `uname -a` shows that spoofed value, everything works: the real kernel is Cogan, apps see the stock kernel.

> 💡 The kernel version in Settings may look different (e.g. `6.1.157`). That is SUSFS spoofing `uname`. The Cogan Smart module reads the real identity through Cogan Bridge.

---

Bootloop? See **[Back to Stock](kembali-ke-stok.en.md)**.

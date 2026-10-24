# 📥 Install the Kernel

[← Back to README](../README.en.md) · <img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> [Bahasa Indonesia](pasang.md)

The Cogan kernel replaces only the **`boot`** partition. Data, `init_boot` and `vendor_boot` are not touched.

---

## Before you start

- The bootloader is **unlocked**.
- HyperOS **`OS3.0.301.0.WNNIDXM`** (Android 16), the version used for testing. The kernel is built from the official Google android14-6.1 ACK: archive r8 and r6 from 6.1.176 (`2026-09_r4`), archive r5 from 6.1.138 (the same as this HyperOS version's stock kernel).
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
2. *Optional:* the **[Cogan Smart Kernel](https://github.com/cogan17/Cogan-Kernel/blob/main/modules/cogan-smart/README.md)** module. Its development is parked (bug fixes only); the kernel runs normally without it. If you install it, reboot once, then check the module WebUI: **"Identitas asli · terverifikasi"** (real identity, verified) and **"✓ kernel dibuat untuk HP ini"** (kernel built for this phone).

> 💡 The kernel version in Settings may look different (e.g. `6.1.170`). That is SUSFS spoofing `uname`. The Cogan Smart module reads the real identity through Cogan Bridge.

---

Bootloop? See **[Back to Stock](kembali-ke-stok.en.md)**.

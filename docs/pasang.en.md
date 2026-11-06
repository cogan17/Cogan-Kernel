# 📥 Install the Kernel

[← Back to README](../README.en.md) · <img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> [Bahasa Indonesia](pasang.md)

The Cogan kernel replaces only the **`boot`** partition. Data, `init_boot` and `vendor_boot` are not touched.

---

## Before you start

- The bootloader is **unlocked**.
- **Write down your phone's stock kernel version before flashing**: Settings → About phone → Kernel version. It changes after flashing, and you need it again in step 3 (disguise the kernel).
- This kernel is for the Xiaomi 14T Pro (`rothko`) **from any region** (Indonesia, Global, EEA, Turkey, …), as long as its stock kernel version is one of these:

  | Stock kernel version | HyperOS |
  |---|---|
  | `6.1.157-android14-11-g0baf70f2581d-ab15659624` | `OS3.0.302` |
  | `6.1.138-android14-11-g6ab8c9a86a33-ab14396278` | `OS3.0.301` |

  Both are HyperOS 3 based on **Android 16** (the letter `W` in the ROM code, e.g. `OS3.0.301.0.WNNIDXM`). The word `android14` in the kernel version is not the phone's Android version but the GKI kernel generation (`android14-6.1`) Google uses for Android 14 to 16.

  Every build is checked against both stock kernels. Phone tests were done on the Indonesian ROM (`OS3.0.302.0.WNNIDXM` and `OS3.0.301.0.WNNIDXM`). Other regions' ROMs carry the same stock kernel when the version matches exactly. **If your stock kernel version is different, do not flash yet**: send it to the Telegram group so that stock kernel can be added to the build check.
- The kernel is built from the official Google android14-6.1 ACK.
- The kernel ZIP `1-KERNEL_Cogan-Rothko-ACK-…zip`. It carries a device check, so on a phone other than `rothko` the flash stops before `boot` is touched.

## 0. Install root first (if you don't have root yet)

The Cogan kernel is flashed with **Kernel Flasher**, which needs root, so **root must come first**. Just unlocking the bootloader (UBL) does not give you root. Skip this section if the phone already has root (e.g. moving from another kernel).

The first root goes on the **`init_boot`** partition, not `boot`, in **LKM mode**: the root manager app puts the KernelSU module into `init_boot`, on top of the stock kernel. This root is temporary, to give Kernel Flasher access. Once the Cogan kernel is installed, root is **built into the kernel** (GKI mode).

On the PC you need: Google's official **platform-tools** (`adb`/`fastboot`), the **Xiaomi USB driver** (installed when you open MiFlash) and a USB cable. Use a **KernelSU** root manager (KernelSU Next/CoganSU), **not Magisk**: the Cogan kernel already carries KernelSU, and two roots at once can clash.

1. Install the root manager app (**KernelSU Next** or **CoganSU**) from the release package.
2. Get the **stock** `init_boot.img` from the same HyperOS ROM version as the phone. Keep a spare copy.
3. In the root manager app → **Install** menu → **Select and patch a file** → pick `init_boot.img`. It produces `init_boot_patched.img` (or similar) in the `Download` folder.
4. Copy `init_boot_patched.img` to the PC. Enter fastboot mode: `adb reboot bootloader` (or power off, then hold **Volume Down + Power**).
5. Flash: `fastboot flash init_boot init_boot_patched.img`, then `fastboot reboot`.
6. Once it boots, open the root manager app → confirm it shows **installed / working** and reads the kernel version. Root is active.

> ⚠️ Do not `fastboot flash boot` with an `init_boot` file, or vice versa. The wrong partition can bootloop.
> Failed or bootloop? Flash the **stock** `init_boot` back: `fastboot flash init_boot init_boot.img`. The `boot` partition and data are untouched in this step.

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
   If the kernel ZIP is named `…+SuSFS…` and you want to configure SUSFS, also install the **SUSFS module** `5-SUSFS-MODULE-SIDEX15_…zip`: sidex15's module with WebUI (its newest CI build), which installs the `ksu_susfs` tool. Releases from 26–28 Oct 2026 also hold simonpunk's module (`5-…SIMONPUNK`) and number sidex15's module `6-`; install only one of them. The [BRENE](https://github.com/rrr333nnn333/BRENE) module is also a SUSFS module: install sidex15's **or** BRENE, not both (BRENE disables other SUSFS modules).
2. *Optional:* the **[Cogan Smart Kernel](https://github.com/cogan17/Cogan-Kernel/blob/main/modules/cogan-smart/README.md)** module. Its development is parked (bug fixes only); the kernel runs normally without it. If you install it, reboot once, then check the module WebUI: **"Identitas asli · terverifikasi"** (real identity, verified) and **"✓ kernel dibuat untuk HP ini"** (kernel built for this phone).
3. *Optional, to disguise the kernel from detector apps:* open the SUSFS module WebUI → **Kernel Uname**, then enter the values matching the stock kernel version you wrote down before flashing (read from the rothko stock `boot.img`). Tick the boxes next to **Spoof Kernel Version** and **Spoof Kernel Build**.
   - **Stock kernel `6.1.157`** (HyperOS `OS3.0.302`):
     - Spoof Kernel Version:
       ```
       6.1.157-android14-11-g0baf70f2581d-ab15659624
       ```
     - Spoof Kernel Build:
       ```
       #1 SMP PREEMPT Tue Jun 16 21:49:26 UTC 2026
       ```
   - **Stock kernel `6.1.138`** (HyperOS `OS3.0.301`):
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

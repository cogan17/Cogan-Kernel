# ↩️ Back to Stock

[← Back to README](../README.en.md) · <img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> [Bahasa Indonesia](kembali-ke-stok.md)

Want the stock kernel back, or is the phone bootlooping after a flash? **Data is not wiped.** Restoring the **`boot`** partition is enough.

---

## The phone still boots

- **Kernel Flasher** → active slot → **Restore** → pick your `boot` backup, then reboot.
- Or **TWRP** → **Install → Install Image** → pick the backup/stock `boot.img` → **boot** → swipe → **Reboot → System**.

## The phone bootloops (stuck on the Mi logo)

**Caused by a module, not the kernel?** Try this first:

1. Force it off: hold **Power ~15 seconds**.
2. Turn it on. After the first boot screen, press **Volume Down more than 3 times** (press and release, do not hold).
3. KernelSU enters *safe mode*: every module is disabled. Remove the bad module in the root manager app (KernelSU Next or BakaSU), then reboot.

**Caused by the kernel** (or safe mode does not help):

1. Hold **Power + Volume Down** → **FASTBOOT**.
2. Connect to a PC and run:
   ```
   fastboot flash boot boot.img
   fastboot reboot
   ```
   `boot.img` = your backup from before the flash, or the stock `boot.img` from the **exact same** HyperOS ROM version.
3. Have TWRP? **Install → Install Image → boot** works without a PC.

This kernel never touches the bootloader, so FASTBOOT is always reachable.

---

## ⛔ Never

- Run **`flash_all_lock`** from a fastboot ROM. Locking the bootloader with modified partitions can hard-brick the phone.
- Flash a ROM **older** than the installed one. Xiaomi's anti-rollback can hard-brick the phone.
- Flash `boot.img` to another partition (`init_boot`, `vendor_boot`, …).
- Use SP Flash Tool / BROM mode. It can wipe the modem/IMEI calibration.

Still bootlooping with the stock `boot.img`? Flash the official fastboot ROM of the same version with **`flash_all_except_storage`** (data is kept).

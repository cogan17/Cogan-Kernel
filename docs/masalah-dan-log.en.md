# 🩺 Issues & Logs

[← Back to README](../README.en.md) · <img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> [Bahasa Indonesia](masalah-dan-log.md)

Something wrong? Collect the logs below, then report on **[Issues](https://github.com/cogan17/Xiomi_14T_Pro/issues)** or the **[Telegram Community](https://t.me/coganTWRP)** with the kernel version (`r…`), the HyperOS version and what happened.

---

## Collect logs

Run in Termux or the root manager's terminal (KernelSU Next or BakaSU):

| Log | Command |
|---|---|
| Current kernel log | `su -c dmesg > /sdcard/Download/dmesg.txt` |
| Real kernel identity | `su -c cat /sys/kernel/cogan/release /sys/kernel/cogan/features` |
| Kernel log of the previous failed boot (if present) | `su -c 'cat /sys/fs/pstore/console-ramoops* > /sdcard/Download/last_kmsg.txt'` |

For a failed boot: recover the phone first ([Back to Stock](kembali-ke-stok.en.md)), then collect the log above **before** rebooting again.

**Cogan Smart Kernel** module:

- **🌡️ Suhu** (temperature) tab → **Simpan log** (saved in `Download/CoganThermal`).
- **🧩 Modul** tab → screenshot the module list and its flags.

## Common issues

| Symptom | Explanation |
|---|---|
| The kernel version in Settings is not `6.1.138` (e.g. `6.1.170`) | Normal: SUSFS spoofs `uname`. The real identity is in the Cogan Smart WebUI or `/sys/kernel/cogan/release` |
| The flash stops with *Unsupported device* | The ZIP is for `rothko` only; other phones are refused before `boot` is touched |
| Many `disagrees about version of symbol` lines in `dmesg` | Known: vendor modules load through *force-load*. Fixed in a later kernel revision |
| Every KernelSU module is off after a bootloop | KernelSU safe mode. Turn them back on in the root manager app → Modules, then reboot |

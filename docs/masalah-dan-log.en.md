# 🩺 Issues & Logs

[← Back to README](../README.en.md) · <img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> [Bahasa Indonesia](masalah-dan-log.md)

Something wrong? Collect the logs below, then report on **[Issues](https://github.com/cogan17/Cogan-Kernel/issues)** or the **[Telegram Community](https://t.me/coganTWRP)** with the kernel version (`r…`), the HyperOS version and what happened.

---

## Collect logs

Run in Termux or the root manager's terminal (KernelSU Next or BakaSU):

| Log | Command |
|---|---|
| Current kernel log | `su -c dmesg > /sdcard/Download/dmesg.txt` |
| Real kernel identity | `su -c cat /sys/kernel/cogan/identity /sys/kernel/cogan/release /sys/kernel/cogan/features` |
| Kernel log of the previous failed boot (if present) | `su -c 'cat /sys/fs/pstore/console-ramoops* > /sdcard/Download/last_kmsg.txt'` |

For a failed boot: recover the phone first ([Back to Stock](kembali-ke-stok.en.md)), then collect the log above **before** rebooting again.

> 🔒 **Check the log before sharing it.** A kernel log can hold the arguments of a command Baseband Guard refused (lines `baseband_guard: deny … argv="…"`), serial numbers, MAC addresses or Wi-Fi names. Remove or mask them before posting to Issues or the group. Since 7 Nov 2026 the kernel log can be read only with root (`dmesg_restrict = 1`), so the commands above keep using `su`.

**Cogan Smart Kernel** module:

- **🌡️ Suhu** (temperature) tab → **Simpan log** (saved in `Download/CoganThermal`).
- **🧩 Modul** tab → screenshot the module list and its flags.

## Common issues

| Symptom | Explanation |
|---|---|
| The kernel version in Settings differs from the Cogan kernel version (e.g. `6.1.138`) | Normal: SUSFS spoofs `uname`. The real identity is in the Cogan Smart WebUI or `/sys/kernel/cogan/release` |
| The flash stops with *Unsupported device* | The ZIP is for `rothko` only; other phones are refused before `boot` is touched |
| `disagrees about version of symbol` lines in `dmesg` | Should not appear: since 7 Nov 2026 the build stops when a KMI symbol's CRC differs from the stock kernel. If it appears, report it with the full log (masked) |
| Every KernelSU module is off after a bootloop | KernelSU safe mode. Turn them back on in the root manager app → Modules, then reboot |

## Release from run fails with HTTP 403

The built-in `GITHUB_TOKEN` cannot tag a commit whose `.github/workflows/` files differ from the commit running **Rilis dari run** (`HTTP 403: Resource not accessible by integration`, [GitHub Docs](https://docs.github.com/en/rest/releases/releases#create-a-release)). Since 24 Oct 2026 the workflow checks this itself: with the same workflows the tag points to the build commit; otherwise it points to the `main` commit running the release. The release files are still that build's files (SHA256 checked), and the notes link its build run. No PAT, GitHub App or secret is needed.

Start **Rilis dari run → Run workflow** from `main`; do not choose **Re-run jobs** on an old run: a rerun uses the workflow of the old commit.

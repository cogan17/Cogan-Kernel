<h1 align="center">Cogan Kernel · Xiaomi 14T Pro</h1>

<p align="center">
  <code>rothko</code> &nbsp;·&nbsp; HyperOS &nbsp;·&nbsp; Android 16 &nbsp;·&nbsp; Linux 6.1 GKI
</p>

<p align="center">
  <a href="README.md"><img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> Bahasa Indonesia</a> &nbsp;·&nbsp; <b><img src="https://flagcdn.com/24x18/gb.png" width="22" alt=""> English</b>
</p>

<p align="center">
  <a href="https://github.com/cogan17/Cogan-Kernel/releases"><b>⬇️ Download Kernel</b></a>
  &nbsp;·&nbsp;
  <a href="docs/pasang.en.md"><b>📖 Guide</b></a>
  &nbsp;·&nbsp;
  <a href="CHANGELOG.en.md"><b>📝 Release Notes</b></a>
  &nbsp;·&nbsp;
  <a href="modules/cogan-smart/README.md"><b>🧠 Cogan Smart Module</b></a>
  &nbsp;·&nbsp;
  <a href="https://t.me/coganTWRP"><b>💬 Telegram Community</b></a>
</p>

> [!WARNING]
> The maintainer/developer is not responsible for bootloops or bricked devices. Device owners are responsible for their own devices! Please back up your data.

> [!TIP]
> TWRP is available for the Xiaomi 14T Pro. You can download [TWRP](https://github.com/cogan17/TWRP-14T-PRO).

---

### 📖 User Guide

|   |   |
|---|---|
| 📥 **[Install the Kernel](docs/pasang.en.md)** | Back up `boot`, then flash with Kernel Flasher or TWRP |
| 🧠 **[Cogan Smart Module](modules/cogan-smart/README.md)** | Power modes, temperature, module guard |
| ↩️ **[Back to Stock](docs/kembali-ke-stok.en.md)** | Undo the kernel / fix a bootloop |
| 🩺 **[Problems & Logs](docs/masalah-dan-log.en.md)** | If something goes wrong |

---

<details>
<summary>📱 <b>Device specifications</b></summary>

| Item | Detail |
|---|---|
| Chipset | MediaTek Dimensity 9300+ (MT6989) |
| CPU | 4× Cortex-X4 up to 3.4 GHz |
| GPU | Immortalis-G720 MC12 |
| RAM | 12 / 16 GB |
| Display | 1220 × 2712 |
| Released | September 2024 (Android 14) |
| Stock kernel | `6.1.138-android14-11` (HyperOS `OS3.0.301.0.WNNIDXM`) |

</details>

<details>
<summary>✨ <b>What's inside</b></summary>

- ✅ Google's official kernel source (Android Common Kernel `android14-6.1`), the same family as the phone's stock kernel. Xiaomi/MediaTek vendor modules still fit
- ✅ Always the newest versions: the ACK release, root manager, SUSFS and NoMount are taken at their newest at build time. When something does not fit yet, the build summary names the developer to wait for
- ✅ In-kernel root + **SUSFS**, two variants: **KernelSU Next** or **BakaSU**
- ✅ **NoMount** (mountless modules, built into the kernel), **Baseband Guard**
- ✅ **BBRv3** as the default TCP (`bbr` and `bbr3`)
- ✅ **Cogan Bridge**: the kernel and the Cogan Smart module know each other (`/sys/kernel/cogan`)
- ✅ Full LTO, device check in the ZIP (`rothko` only)
- ⚙️ Optional, off by default: **Unicode fix** (WildKernel). File names with invisible characters (e.g. zero-width) on internal storage no longer count as the same name without them (the *unicode bypass* gap used to find hidden paths)
- ✅ Every build is checked automatically against the stock kernel ABI (KMI gate); failure = no ZIP

</details>

<details>
<summary>🧩 <b>Supported sublevels</b></summary>

The builder uses the official ACK `android14-6.1` releases since the phone's stock kernel; `lts` = the newest. The **Catat sublevel** (record sublevels) workflow button records the latest build in this table (✅ passed the build and the KMI gate, ⏳ waiting for an upstream update); it neither checks nor builds.

The **Cek pembaruan** (check for updates) button is the only check, and it builds nothing: the newest version of every component (ACK, KernelSU Next, BakaSU, simonpunk's SUSFS and sidex15's SUSFS module, NoMount, Baseband Guard, AnyKernel3, Neutron clang, Unicode fix) against the last build, with the dates of the stable and CI versions, what is new and fixed, and whom to wait for when it cannot be built yet. When something is newer, the summary suggests running the Builder.

**[Build history](kernel/history/)** is saved automatically by the Builder as Markdown documents. **Last build** and **Status** remain comparable after Actions logs, artifacts or runs are deleted; **Delete old run logs** works as before.

<!-- sublevel:start -->
| Sublevel | ACK release | Status |
|---|---|---|
| **176** (`lts`) | `2026-09_r5` | ✅ KernelSU Next · BakaSU: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/40276957002) · r1 and r2 tested on the phone |
| 172 | `2026-06_r14` | ✅ KernelSU Next: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498) |
| 162 | `2026-03_r24` | ✅ KernelSU Next: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498) |
| 157 | `2025-12_r32` | ✅ KernelSU Next: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498) |
| 145 | `2025-09_r36` | ✅ KernelSU Next: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/40061712549) |
| 138 | `2025-06_r17` | ✅ KernelSU Next: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/40061712549) · the phone's stock kernel; archive r5 tested on the phone |
<!-- sublevel:end -->

Unicode fix (optional) passes the build + KMI gate on 157, 162, 172 and 176, and applies cleanly on 138 and 145 ([CI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498)). If WildKernel's patch does not fit yet, the build stops: untick Unicode fix to build anyway.

To publish an existing build, run **Rilis dari run** with the green Builder run ID. A run containing KernelSU Next and BakaSU becomes **one release** with both kernel ZIPs and their matching manager APKs, without rebuilding. Tick **diuji di HP** only if the owner tested every variant in that run on the phone.

Release notes include **What's New & Fixes**, compared with the previous release of the same root manager. The run's **Summary** provides **one Telegram post ready to copy** for the whole release (KernelSU Next and BakaSU in one text) in Indonesian and English, each in a code block with a copy button. Tick **teks_saja** to generate only notes and Telegram posts, including for an already published version; this mode does not publish or change a release.

</details>

<details>
<summary>🧪 <b>Test status</b></summary>

| Build | Result |
|---|---|
| `r2` (ACK 6.1.176 · KernelSU Next · Unicode fix) | ✅ Tested on the phone 24 Oct: Unicode fix works (a name with a zero-width space no longer matches the real file) |
| `r1` (ACK 6.1.176 · KernelSU Next) | ✅ Tested on the phone 24 Oct: KernelSU Next works, SUSFS v2.3.0, NoMount v2.2.0, SELinux Enforcing |
| `archive r8` (ACK 6.1.176 · BakaSU) | ✅ Tested on the phone 23 Oct: BakaSU works, SUSFS v2.3.0, SELinux Enforcing |
| `archive r6` (ACK 6.1.176 · KernelSU Next) | ✅ Tested on the phone 22 Oct |
| `archive r5` (ACK 6.1.138 · KernelSU Next) | ✅ Tested on the phone; the proven fallback |

`r1` and `r2` are this repository's releases; the other three are archived releases from the predecessor repository. Full history: [Release Notes](CHANGELOG.en.md).

</details>

---

<p align="center">
  Maintainer <b>Cogan17</b> &nbsp;·&nbsp; source <b>Android Common Kernel</b> &nbsp;·&nbsp; <b>KernelSU Next</b> &nbsp;·&nbsp; <b>BakaSU</b> &nbsp;·&nbsp; <b>SUSFS</b>
  <br><a href="docs/keaslian-dan-kredit.en.md">🔏 Authenticity & full credits</a>
</p>

<sub>Predecessor repository (development history, Xiaomi BSP source): [cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro)</sub>

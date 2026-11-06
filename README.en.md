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
<summary>🧰 <b>Modules the owner uses</b></summary>

Modules the owner runs on their phone together with Cogan Kernel. Click a module name to open its repository. None are required: the kernel works without them, install what you need.

| Module | Purpose | Author |
|---|---|---|
| 🛡️ [SUSFS-FOR-KERNELSU](https://github.com/sidex15/susfs4ksu-module) | SUSFS settings through a WebUI (already in the release as file 5) | sidex15 |
| 🧷 [BRENE](https://github.com/rrr333nnn333/BRENE) | Another SUSFS module with a WebUI: hides root, custom kernel, recovery and Zygisk module traces, and spoofs system properties and `uname` | rrr333nnn333 |
| 📂 [NoMount](https://github.com/maxsteeel/nomount) | Mountless module loading (already in the kernel) | maxsteeel |
| 🧠 [Cogan Smart Kernel](modules/cogan-smart/README.md) | Power modes, thermals, module guard | Cogan17 |
| 🔁 [AshReXcue BootLoop Protector](https://github.com/RipperHybrid/AshLooper) | Disables modules automatically on bootloop | RipperHybrid |
| 🧬 [Zygisk Next](https://github.com/Dr-TSNG/ZygiskNext) | Zygisk for KernelSU (needed by the Zygisk modules below) | Dr-TSNG |
| 🧩 [Vector](https://github.com/JingMatrix/Vector) | Xposed framework (LSPosed successor) | JingMatrix |
| 🔌 [AdbHide](https://github.com/enchantedglycerin/AdbHide) | Vector/LSPosed module: hides ADB and developer options from apps, USB debugging keeps working | enchantedglycerin |
| 🔓 [Core Patch](https://github.com/LSPosed/CorePatch) | Vector/LSPosed module: allows app downgrades and skips APK signature checks | CoderStory, LSPosed |
| 📁 [FuseHide](https://github.com/XiaoTong6666/FuseHide) | Vector/LSPosed module: hides storage folders (e.g. root traces) from selected apps | XiaoTong6666 |
| 🙈 [HMA-OSS](https://github.com/frknkrc44/HMA-OSS) | Hides your app list from other apps | frknkrc44 |
| ✅ [Play Integrity Fix [INJECT]](https://github.com/KOWX712/PlayIntegrityFix) | Fixes Play Integrity | KOWX712 |
| 🔑 [Tricky Store OSS](https://github.com/beakthoven/TrickyStoreOSS) | Key attestation for Play Integrity | beakthoven |
| 🔐 [TEESimulator](https://github.com/JingMatrix/TEESimulator) | TEE simulation for key attestation, replaces Tricky Store (install one of them); of the system apps, target only Google Play services and the Play Store | JingMatrix |
| ➕ [Tricky Addon](https://github.com/KOWX712/Tricky-Addon-Update-Target-List) | WebUI to manage the Tricky Store target app list (`target.txt`) | KOWX712 |
| 🦆 [Duck ToolBox](https://github.com/eltavine/Duck-ToolBox) | Attestation toolbox in one WebUI: Tricky Store/TEESimulator manager (a full Tricky Addon port), its own Play Integrity engine (off by default), RKP | Eltavine, KOW, MhmRdd |
| 🕵️ [Stealth Debug](https://github.com/sp11xy/StealthDebug) | Hides USB/developer debugging from apps | sp11xy |
| 🌐 [TCP Optimiser](https://github.com/fatalcoder524/TCP_Optimiser_Module) | Tunes TCP congestion control | fatalcoder524 |
| 📱 [HyperUnlocked](https://github.com/ukriu/HyperUnlocked) | Unlocks hidden HyperOS features | ukriu |
| 👆 [NavTweaks](https://github.com/DanGLVK/Hide-Navbar) | Hides the gesture navigation bar | DanGLVK |
| ▶️ [YouTube Morphe](https://github.com/MorpheApp/morphe-manager) | Modded YouTube, root-installed through Morphe Manager | MorpheApp |
| 🚫 [zygisk-detach](https://github.com/j-hc/zygisk-detach) | Detaches apps from Play Store updates | j-hc |
| 📶 [WiFi Password Viewer](https://github.com/Googlers-Repo/wpd) | Shows saved Wi-Fi passwords (for MMRL) | Googlers-Repo |

**⚠️ Pick one.** The modules below do the same job. Installing both can overwrite each other's settings or make Play Integrity fail.

| Pick one | Why |
|---|---|
| SUSFS-FOR-KERNELSU **or** BRENE | Both manage SUSFS and install the `ksu_susfs` tool. BRENE disables other SUSFS modules when installed |
| Play Integrity Fix [INJECT] **or** Duck ToolBox (Play Integrity feature) | Duck ToolBox ships its own Play Integrity engine (derived from Play Integrity Fork). If you use PIF Inject, leave Duck ToolBox's Play Integrity feature off |
| Tricky Store OSS **or** TEESimulator | Both are keystore modules for key attestation |
| Tricky Addon **or** Duck ToolBox | Duck ToolBox already contains a full Tricky Addon port |

**📝 Notes before installing**

- Install modules **one at a time**: install, reboot, check the phone works, then move on to the next one. If the phone bootloops, you know which module did it.
- Install **AshReXcue BootLoop Protector** first, so modules are disabled automatically on a bootloop. If the phone is still stuck, see [Back to Stock](docs/kembali-ke-stok.en.md).
- AdbHide, Core Patch and FuseHide are Vector/LSPosed modules: they need **Zygisk Next** and **Vector**, and are enabled in the Vector app.
- Duck ToolBox needs **Zygisk Next**. Its Tricky Store manager configures the active keystore module (Tricky Store OSS or TEESimulator), so one of them is still installed.
- The `uname` spoof in [Install the Kernel](docs/pasang.en.md) uses the sidex15 SUSFS module's WebUI. With BRENE, enter the same values in BRENE's *Spoof Uname* setting.

</details>

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
| Stock kernel | `6.1.157-android14-11` (HyperOS `OS3.0.302`) or `6.1.138-android14-11` (`OS3.0.301`), any region ([check the version](docs/pasang.en.md#before-you-start)) |

</details>

<details>
<summary>✨ <b>What's inside</b></summary>

- ✅ Google's official kernel source (Android Common Kernel `android14-6.1`), the same family as the phone's stock kernel. Xiaomi/MediaTek vendor modules still fit
- ✅ Always the newest versions: the ACK release, root manager, SUSFS and NoMount are taken at their newest at build time. When something does not fit yet, the build summary names the developer to wait for
- ✅ In-kernel root + **SUSFS**, five variants: **KernelSU Next**, **BakaSU**, official **KernelSU** (tiann, a fallback; kernel and manager from the newest `main` commit with an official CI manager build), or **SukiSU** Ultra (with SUSFS the kernel comes from its `builtin` branch, which has SUSFS built in, without SUSFS from the newest release; the manager always from the newest release; no KPM), or **[CoganSU](https://github.com/cogan17/CoganSU)** (a root manager made for Cogan Kernel, based on KernelSU; kernel and manager from the same newest CoganSU release). SUSFS is ticked by default; unticked, the kernel uses the plain root manager without SUSFS (ZIP name without `+SuSFS`, no SUSFS module)
- ✅ **NoMount** (mountless modules, built into the kernel), **Baseband Guard**
- ✅ **BBRv3** as the default TCP (`bbr` and `bbr3`)
- ✅ **Cogan Bridge**: the kernel and the Cogan Smart module know each other (`/sys/kernel/cogan`)
- ✅ No LTO by default (faster builds; Thin/Full LTO can still be chosen), device check in the ZIP (`rothko` only)
- ⚙️ Optional, ticked by default: **Unicode fix** (WildKernel). File names with invisible characters (e.g. zero-width) on internal storage no longer count as the same name without them (the *unicode bypass* gap used to find hidden paths)
- ⚙️ Optional, **off by default**: **Disguise kernel identity**. `uname` and `/proc/version` use the stock GKI format (`6.1.176-android14-11-g…-ab…`) instead of the `Cogan` name. Display only, not behaviour-based hiding
- ✅ Every build is checked automatically against the stock kernel ABI (KMI gate); failure = no ZIP

</details>

<details>
<summary>🧩 <b>Supported sublevels</b></summary>

The builder uses the official ACK `android14-6.1` releases since the phone's stock kernel; `lts` = the newest; type `semua` (or `all`) in Kernel Sublevel for every sublevel (GitHub replaces an empty field with its default, `lts`). The **Catat sublevel** (record sublevels) workflow button records the latest build in this table (✅ passed the build and the KMI gate, ⏳ waiting for an upstream update); it neither checks nor builds.

**Pilih sumber / Source** (the first field of the Builder form): **Always newest (CI)** takes the newest version of every component; when one does not fit yet, that root waits. **Stable (last good build)** takes every component (ACK, root manager, SUSFS, NoMount, modules and the rest) exactly from the last successful build of that root (`kernel/history/`), so it still builds while the newest versions wait. Managers from the developers' CI are kept for 90 days only.

The **Cek pembaruan** (check for updates) button is the only check, and it builds nothing: the newest version of every component (ACK, KernelSU Next, BakaSU, KernelSU, SukiSU, CoganSU, simonpunk's SUSFS and sidex15's SUSFS module, NoMount, Baseband Guard, AnyKernel3, Neutron clang, Unicode fix) against the last build, with the dates of the stable and CI versions, what is new and fixed, and whom to wait for when it cannot be built yet. When something is newer, the summary suggests running the Builder.

**[Build history](kernel/history/)** is saved automatically by the Builder as Markdown documents. **Last build** and **Status** remain comparable after Actions logs, artifacts or runs are deleted; **Delete old run logs** works as before.

<!-- sublevel:start -->
| Sublevel | ACK release | Status |
|---|---|---|
| **176** (`lts`) | `2026-09_r5` | ✅ KernelSU Next · BakaSU: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/41377913431) · r1 and r2 tested on the phone |
| 172 | `2026-06_r17` | ✅ KernelSU Next · BakaSU: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/41377913431) |
| 162 | `2026-03_r25` | ✅ KernelSU Next · BakaSU: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/41377913431) |
| 157 | `2025-12_r32` | ✅ KernelSU Next · BakaSU: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/41377913431) |
| 145 | `2025-09_r36` | ✅ KernelSU Next · BakaSU: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/41377913431) |
| 141 | `2025-07_r13` | ✅ KernelSU Next · BakaSU: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/41384518511) |
| 138 | `2025-06_r17` | ✅ KernelSU Next · BakaSU: [build + KMI gate](https://github.com/cogan17/Cogan-Kernel/actions/runs/41377913431) · the phone's stock kernel; archive r5 tested on the phone |
<!-- sublevel:end -->

Unicode fix (ticked by default since 1 Nov 2026) passes the build + KMI gate on 157, 162, 172 and 176, and applies cleanly on 138 and 145 ([CI](https://github.com/cogan17/Cogan-Kernel/actions/runs/40048269498)). If WildKernel's patch does not fit yet, the build stops: untick Unicode fix to build anyway.

🛡️ **CVE-2026-53163** is applied automatically in every build: the official Linux 6.1.177 fix (commit `40a25d59e85b`) for a kernel crash through futex that came with the CVE-2026-43499 fix in 6.1.175. ACK releases without the CVE-2026-43499 fix (below 175) do not have this bug, and ACK releases that already contain the fix are skipped.

🫥 **Disguise kernel identity** (checkbox, off by default): `uname` and `/proc/version` mimic the phone's own stock kernel (taken from the rothko stock boot.img): the GKI format `6.1.176-android14-11-g<ACK commit>-ab…`, builder `build-user@build-host`, and Google's Android clang 17.0.2 / LLD 17.0.2 text, instead of the `Cogan` name and Neutron clang. The version stays the real one (e.g. 6.1.176). This only changes what is shown, not the compiled code, so the KMI gate is unaffected. Cogan Bridge and the Cogan Smart module keep working; the `Cogan` name and revision stay in the ZIP name and release notes. It does **not** defeat behaviour-based detection (root traces, mounts, properties) or the phone's security-chip checks (Play Integrity). Test on the phone first.

To publish an existing build, run **Rilis dari run** with the green Builder run ID. A run containing several root managers (KernelSU Next, BakaSU, KernelSU, SukiSU, CoganSU) becomes **one release** with all kernel ZIPs and their matching manager APKs, without rebuilding. Tick **diuji di HP** only if the owner tested every variant in that run on the phone. If the same tag already exists (e.g. `v26.11.02-r21`: the owner's rN and the run number of a CI build can meet on the same day), the release stops; tick **timpa** to replace that old release and its files with this run's build. Only kernel releases `vYY.MM.DD-rN` can be replaced; archives and Cogan Smart cannot.

Release notes include **What's New & Fixes**, compared with the previous release of the same root manager. The run's **Summary** provides **one Telegram post ready to copy** for the whole release (KernelSU Next and BakaSU in one text) in Indonesian and English, each in a code block with a copy button. Changes from the root manager and SUSFS developers are written in plain words (e.g. "fixes SELinux hiding"), without commit codes. Tick **teks_saja** to generate only notes and Telegram posts, including for an already published version; this mode does not publish or change a release.

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
  Maintainer <b>Cogan17</b> &nbsp;·&nbsp; source <b>Android Common Kernel</b> &nbsp;·&nbsp; <b>KernelSU Next</b> &nbsp;·&nbsp; <b>BakaSU</b> &nbsp;·&nbsp; <b>KernelSU</b> &nbsp;·&nbsp; <b>SukiSU</b> &nbsp;·&nbsp; <b>CoganSU</b> &nbsp;·&nbsp; <b>SUSFS</b>
  <br><a href="docs/keaslian-dan-kredit.en.md">🔏 Authenticity & full credits</a>
</p>

<sub>Predecessor repository (development history, Xiaomi BSP source): [cogan17/Kernel-14t-pro](https://github.com/cogan17/Kernel-14t-pro)</sub>

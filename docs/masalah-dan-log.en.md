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

## Release from run fails with HTTP 403

If **Terbitkan / publish** reports `HTTP 403: Resource not accessible by integration`, check the release token permissions. `contents: write` alone is insufficient when the older build commit has different `.github/workflows/` files from `main` at release time. The built-in `GITHUB_TOKEN` cannot be granted the additional permission required here ([GitHub Docs](https://docs.github.com/en/rest/releases/releases#create-a-release)).

One-time owner setup:

1. Open [fine-grained token creation](https://github.com/settings/personal-access-tokens/new). Select resource owner **cogan17**, **Only select repositories** → **Xiomi_14T_Pro**, and an appropriate expiry.
2. Under **Repository permissions**, grant **Contents: Read and write** and **Workflows: Read and write**. Generate the token.
3. Open the repository's [Actions secrets](https://github.com/cogan17/Xiomi_14T_Pro/settings/secrets/actions) → **New repository secret**. Name it `RELEASE_TOKEN` and paste the token as its value. Keep it in the secret, never in source, issues or chat.
4. Once the workflow fix reaches `main`, start **Rilis dari run → Run workflow** from `main` using the same successful build ID. Do not choose **Re-run jobs** on the old run: GitHub reruns use the workflow at the old commit.

For failed [run 40052126936](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/40052126936), use `run_id` **40046361218**, **Pre-Release**, and the same phone-test choice and note as before. No kernel rebuild is needed while its artifacts remain available (7 days).

The workflow uses `RELEASE_TOKEN` only in the publication step; reading and downloading still use the built-in token. Without the secret, it falls back to the built-in token, which can publish builds that do not need the additional Workflows permission. The tag still points to the original build commit, and existing releases are still refused. If the secret is configured but 403 persists, check its expiry, repository selection and both permissions.

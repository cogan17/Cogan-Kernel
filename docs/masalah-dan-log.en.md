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

**Release from run uses a GitHub App**, as chosen by the owner on 24 Oct 2026. The App creates a short-lived token whenever the owner presses **Run workflow**, without periodic PAT renewal. GitHub's official action revokes the token when the job ends. Complete the one-time registration and credential setup below before first use ([GitHub Docs](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/making-authenticated-api-requests-with-a-github-app-in-a-github-actions-workflow)).

### One-time GitHub App setup

1. Open [New GitHub App](https://github.com/settings/apps/new) under **cogan17**. Enter a **GitHub App name**, such as `Cogan17 Rothko Release` (it must be unique), and **Homepage URL**: `https://github.com/cogan17/Xiomi_14T_Pro`.
2. Leave **Callback URL** empty, and leave **Request user authorization (OAuth) during installation** and **Enable Device Flow** unchecked. Under **Webhook**, uncheck **Active**: this App only authenticates releases, with no server or automatic triggers.
3. Under **Repository permissions**, grant **Contents: Read and write** and **Workflows: Read and write**. Read-only Metadata is included automatically. No other permissions are needed. Select **Only on this account**, then **Create GitHub App**.
4. Copy the App's **Client ID** (not its App ID or Client secret). Open the repository's [Actions variables](https://github.com/cogan17/Xiomi_14T_Pro/settings/variables/actions) → **New repository variable**:

   | Variable name | Value |
   |---|---|
   | `RELEASE_APP_CLIENT_ID` | The App's Client ID |

5. Return to the App page → **Private keys → Generate a private key**. A `.pem` file downloads. Open the repository's [Actions secrets](https://github.com/cogan17/Xiomi_14T_Pro/settings/secrets/actions) → **New repository secret**:

   | Secret name | Value |
   |---|---|
   | `RELEASE_APP_PRIVATE_KEY` | The entire PEM file, including its `BEGIN RSA PRIVATE KEY` and `END RSA PRIVATE KEY` lines |

   Keep the private key in the GitHub secret; never upload it to source, issues or chat. No OAuth Client secret is used.
6. In the App's settings, open **Install App** → **Install** for cogan17 → **Only select repositories** → **Xiomi_14T_Pro** → **Install**. Registration alone is insufficient; install the App on the repository.
7. Start the latest **Rilis dari run → Run workflow** from `main` with a successful build ID. Do not choose **Re-run jobs** on the old run: GitHub reruns use the workflow at the old commit.

For failed [run 40052126936](https://github.com/cogan17/Xiomi_14T_Pro/actions/runs/40052126936), use `run_id` **40046361218**, **Pre-Release**, and the same phone-test choice and note as before. No kernel rebuild is needed while its artifacts remain available (7 days).

The workflow checks the variable and secret before downloading artifacts. Reading and downloading use the read-only `GITHUB_TOKEN`; only publication receives the App token, limited to this repository. The source SHA comes from the validated run, so the App needs no Actions permission. Tags still point to the original build commit, and existing releases are still refused. The previous PAT secret `RELEASE_TOKEN` is no longer used.

If token creation or publication fails, check the Client ID, active private key, App installation on this repository and Contents + Workflows permissions. If App permissions change, accept the installation's permission update. Each run creates a new token while the installation and private key remain active. Workflow and CI success alone do not prove that App registration or a real release has completed.

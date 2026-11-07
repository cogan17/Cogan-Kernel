# 🔑 CoganSU token (COGANSU_TOKEN)

[← Back to README](../README.en.md) · <img src="https://flagcdn.com/24x18/id.png" width="22" alt=""> [Bahasa Indonesia](cogansu-token.md)

With this token the CoganSU variant of **Cogan Kernel Builder** becomes **one step**. When the newest CoganSU release lacks the newest KernelSU `main`, or does not fit SUSFS yet, the Builder runs **Build CoganSU** in `cogan17/CoganSU` itself. Build CoganSU merges the newest KernelSU automatically. The Builder waits for it to finish, then builds the kernel with the new CoganSU release.

A token is needed because a workflow in one repository may not start a workflow of another repository with GitHub's built-in token.

> [!IMPORTANT]
> This token may only run workflows in `cogan17/CoganSU`. Give it no other repository and no other permission. Never share it with anyone, chats included.

---

## 1. Create the token (fine-grained)

Open **https://github.com/settings/personal-access-tokens/new** (signed in as `cogan17`). From the menu: profile picture → **Settings** → at the bottom **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**. Fill in from top to bottom:

1. **Token name**: `Cogan Kernel - Build CoganSU`
2. **Description** (optional): `Used by Cogan Kernel Builder to run Build CoganSU`
3. **Resource owner**: leave **cogan17**.
4. **Expiration**: tap **No expiration** → **Custom…** → pick a date one year ahead and note it. *No expiration* works too, but GitHub recommends a date.
5. **Repository access**: choose **Only select repositories** (not *Public repositories* or *All repositories*) → tap **Select repositories** → type `CoganSU` → tick **cogan17/CoganSU** only.
6. **Permissions**:
   - Once the repository is chosen, the Permissions box has a **Repositories** part next to **Account**. Open **Repositories**.
   - Tap **Add permissions** → tick **Actions** → close the list.
   - On the **Actions** row, change *Read-only* to **Read and write**.
   - **Metadata** (*Read-only*) is added automatically; leave it.
   - Leave **Account** at **0**; add nothing there.
7. Tap **Generate token**. If a summary shows up, check it: repository `cogan17/CoganSU`, *Actions: Read and write*, *Metadata: Read-only*. Then tap **Generate token** again.
8. **Copy** the token (it starts with `github_pat_…`). It is shown only once.

## 2. Store it as a secret in Cogan-Kernel

1. Open **https://github.com/cogan17/Cogan-Kernel/settings/secrets/actions**.
   From the menu: the **Cogan-Kernel** repository → **Settings** → **Secrets and variables** → **Actions**. On a phone, turn on **Desktop site** if Settings does not show.
2. Tap **New repository secret**.
3. **Name**: type `COGANSU_TOKEN` (capitals, no spaces).
   **Secret**: paste the token from step 1.
4. Tap **Add secret**.

## 3. Use it

Run **Cogan Kernel Builder** as usual with Root Flavor `CoganSU` or a combination with it. There is no need to run Build CoganSU first.

| Kernel Release Type | CoganSU release made automatically |
|---|---|
| `CI` | Pre-Release |
| `Pre-Release` | Pre-Release |
| `Release` | Release |

- When the CoganSU release already carries the newest KernelSU and fits SUSFS, the Builder builds the kernel right away, without Build CoganSU.
- When it is needed, the Builder summary says **🔄 CoganSU was built automatically** and links the Build CoganSU run. The Builder then takes about 10 minutes longer.
- **"Wait"** only appears when a main developer is not ready, e.g. *Wait for simonpunk* when the SUSFS patch does not fit KernelSU `main` either.

## If something goes wrong

| Message in the Builder summary | Meaning |
|---|---|
| *Secret COGANSU_TOKEN is missing* | Step 2 was not done. Other variants are still built. |
| *GitHub refused COGANSU_TOKEN (HTTP 401/403/404)* | The token expired, was copied wrongly, or lacks *Actions: Read and write* on `cogan17/CoganSU`. Create a new token (step 1) and **Update** the secret. |
| *Build CoganSU failed (…): link* | Build CoganSU itself failed. Open the link and read its log. |

GitHub emails you before the token expires. Renew it with **Regenerate token** on the token's page, then **Update** the `COGANSU_TOKEN` secret.

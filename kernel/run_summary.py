#!/usr/bin/env python3
"""One result table for a Cogan Kernel Builder run, in Indonesian and English (owner 2026-10-24).

Every planned build is listed, README style: ✅ built (release, KMI gate, sha256), ❌ failed (why:
the KMI gate's reason, the error, or the stage where it stopped) and ⏳ not built (whom to wait for).

Usage: run_summary.py --matrix JSON --info DIR --snapshots DIR --repo OWNER/REPO
                      [--resolve RESULT] [--attest RESULT] [--release RESULT] [--telegram DIR]
DIR holds one build-info-<root>-<sublevel> directory per build, with what the build left behind:
build.env (built), wait.json (a newest version does not fit yet), kmi-compat.json (the gate's
report), error.txt (a fault of this repository) and stage.txt (the last stage it started).
RESULT is a job result: success, failure, cancelled or skipped. DIR holds id.txt and en.txt of
kernel/telegram.py; with one build they are shown in a code block, ready to copy for Telegram.
--susfs DIR holds the susfs-<commit>.env files of the SUSFS module job (kernel/susfs_module.sh).
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOTS = {"KSUN": "KernelSU Next", "BSU": "BakaSU"}
TEXT = {
    "id": {"flag": "🇮🇩 Bahasa Indonesia", "build": "Build", "result": "Hasil", "detail": "Keterangan",
           "ok": "✅ Berhasil", "fail": "❌ Gagal", "wait": "⏳ Tidak dibangun",
           "count": "**{ok} berhasil · {fail} gagal · {wait} tidak dibangun**",
           "gate_ok": "gate KMI OK, CRC beda {crc}", "gate_no": "gate KMI menolak: {why}",
           "stage": "berhenti di: {stage}", "nothing": "tanpa keterangan, lihat log job ini",
           "features": "**Fitur:** {features}", "zip": "**ZIP** (cek: `gh attestation verify <zip> --repo {repo}`)",
           "resolve": "❌ **Gagal sebelum build.** Lihat pesan error di atas (isian form atau versi terbaru).",
           "attest": "❌ Tanda tangan ZIP gagal: jangan terbitkan run ini.",
           "published": "Terbit: [{tag}]({url})", "unpublished": "❌ Gagal terbit: lihat job Terbit.",
           "telegram": "**📣 Teks Telegram** (salin lewat tombol di pojok kanan atas kotak)",
           "susfs": "**Modul SUSFS** (5 simonpunk, 6 sidex15 dengan WebUI; pasang salah satu)",
           "susfs_fail": "❌ Modul SUSFS gagal dibuat atau diambil: lihat job Modul SUSFS. Run ini tidak bisa diterbitkan."},
    "en": {"flag": "🇬🇧 English", "build": "Build", "result": "Result", "detail": "Details",
           "ok": "✅ Built", "fail": "❌ Failed", "wait": "⏳ Not built",
           "count": "**{ok} built · {fail} failed · {wait} not built**",
           "gate_ok": "KMI gate OK, CRC differs {crc}", "gate_no": "KMI gate refused: {why}",
           "stage": "stopped at: {stage}", "nothing": "no details, see this job's log",
           "features": "**Features:** {features}", "zip": "**ZIP** (check: `gh attestation verify <zip> --repo {repo}`)",
           "resolve": "❌ **Failed before any build.** See the error above (form input or newest versions).",
           "attest": "❌ Signing the ZIP failed: do not publish this run.",
           "published": "Published: [{tag}]({url})", "unpublished": "❌ Publishing failed: see the publish job.",
           "telegram": "**📣 Telegram post** (copy with the button at the top right of the box)",
           "susfs": "**SUSFS modules** (5 simonpunk, 6 sidex15 with WebUI; install one)",
           "susfs_fail": "❌ A SUSFS module could not be built or fetched: see the SUSFS modules job. This run cannot be published."},
}


def read_env(path):
    return dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line) if path.is_file() else {}


def outcome(build, folder):
    """(kind, values) of one planned build: ok, wait or fail, from the files it left behind."""
    env = read_env(folder / "build.env")
    if env.get("ZIP_SHA256"):
        crc = re.search(r"CRC differs (\d+)", env.get("KMI_COMPAT", ""))
        return "ok", {"env": env, "crc": crc[1] if crc else "?"}
    if (folder / "wait.json").is_file():
        return "wait", json.loads((folder / "wait.json").read_text())
    report = folder / "kmi-compat.json"
    errors = json.loads(report.read_text()).get("errors", []) if report.is_file() else []
    if errors:
        return "fail", {"gate": "; ".join(errors)[:300]}
    error = (folder / "error.txt").read_text().strip() if (folder / "error.txt").is_file() else ""
    stage = (folder / "stage.txt").read_text().strip() if (folder / "stage.txt").is_file() else ""
    return "fail", {"error": error[:300], "stage": stage}


def rows(matrix, info, snapshots):
    found = []
    for build in matrix:
        kind, values = outcome(build, info / f"build-info-{build['root']}-{build['sublevel']}")
        found.append((build["name"], kind, values))
    for path in sorted(snapshots.glob("*.json")):  # a root whose newest version does not fit is not planned
        snap = json.loads(path.read_text())
        if "wait" in snap:
            found.append((ROOTS.get(snap.get("root"), snap.get("root", path.stem)), "wait", snap["wait"]))
    return found


def detail(lang, kind, values):
    t = TEXT[lang]
    if kind == "ok":
        return f"`{values['env'].get('RELEASE', '')}` · " + t["gate_ok"].format(crc=values["crc"])
    if kind == "wait":
        return values[lang]
    if "gate" in values:
        return t["gate_no"].format(why=values["gate"])
    if values.get("error"):
        return values["error"]
    return t["stage"].format(stage=values["stage"]) if values.get("stage") else t["nothing"]


def summary(matrix, info, snapshots, repo, resolve="success", attest="success", release="skipped", telegram=None,
            susfs=None, susfs_result="skipped"):
    found = rows(matrix, info, snapshots)
    modules = [read_env(path) for path in sorted(susfs.glob("susfs-*.env"))] if susfs and susfs.is_dir() else []
    built = [values["env"] for _, kind, values in found if kind == "ok"]
    # One features line when every build has the same features; otherwise per row.
    common = built[0].get("FEATURES", "") if built and len({env.get("FEATURES", "") for env in built}) == 1 else ""
    lines = ["## 📋 Hasil / Results", ""]
    for lang in ("id", "en"):
        t = TEXT[lang]
        lines += [f"<details{' open' if lang == 'id' else ''}><summary>{t['flag']}</summary>", ""]
        if resolve != "success" and not found:
            lines += [t["resolve"], "", "</details>", ""]
            continue
        counts = {kind: sum(1 for _, k, _ in found if k == kind) for kind in ("ok", "fail", "wait")}
        lines += [t["count"].format(**counts), "", f"| {t['build']} | {t['result']} | {t['detail']} |", "|---|---|---|"]
        for name, kind, values in found:
            text = detail(lang, kind, values).replace("|", "\\|").replace("\n", " ")
            if kind == "ok" and not common:
                text += f" · {values['env'].get('FEATURES', '')}"
            lines.append(f"| {name} | {t[kind]} | {text} |")
        lines.append("")
        if common:
            lines += [t["features"].format(features=common), ""]
        if built:
            lines += [t["zip"].format(repo=repo),
                      *[f"- `{env.get('ZIP', '')}` · sha256 `{env['ZIP_SHA256']}`" for env in built], ""]
        if modules:
            lines += [t["susfs"], *[f"- `{env.get('SUSFS_MODULE', '')}` · sha256 `{env.get('SUSFS_MODULE_SHA256', '')}`"
                                    for env in modules], ""]
        if susfs_result == "failure":
            lines += [t["susfs_fail"], ""]
        if attest == "failure":
            lines += [t["attest"], ""]
        if release == "success" and len(built) == 1:
            tag = built[0].get("RELEASE", "")
            lines += [t["published"].format(tag=tag, url=f"https://github.com/{repo}/releases/tag/{tag}"), ""]
        elif release == "failure":
            lines += [t["unpublished"], ""]
        post = telegram / f"{lang}.txt" if telegram else None
        if post and post.is_file() and len(built) == 1:
            lines += [t["telegram"], "", "```text", post.read_text().rstrip("\n"), "```", ""]
        lines += ["</details>", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--matrix", default="")
    parser.add_argument("--info", type=Path, required=True)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--resolve", default="success")
    parser.add_argument("--attest", default="success")
    parser.add_argument("--release", default="skipped")
    parser.add_argument("--telegram", type=Path)
    parser.add_argument("--susfs", type=Path)
    parser.add_argument("--susfs-result", default="skipped")
    args = parser.parse_args(argv)
    matrix = json.loads(args.matrix)["include"] if args.matrix.strip() else []
    sys.stdout.write(summary(matrix, args.info, args.snapshots, args.repo, args.resolve, args.attest, args.release,
                             args.telegram, args.susfs, args.susfs_result))
    return 0


if __name__ == "__main__":
    sys.exit(main())

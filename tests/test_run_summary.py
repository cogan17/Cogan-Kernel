#!/usr/bin/env python3
"""Offline tests for kernel/run_summary.py: one bilingual result table, success and failure alike."""
import json
import tempfile
import unittest
from pathlib import Path

from kernel import run_summary as rs

KMI_OK = ("KMI Xiaomi 14T Pro (rothko): OK; generation 11; exported GKI 2/2; CRC differs 0 (force-load on); "
          "BSP: generation 11")
FEATURES = "SUSFS, BBRv3 (default, also bbr3), BBG, NoMount, Cogan Bridge, Full LTO"


def build(root, sublevel):
    return {"root": root, "sublevel": str(sublevel), "name": f"{rs.ROOTS[root]} 6.1.{sublevel}"}


class RunSummaryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.info, self.snapshots = base / "info", base / "snapshots"
        self.info.mkdir()
        self.snapshots.mkdir()

    def left(self, root, sublevel, **files):
        folder = self.info / f"build-info-{root}-{sublevel}"
        folder.mkdir()
        names = {"build_env": "build.env", "kmi_compat": "kmi-compat.json", "stage_txt": "stage.txt",
                 "error_txt": "error.txt", "wait_json": "wait.json"}
        for name, text in files.items():
            (folder / names[name]).write_text(text)

    def test_every_build_is_listed_with_its_result_and_reason(self):
        self.left("KSUN", 176, build_env=f"RELEASE=v26.10.24-r2\nZIP=1-KERNEL_x.zip\nZIP_SHA256={'a' * 64}\n"
                                         f"KMI_COMPAT={KMI_OK}\nFEATURES={FEATURES}\n")
        self.left("KSUN", 141, kmi_compat=json.dumps({"errors": ["stock vendor hooks missing but used by vendor modules: "
                                                                 "android_vh_reweight_entity"]}), stage_txt="KMI gate")
        self.left("KSUN", 162, stage_txt="Building kernel")
        self.left("KSUN", 157, error_txt="BBRv3 does not fit ACK 6.1.157 yet", stage_txt="BBRv3")
        (self.snapshots / "BSU.json").write_text(json.dumps({"root": "BSU", "wait": {
            "id": "Tunggu pengembang BakaSU.", "en": "Wait for the BakaSU developer."}}))
        matrix = [build("KSUN", s) for s in (176, 141, 162, 157, 145)]
        text = rs.summary(matrix, self.info, self.snapshots, "cogan17/Cogan-Kernel")
        self.assertIn("**1 berhasil · 4 gagal · 1 tidak dibangun**", text)
        self.assertIn("**1 built · 4 failed · 1 not built**", text)
        self.assertIn("| KernelSU Next 6.1.176 | ✅ Berhasil | `v26.10.24-r2` · gate KMI OK, CRC beda 0 |", text)
        self.assertIn("| KernelSU Next 6.1.176 | ✅ Built | `v26.10.24-r2` · KMI gate OK, CRC differs 0 |", text)
        self.assertIn("| KernelSU Next 6.1.141 | ❌ Gagal | gate KMI menolak: stock vendor hooks missing", text)
        self.assertIn("| KernelSU Next 6.1.162 | ❌ Failed | stopped at: Building kernel |", text)
        self.assertIn("| KernelSU Next 6.1.157 | ❌ Gagal | BBRv3 does not fit ACK 6.1.157 yet |", text)
        self.assertIn("| KernelSU Next 6.1.145 | ❌ Gagal | tanpa keterangan, lihat log job ini |", text)
        self.assertIn("| BakaSU | ⏳ Tidak dibangun | Tunggu pengembang BakaSU. |", text)
        self.assertIn("| BakaSU | ⏳ Not built | Wait for the BakaSU developer. |", text)
        self.assertIn(f"**Fitur:** {FEATURES}", text)
        self.assertIn(f"- `1-KERNEL_x.zip` · sha256 `{'a' * 64}`", text)
        self.assertLess(text.index("🇮🇩"), text.index("🇬🇧"))

    def test_failed_before_any_build(self):
        text = rs.summary([], self.info, self.snapshots, "r/r", resolve="failure")
        self.assertIn("❌ **Gagal sebelum build.**", text)
        self.assertIn("❌ **Failed before any build.**", text)

    def test_nothing_buildable_still_names_whom_to_wait_for(self):
        (self.snapshots / "BSU.json").write_text(json.dumps({"root": "BSU", "wait": {"id": "Tunggu.", "en": "Wait."}}))
        text = rs.summary([], self.info, self.snapshots, "r/r", resolve="failure")
        self.assertIn("**0 berhasil · 0 gagal · 1 tidak dibangun**", text)
        self.assertNotIn("Gagal sebelum build", text)

    def test_published_release_and_failed_signing(self):
        self.left("KSUN", 176, build_env=f"RELEASE=v26.10.24-r2\nZIP=z.zip\nZIP_SHA256={'b' * 64}\nKMI_COMPAT={KMI_OK}\n")
        text = rs.summary([build("KSUN", 176)], self.info, self.snapshots, "cogan17/Cogan-Kernel", release="success")
        self.assertIn("Terbit: [v26.10.24-r2](https://github.com/cogan17/Cogan-Kernel/releases/tag/v26.10.24-r2)", text)
        self.assertIn("Published: [v26.10.24-r2]", text)
        text = rs.summary([build("KSUN", 176)], self.info, self.snapshots, "r/r", attest="failure", release="failure")
        self.assertIn("❌ Tanda tangan ZIP gagal", text)
        self.assertIn("❌ Publishing failed", text)

    def test_susfs_module_is_listed_and_its_failure_named(self):
        # The SUSFS module is the 5th file of a run: sidex15's, next to the kernel, managers and NoMount (owner 2026-10-29).
        self.left("KSUN", 176, build_env=f"RELEASE=v26.10.26-r7\nZIP=z.zip\nZIP_SHA256={'d' * 64}\nKMI_COMPAT={KMI_OK}\n")
        susfs = Path(self.temp.name) / "susfs"
        susfs.mkdir()
        (susfs / "susfs-sidex15.env").write_text(f"SUSFS_MODULE=5-SUSFS-MODULE-SIDEX15_v1.5.2-CI-89b04b9.zip\nSUSFS_MODULE_SHA256={'f' * 64}\n")
        text = rs.summary([build("KSUN", 176)], self.info, self.snapshots, "r/r", susfs=susfs, susfs_result="success")
        self.assertIn("**Modul SUSFS** (sidex15, dengan WebUI)\n"
                      f"- `5-SUSFS-MODULE-SIDEX15_v1.5.2-CI-89b04b9.zip` · sha256 `{'f' * 64}`", text)
        self.assertIn("**SUSFS module** (sidex15, with WebUI)", text)
        text = rs.summary([build("KSUN", 176)], self.info, self.snapshots, "r/r", susfs=Path(self.temp.name) / "none",
                          susfs_result="failure")
        self.assertIn("❌ Modul SUSFS gagal diambil", text)
        self.assertIn("❌ The SUSFS module could not be fetched", text)

    def test_telegram_post_is_shown_in_a_code_block_for_one_build(self):
        self.left("KSUN", 176, build_env=f"RELEASE=v26.10.24-r2\nZIP=z.zip\nZIP_SHA256={'c' * 64}\nKMI_COMPAT={KMI_OK}\n")
        posts = Path(self.temp.name) / "telegram"
        posts.mkdir()
        (posts / "id.txt").write_text("🧠 Cogan Kernel\n✨ Baru\n")
        (posts / "en.txt").write_text("🧠 Cogan Kernel\n✨ New\n")
        text = rs.summary([build("KSUN", 176)], self.info, self.snapshots, "r/r", telegram=posts)
        self.assertIn("**📣 Teks Telegram** (salin lewat tombol di pojok kanan atas kotak)\n\n```text\n"
                      "🧠 Cogan Kernel\n✨ Baru\n```", text)
        self.assertIn("**📣 Telegram post** (copy with the button at the top right of the box)\n\n```text\n"
                      "🧠 Cogan Kernel\n✨ New\n```", text)
        self.assertNotIn("Telegram", rs.summary([build("KSUN", 176)], self.info, self.snapshots, "r/r"))

    def test_cli_reads_the_workflow_matrix(self):
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            rs.main(["--matrix", json.dumps({"include": [build("KSUN", 176)]}), "--info", str(self.info),
                     "--snapshots", str(self.snapshots), "--repo", "r/r"])
        self.assertIn("| KernelSU Next 6.1.176 | ❌ Gagal | tanpa keterangan", out.getvalue())


if __name__ == "__main__":
    unittest.main()

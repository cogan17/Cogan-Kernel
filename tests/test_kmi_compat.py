#!/usr/bin/env python3
"""Offline tests for the rothko KMI compatibility gate."""
import json
import tempfile
import unittest
from pathlib import Path

from kernel.scripts import kmi_compat as kc

ROOT = Path(__file__).resolve().parents[1]
STG = """elf_symbol {
  id: 0x1
  name: "vendor_used"
  is_defined: true
  crc: 0x0000000a
}
elf_symbol {
  id: 0x2
  name: "changed_type"
  crc: 0x0000000b
}
elf_symbol {
  id: 0x3
  name: "no_crc"
}
elf_symbol {
  id: 0x4
  name: "xiaomi_only"
  crc: 0x00000001
}
elf_symbol {
  id: 0x5
  name: "hci_cmd_sync_status"
  crc: 0x00000005
}
elf_symbol {
  id: 0x6
  name: "inode_add_lru"
  crc: 0x00000006
}
"""


class KmiCompatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.src, self.out = base / "src", base / "out"
        (self.src / "android").mkdir(parents=True)
        (self.src / "kernel/module").mkdir(parents=True)
        self.out.mkdir()
        (self.src / "build.config.common").write_text("BRANCH=android14-6.1\nKMI_GENERATION=11\n")
        (self.src / "kernel/module/version.c").write_text(
            'pr_warn("%s: disagrees about version of symbol %s, but ignore...\\n", a, b);\n')
        (self.src / "android/abi_gki_aarch64").write_text("[abi_symbol_list]\n  vendor_used\n")
        (self.src / "android/abi_gki_aarch64_mtk").write_text("[abi_symbol_list]\n# comment\n  changed_type\n\n")
        (self.src / "android/abi_gki_aarch64_xiaomi").write_text("[abi_symbol_list]\n  xiaomi_only\n")
        (self.src / "android/abi_gki_aarch64.stg").write_text(STG)
        (self.out / "vmlinux.symvers").write_text(
            "0x0000000a\tvendor_used\tvmlinux\tEXPORT_SYMBOL\t\n"
            "0x0000000b\tchanged_type\tvmlinux\tEXPORT_SYMBOL_GPL\t\n"
            "0x00000001\txiaomi_only\tvmlinux\tEXPORT_SYMBOL\t\n")

    def run_gate(self):
        report_file = Path(self.temp.name) / "report.json"
        env_file = Path(self.temp.name) / "env"
        status = kc.main(["--device", "rothko", str(self.src), str(self.out),
                          "--json", str(report_file), "--github-env", str(env_file)])
        return status, json.loads(report_file.read_text()), env_file.read_text()

    def test_compatible_kernel_passes(self):
        status, report, env = self.run_gate()
        self.assertEqual(status, 0, report)
        self.assertEqual(report["crc_differences"], [])
        self.assertEqual(report["lists"]["abi_gki_aarch64_mtk"], {"symbols": 1, "missing": []})
        self.assertIn("KMI_COMPAT=KMI Xiaomi 14T Pro (rothko): OK; generation 11", env)
        self.assertIn("mtk 1/1", env)
        self.assertIn("xiaomi 1/1", env)
        self.assertIn("(0 via GKI modules); CRC differs 0 of 3 compared (force-load on)", env)
        self.assertEqual(report["crc"], {"required": 3, "reference_crc": 3, "build_crc": 3, "compared": 3,
                                         "not_measured": {}, "differs": []})
        self.assertIn("force-load", report["loader_policy"])

    def test_a_crc_difference_fails(self):
        # A changed KMI type: force-load would load the vendor module anyway (owner 2026-11-07, audit r13/r14).
        (self.out / "vmlinux.symvers").write_text(
            "0x0000000a\tvendor_used\tvmlinux\tEXPORT_SYMBOL\t\n"
            "0x000000ff\tchanged_type\tvmlinux\tEXPORT_SYMBOL_GPL\t\n"
            "0x00000001\txiaomi_only\tvmlinux\tEXPORT_SYMBOL\t\n")
        status, report, env = self.run_gate()
        self.assertEqual(status, 1)
        self.assertEqual(report["errors"], ["ACK CRC differs for 1 symbol(s), e.g. changed_type"])
        self.assertIn("GAGAL / FAILED", env)

    def test_missing_vendor_symbol_fails(self):
        (self.out / "vmlinux.symvers").write_text("0x0000000a\tvendor_used\tvmlinux\tEXPORT_SYMBOL\t\n")
        status, report, env = self.run_gate()
        self.assertEqual(status, 1)
        self.assertEqual(report["lists"]["abi_gki_aarch64_xiaomi"]["missing"], ["xiaomi_only"])
        self.assertIn("GAGAL / FAILED", env)

    def test_wrong_generation_protected_exports_and_no_force_load_fail(self):
        for change, message in (
                (lambda: (self.src / "build.config.common").write_text("KMI_GENERATION=8\n"), "KMI generation 8"),
                (lambda: (self.src / "android/abi_gki_protected_exports_aarch64").write_text("x\n"),
                 "protected exports still present"),
                (lambda: (self.src / "kernel/module/version.c").write_text("pr_warn(\"disagrees\");\n"),
                 "force-load change missing")):
            self.setUp()
            change()
            status, report, _ = self.run_gate()
            self.assertEqual(status, 1, message)
            self.assertTrue(any(message in error for error in report["errors"]), report["errors"])

    def test_a_candidate_without_force_load_needs_the_upstream_loader(self):
        # Audit r21 T1 (owner 2026-11-19): the Builder box unticked builds with the upstream loader.
        report_file = Path(self.temp.name) / "report.json"
        run = lambda: kc.main(["--device", "rothko", str(self.src), str(self.out), "--force-load", "off",
                               "--json", str(report_file)])
        self.assertEqual(run(), 1)   # the patch is still in this tree
        self.assertIn("module force-load change present in a build without force-load (candidate)",
                      json.loads(report_file.read_text())["errors"])
        (self.src / "kernel/module/version.c").write_text(
            'pr_warn("%s: disagrees about version of symbol %s\\n", a, b);\n\treturn 0;\n')
        self.assertEqual(run(), 0)
        report = json.loads(report_file.read_text())
        self.assertFalse(report["force_load"])
        self.assertEqual(report["loader_policy"], "upstream: a symbol CRC mismatch refuses the module")
        self.assertIn("(force-load OFF)", kc.summary(report))

    def test_symbols_exported_by_stock_gki_modules_are_accepted(self):
        (self.src / "android/abi_gki_aarch64_mtk").write_text("[abi_symbol_list]\n  changed_type\n  hci_cmd_sync_status\n")
        (self.src / "net/bluetooth").mkdir(parents=True)
        (self.src / "net/bluetooth/hci_sync.c").write_text("int hci_cmd_sync_status(void) {}\nEXPORT_SYMBOL(hci_cmd_sync_status);\n")
        status, report, _ = self.run_gate()
        self.assertEqual(status, 1)  # no GKI module list yet
        self.assertEqual(report["lists"]["abi_gki_aarch64_mtk"]["missing"], ["hci_cmd_sync_status"])
        (self.src / "modules.bzl").write_text('COMMON = [\n    "net/bluetooth/bluetooth.ko",\n]\n')
        status, report, env = self.run_gate()
        self.assertEqual(status, 0, report["errors"])
        self.assertEqual(report["from_gki_modules"], {"hci_cmd_sync_status": "net/bluetooth/bluetooth.ko"})
        # Only a source candidate: listed apart, and its CRC is not measured (audit 2026-11-18, T2/T3).
        self.assertEqual(report["gki_module_proof"], {"hci_cmd_sync_status": "source"})
        self.assertIn("(1 via GKI modules: 0 from built .ko, 1 source only); "
                      "CRC differs 0 of 3 compared, 1 not measured", env)
        self.assertEqual(report["crc"]["not_measured"],
                         {"hci_cmd_sync_status": "source-only GKI module export, no CRC in the build"})
        # A GKI module elsewhere does not cover a symbol exported from another directory.
        (self.src / "modules.bzl").write_text('COMMON = ["lib/crypto/libarc4.ko"]\n')
        self.assertEqual(self.run_gate()[0], 1)

    def make_bsp(self, generation="11", mtk="changed_type", config="CONFIG_A=y\nCONFIG_MEDIA_CEC_RC=y\n"):
        bsp = Path(self.temp.name) / "bsp"
        (bsp / "android").mkdir(parents=True, exist_ok=True)
        (bsp / "arch/arm64/configs").mkdir(parents=True, exist_ok=True)
        (bsp / "build.config.common").write_text(f"KMI_GENERATION={generation}\n")
        (bsp / "android/abi_gki_aarch64").write_text("[abi_symbol_list]\n  vendor_used\n")
        (bsp / "android/abi_gki_aarch64_mtk").write_text(f"[abi_symbol_list]\n  {mtk}\n")
        (bsp / "android/abi_gki_aarch64_xiaomi").write_text("[abi_symbol_list]\n")
        (bsp / "arch/arm64/configs/gki_defconfig").write_text(config)
        (self.out / ".config").write_text("CONFIG_A=y\n# CONFIG_MEDIA_CEC_RC is not set\n")
        return bsp

    def run_reference(self, bsp):
        report_file = Path(self.temp.name) / "ref.json"
        status = kc.main(["--device", "rothko", str(self.src), str(self.out), "--reference", str(bsp),
                          "--json", str(report_file)])
        return status, json.loads(report_file.read_text())

    def test_bsp_reference_passes_with_reviewed_config_exceptions(self):
        status, report = self.run_reference(self.make_bsp())
        self.assertEqual(status, 0, report["errors"])
        self.assertEqual(report["references"]["bsp"]["kmi_generation"], "11")
        self.assertEqual(report["references"]["bsp"]["config_not_enabled"],
                         {"CONFIG_MEDIA_CEC_RC": kc.DEVICES["rothko"]["bsp_config_exceptions"]["CONFIG_MEDIA_CEC_RC"]})
        line = kc.summary(report)
        self.assertIn("BSP: generation 11, exported GKI 1/1, mtk 1/1, xiaomi 0/0, config =y not enabled 1 (reviewed)", line)

    def test_module_scmversion_is_a_reviewed_exception_for_both_references(self):
        # build.sh turns LOCALVERSION_AUTO off (Cogan version name), so MODULE_SCMVERSION goes too.
        for kind in ("bsp", "stock"):
            self.assertIn("CONFIG_MODULE_SCMVERSION", kc.DEVICES["rothko"][f"{kind}_config_exceptions"])

    def test_summary_names_unreviewed_config_options(self):
        status, report = self.run_reference(self.make_bsp(config="CONFIG_A=y\nCONFIG_INTERCONNECT=y\n"))
        self.assertEqual(status, 1)
        self.assertIn("config =y not enabled 1 (1 NOT REVIEWED)", kc.summary(report))

    def test_bsp_reference_failures(self):
        for change, message in (({"generation": "8"}, "BSP KMI generation 8"),
                                ({"mtk": "bsp_only_symbol"}, "BSP abi_gki_aarch64_mtk: 1 symbol(s) not exported"),
                                ({"config": "CONFIG_A=y\nCONFIG_INTERCONNECT=y\n"},
                                 "BSP gki_defconfig options not enabled: CONFIG_INTERCONNECT")):
            status, report = self.run_reference(self.make_bsp(**change))
            self.assertEqual(status, 1, message)
            self.assertTrue(any(message in error for error in report["errors"]), report["errors"])

    def test_bsp_only_vendor_hooks_fail_only_when_vendor_modules_use_them(self):
        bsp = self.make_bsp()
        (bsp / "include/trace/hooks").mkdir(parents=True)
        (bsp / "include/trace/hooks/pm_domain.h").write_text(
            "DECLARE_HOOK(android_vh_allow_domain_state,\n\tTP_PROTO(int a), TP_ARGS(a));\n"
            "DECLARE_RESTRICTED_HOOK(android_rvh_shared,\n\tTP_PROTO(int a), TP_ARGS(a), 1);\n")
        (self.src / "include/trace/hooks").mkdir(parents=True)
        (self.src / "include/trace/hooks/sched.h").write_text("DECLARE_RESTRICTED_HOOK(android_rvh_shared, x, y, 1);\n")
        status, report = self.run_reference(bsp)
        self.assertEqual(status, 0, report["errors"])
        self.assertEqual(report["references"]["bsp"]["hooks_absent"],
                         {"android_vh_allow_domain_state": "unused by vendor modules"})
        (bsp / "android/abi_gki_aarch64_mtk").write_text(
            "[abi_symbol_list]\n  changed_type\n  __tracepoint_android_vh_allow_domain_state\n")
        status, report = self.run_reference(bsp)
        self.assertEqual(status, 1)
        self.assertTrue(any("BSP vendor hooks missing but used by vendor modules: android_vh_allow_domain_state" in e
                            for e in report["errors"]), report["errors"])

    def make_stock(self, version="138", config="CONFIG_A=y\nCONFIG_MEMFD_ASHMEM_SHIM=y\n"):
        stock = self.make_bsp(config=config).rename(Path(self.temp.name) / f"stock-{version}")
        (stock / "Makefile").write_text(f"# SPDX\nVERSION = 6\nPATCHLEVEL = 1\nSUBLEVEL = {version}\nEXTRAVERSION =\n")
        (stock / "android/abi_gki_aarch64.stg").write_text(STG)
        return stock

    def run_stocks(self, *stocks):
        report_file = Path(self.temp.name) / "stock.json"
        args = ["--device", "rothko", str(self.src), str(self.out), "--json", str(report_file)]
        for stock in stocks:
            args += ["--stock-reference", str(stock)]
        status = kc.main(args)
        return status, json.loads(report_file.read_text())

    def test_stock_references_pass_with_matching_crcs(self):
        status, report = self.run_stocks(self.make_stock(), self.make_stock("157"))
        self.assertEqual(status, 0, report["errors"])
        self.assertEqual(sorted(report["references"]), ["stock 6.1.138", "stock 6.1.157"])
        self.assertEqual(report["references"]["stock 6.1.157"]["hyperos"], "OS3.0.302.0.WNNIDXM")
        ref = report["references"]["stock 6.1.138"]
        self.assertEqual(ref["hyperos"], "OS3.0.301.0.WNNIDXM")
        self.assertEqual(ref["config_not_enabled"],
                         {"CONFIG_MEMFD_ASHMEM_SHIM": kc.DEVICES["rothko"]["stock_config_exceptions"]["CONFIG_MEMFD_ASHMEM_SHIM"]})
        self.assertEqual(ref["crc_differences"], [])
        self.assertIn("; stock 6.1.138: generation 11, exported GKI 1/1, mtk 1/1, xiaomi 0/0, "
                      "config =y not enabled 1 (reviewed), stock-only vendor hooks 0 (unused), "
                      "CRC differs 0 of 2 compared; stock 6.1.157: generation 11", kc.summary(report))

    def test_a_crc_difference_against_a_stock_frozen_abi_fails(self):
        # The stock frozen ABI is the one that HyperOS version's vendor modules were built with.
        newer = self.make_stock("157")
        (newer / "android/abi_gki_aarch64.stg").write_text(STG.replace("0x0000000a", "0x0000000c"))
        status, report = self.run_stocks(self.make_stock(), newer)
        self.assertEqual(status, 1)
        self.assertEqual(report["errors"], ["stock 6.1.157 CRC differs for 1 symbol(s), e.g. vendor_used"])

    def test_every_supported_hyperos_stock_kernel_must_be_checked(self):
        # Users still on HyperOS OS3.0.301 get the newest kernel too (owner 2026-11-06).
        status, report = self.run_stocks(self.make_stock("157"))
        self.assertEqual(status, 1)
        self.assertIn("stock reference of 6.1.138 (HyperOS OS3.0.301.0.WNNIDXM) not given: "
                      "every supported HyperOS version must be checked", report["errors"])

    def test_a_symbol_only_the_newer_stock_kernel_needs_fails(self):
        newer = self.make_stock("157")
        (newer / "android/abi_gki_aarch64_xiaomi").write_text("[abi_symbol_list]\n  inode_add_lru\n")
        status, report = self.run_stocks(self.make_stock(), newer)
        self.assertEqual(status, 1)
        self.assertEqual(report["errors"], ["stock 6.1.157 abi_gki_aarch64_xiaomi: 1 symbol(s) not exported, "
                                            "e.g. inode_add_lru"])

    def test_stock_reference_must_be_the_stock_kernel(self):
        for change, message in (({"version": "155"}, "stock reference is kernel 6.1.155, the phone's stock kernels "
                                 "are 6.1.138 (HyperOS OS3.0.301.0.WNNIDXM), 6.1.157 (HyperOS OS3.0.302.0.WNNIDXM)"),
                                ({"config": "CONFIG_A=y\nCONFIG_INTERCONNECT=y\n"},
                                 "stock 6.1.138 gki_defconfig options not enabled: CONFIG_INTERCONNECT")):
            self.setUp()
            status, report = self.run_stocks(self.make_stock(**change), self.make_stock("157"))
            errors = report["errors"]
            self.assertEqual(status, 1, message)
            self.assertTrue(any(message in error for error in errors), errors)

    def test_module_symvers_is_the_fallback(self):
        (self.out / "vmlinux.symvers").rename(self.out / "Module.symvers")
        self.assertEqual(self.run_gate()[0], 0)

    def gki_pair(self):
        """Two GKI modules in one directory; only one of them links the exporting file."""
        (self.src / "android/abi_gki_aarch64_mtk").write_text("[abi_symbol_list]\n  changed_type\n  hci_cmd_sync_status\n")
        (self.src / "net/bluetooth").mkdir(parents=True)
        (self.src / "net/bluetooth/hci_sync.c").write_text("EXPORT_SYMBOL(hci_cmd_sync_status);\n")
        (self.src / "modules.bzl").write_text('COMMON = ["net/bluetooth/bluetooth.ko", "net/bluetooth/rfcomm/rfcomm.ko",'
                                              ' "net/bluetooth/hidp.ko"]\n')

    def test_a_built_gki_module_export_is_binary_proof_with_its_crc(self):
        # Module.symvers names the .ko that really exports it, not every module of the directory.
        self.gki_pair()
        (self.out / "Module.symvers").write_text("0x00000005\thci_cmd_sync_status\tnet/bluetooth/hidp\tEXPORT_SYMBOL\t\n")
        status, report, env = self.run_gate()
        self.assertEqual(status, 0, report["errors"])
        self.assertEqual(report["from_gki_modules"], {"hci_cmd_sync_status": "net/bluetooth/hidp.ko"})
        self.assertEqual(report["gki_module_proof"], {"hci_cmd_sync_status": "binary"})
        self.assertEqual(report["crc"]["compared"], 4)
        self.assertIn("(1 via GKI modules: 1 from built .ko, 0 source only); CRC differs 0 of 4 compared (", env)
        # The same directory without Module.symvers: two candidates, only from the source.
        (self.out / "Module.symvers").unlink()
        status, report, _ = self.run_gate()
        self.assertEqual(report["from_gki_modules"],
                         {"hci_cmd_sync_status": "net/bluetooth/bluetooth.ko / net/bluetooth/hidp.ko"})
        self.assertEqual(report["gki_module_proof"], {"hci_cmd_sync_status": "source"})

    def test_a_built_gki_module_with_another_crc_fails(self):
        self.gki_pair()
        (self.out / "Module.symvers").write_text("0x00000099\thci_cmd_sync_status\tnet/bluetooth/bluetooth\tEXPORT_SYMBOL\t\n")
        status, report, _ = self.run_gate()
        self.assertEqual(status, 1)
        self.assertEqual(report["errors"], ["ACK CRC differs for 1 symbol(s), e.g. hci_cmd_sync_status"])

    def test_a_module_outside_modules_bzl_is_no_proof(self):
        # Only GKI modules come from the phone's stock system_dlkm; another built module proves nothing.
        self.gki_pair()
        (self.src / "modules.bzl").write_text('COMMON = ["lib/crypto/libarc4.ko"]\n')
        (self.out / "Module.symvers").write_text("0x00000005\thci_cmd_sync_status\tnet/bluetooth/bluetooth\tEXPORT_SYMBOL\t\n")
        status, report, _ = self.run_gate()
        self.assertEqual(status, 1)
        self.assertEqual(report["lists"]["abi_gki_aarch64_mtk"]["missing"], ["hci_cmd_sync_status"])

    def test_an_empty_frozen_abi_fails_instead_of_crc_differs_0(self):
        # Audit 2026-11-18, T3: an empty STG used to give "CRC differs 0" and exit 0.
        (self.src / "android/abi_gki_aarch64.stg").write_text("")
        status, report, env = self.run_gate()
        self.assertEqual(status, 1)
        self.assertIn("ACK frozen ABI has no symbol CRC (empty or unreadable abi_gki_aarch64.stg)", report["errors"])
        self.assertIn("CRC differs 0 of 0 compared, 3 not measured", env)
        newer = self.make_stock("157")
        (newer / "android/abi_gki_aarch64.stg").write_text("")
        (self.src / "android/abi_gki_aarch64.stg").write_text(STG)
        status, report = self.run_stocks(self.make_stock(), newer)
        self.assertEqual(status, 1)
        self.assertEqual(report["errors"],
                         ["stock 6.1.157 frozen ABI has no symbol CRC (empty or unreadable abi_gki_aarch64.stg)"])

    def test_a_list_symbol_without_a_frozen_crc_fails_unless_a_named_exception(self):
        (self.src / "android/abi_gki_aarch64_xiaomi").write_text("[abi_symbol_list]\n  xiaomi_only\n  no_crc\n")
        (self.out / "vmlinux.symvers").write_text(
            "0x0000000a\tvendor_used\tvmlinux\tEXPORT_SYMBOL\t\n0x0000000b\tchanged_type\tvmlinux\tEXPORT_SYMBOL\t\n"
            "0x00000001\txiaomi_only\tvmlinux\tEXPORT_SYMBOL\t\n0x00000002\tno_crc\tvmlinux\tEXPORT_SYMBOL\t\n")
        status, report, _ = self.run_gate()
        self.assertEqual(status, 1)
        self.assertEqual(report["errors"], ["ACK frozen ABI has no CRC for 1 list symbol(s), e.g. no_crc"])
        spec = kc.DEVICES["rothko"]
        spec["crc_exceptions"] = {"no_crc": "reviewed: why it has no CRC"}
        self.addCleanup(spec.pop, "crc_exceptions")
        status, report, _ = self.run_gate()
        self.assertEqual(status, 0, report["errors"])
        self.assertEqual(report["crc"]["not_measured"], {"no_crc": "reviewed: why it has no CRC"})

    def test_real_frozen_abis_have_no_crc_exceptions(self):
        # Checked 2026-11-18 against the STG and lists of both stock commits and the seven ACK releases of
        # run 43841852829 (138 r17 ... 176 r8): every list symbol has a CRC, so none is excepted.
        self.assertNotIn("crc_exceptions", kc.DEVICES["rothko"])


if __name__ == "__main__":
    unittest.main()

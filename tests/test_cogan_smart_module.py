#!/usr/bin/env python3
"""Offline tests for what joins the two parts of Cogan Smart Kernel into one module:
the installer's migration from the old separate modules, peer detection inside one module folder,
the Action button, uninstall and the WebUI pages.
"""
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_cogan_smart_power import MODULE, SHELL, FakePhone as Power, write
from test_cogan_smart_thermal import FakePhone as Thermal

THEME = r'href="theme\.css(\?v=[\d.]+)?"'   # v2.8.1 adds ?v=<version> so WebView loads the new file


class OneModuleTests(unittest.TestCase):
    """Both parts run from the same module copy, with no CT_MOD / CP_MOD override."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.p = Power(base / "p")
        self.t = Thermal(base / "t")
        self.t.mod = self.p.root / "thermal"
        self.p.env.pop("CT_MOD")
        self.p.env.update(CT_DATA=str(self.t.data))
        self.t.env.update(CP_DATA=str(self.p.data), CT_SYS=str(self.p.sys))

    def tearDown(self):
        self.t.report("stop")
        self.p.report("stop")
        self.tmp.cleanup()

    def test_parts_find_each_other_in_the_same_module(self):
        self.t.report("start")
        status = self.p.report("status")
        self.assertEqual((status["monitor"]["installed"], status["peer"]["installed"], status["peer"]["running"]), (1, 1, 1))
        self.assertRegex(status["peer"]["version"], r"^v\d+(\.\d+){1,2}$")   # v2.7, v2.8.2
        self.assertEqual(json.loads(self.t.report("status"))["power"]["installed"], 1)

    def test_disabled_module_is_not_used_as_monitor(self):
        write(self.p.root / "disable", "")
        self.assertEqual(self.p.report("status")["monitor"]["installed"], 0)

    def test_action_button_switches_mode_and_starts_the_log(self):
        env = dict(self.p.env, CT_SYS=str(self.t.sys), CT_PROC=str(self.t.proc), CT_OUT=str(self.t.out))
        result = subprocess.run([SHELL, str(self.p.root / "action.sh")], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Mode Performa", result.stdout)
        self.assertEqual(self.p.report("status")["config"]["mode"], "game")
        self.assertEqual(json.loads(self.t.report("status"))["running"], 1)

    def test_uninstall_restores_and_removes_both_parts(self):
        adb = Path(self.tmp.name) / "adb"
        self.p.report("set", "MODE", "hemat")
        self.t.run("sampler.sh", "--once")
        env = dict(self.p.env, CS_ADB=str(adb))
        result = subprocess.run([SHELL, str(self.p.root / "uninstall.sh")], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.p.data.exists())
        self.assertFalse(self.t.data.exists())


class DeviceTests(unittest.TestCase):
    """Device ⇄ kernel ⇄ module: both parts report which phone this is and whether the kernel fits it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.p = Power(base / "p")
        self.t = Thermal(base / "t")
        self.t.env.update(CT_SYS=str(self.p.sys), CT_PROC=str(self.p.base / "proc"))
        self.phone("rothko")

    def tearDown(self):
        self.tmp.cleanup()

    def phone(self, codename):
        props = {"sys.boot_completed": "1", "ro.product.device": codename, "ro.product.marketname": "Xiaomi 14T Pro",
                 "ro.product.model": "2407FPN8EG", "ro.board.platform": "mt6989"}
        body = "case \"$1\" in\n" + "".join(f"  {k}) echo '{v}' ;;\n" for k, v in props.items()) + "esac\n"
        for phone in (self.p, self.t):
            write(phone.bin / "getprop", "#!/bin/sh\n" + body)
            (phone.bin / "getprop").chmod(0o755)

    def kernel(self, release):
        write(self.p.base / "proc/sys/kernel/osrelease", release + "\n")
        write(self.p.base / "proc/version", f"Linux version {release} (cogan17@ACK)\n")

    def bridge(self, device, soc="mt6989"):
        root = self.p.sys / "kernel/cogan"
        for name, value in {"abi": "1", "release": "6.1.138-Cogan-Rothko-ACK-r3", "device": device, "soc": soc}.items():
            write(root / name, value + "\n")

    def devices(self):
        return self.p.report("status")["device"], json.loads(self.t.report("status"))["device"]

    def test_kernel_named_for_this_phone_is_a_candidate_without_bridge(self):
        self.kernel("6.1.138-Cogan-Rothko-ACK-r2-6e2dd0510")
        for d in self.devices():
            self.assertEqual((d["codename"], d["name"], d["platform"], d["supported"]), ("rothko", "Xiaomi 14T Pro", "mt6989", 1))
            self.assertEqual((d["kernel_target"], d["match"], d["verified"]), ("rothko", 1, 0))

    def test_kernel_without_device_name_is_unknown(self):
        self.kernel("6.1.177-Cogan-r2-3f08838cb")
        for d in self.devices():
            self.assertEqual((d["kernel_target"], d["match"], d["verified"]), ("", -1, 0))

    def test_bridge_target_is_verified_and_can_disagree(self):
        self.bridge("rothko")
        for d in self.devices():
            self.assertEqual((d["kernel_target"], d["kernel_soc"], d["match"], d["verified"]), ("rothko", "mt6989", 1, 1))
        self.bridge("duchamp")
        for d in self.devices():
            self.assertEqual((d["kernel_target"], d["match"], d["verified"]), ("duchamp", 0, 1))

    def test_other_phone_is_not_claimed_as_supported(self):
        self.phone("degas")
        self.kernel("6.1.138-Cogan-Rothko-ACK-r2-6e2dd0510")
        for d in self.devices():
            self.assertEqual((d["supported"], d["match"]), (0, 0))


class InstallerTests(unittest.TestCase):
    def install(self, adb, modpath):
        script = ('ui_print() { echo "$1"; }; set_perm() { :; }; set_perm_recursive() { :; }\n'
                  f'MODPATH={modpath}\n. {modpath}/customize.sh\n')
        return subprocess.run([SHELL, "-c", script], env=dict(os.environ, CS_ADB=str(adb)),
                              capture_output=True, text=True, timeout=60, check=True).stdout

    def test_migrates_old_settings_and_history_once_and_retires_old_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            adb = Path(tmp)
            write(adb / "cogan_power/config", "MODE=hemat\n")
            write(adb / "cogan_power/switch", "class/power_supply/battery/input_suspend|0|1\n")
            write(adb / "cogan_power/run/pid", "123\n")
            write(adb / "cogan_thermal/data/20261020.tsv", "sample\n")
            write(adb / "cogan_thermal/modes.tsv", "1\tseimbang\n")
            for old in ("cogan_power", "cogan_thermal"):
                write(adb / f"modules/{old}/module.prop", f"id={old}\n")
            out = self.install(adb, MODULE)
            new = adb / "cogan_smart"
            self.assertEqual((new / "power/config").read_text(), "MODE=hemat\n")
            self.assertTrue((new / "power/switch").is_file())
            self.assertFalse((new / "power/run").exists())
            self.assertEqual((new / "thermal/data/20261020.tsv").read_text(), "sample\n")
            self.assertTrue((new / "thermal/modes.tsv").is_file())
            self.assertTrue((adb / "modules/cogan_power/remove").is_file())
            self.assertTrue((adb / "modules/cogan_thermal/remove").is_file())
            self.assertIn("disalin dari", out)
            # An update must not overwrite what the merged module has written since.
            write(new / "power/config", "MODE=game\n")
            self.install(adb, MODULE)
            self.assertEqual((new / "power/config").read_text(), "MODE=game\n")

    def test_fresh_install_creates_data_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            adb = Path(tmp)
            self.install(adb, MODULE)
            self.assertTrue((adb / "cogan_smart/power").is_dir())
            self.assertTrue((adb / "cogan_smart/thermal/data").is_dir())
            self.assertFalse((adb / "modules").exists())


class WebUITests(unittest.TestCase):
    def test_each_page_calls_an_existing_script_and_links_the_others(self):
        pages = ("index.html", "thermal.html", "modules.html")
        for page in pages:
            html = (MODULE / "webroot" / page).read_text()
            report = re.search(r"const REPORT = '/data/adb/modules/cogan_smart/(.+?)';", html).group(1)
            self.assertTrue((MODULE / report).is_file(), report)
            for other in pages:
                self.assertIn(f'href="{other}"', html)
            self.assertIn(f'href="{page}" aria-current="page"', html)
            self.assertIn('href="about.html"', html)
            self.assertRegex(html, THEME)
        about = (MODULE / "webroot/about.html").read_text()
        self.assertRegex(about, THEME)
        for page in pages:
            self.assertIn(f'href="{page}"', about)

    def test_one_shared_bridge_and_client(self):
        self.assertTrue((MODULE / "bridge.sh").is_file())
        self.assertTrue((MODULE / "webroot/client.js").is_file())
        self.assertEqual(sorted(p.relative_to(MODULE).as_posix() for p in MODULE.rglob("bridge.sh")), ["bridge.sh"])
        self.assertFalse(list(MODULE.glob("*/module.prop")))


if __name__ == "__main__":
    unittest.main()

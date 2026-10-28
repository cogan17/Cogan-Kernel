"""Manager against a fake phone: native identity, governors, live ZRAM and app evidence."""
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from test_cogan_smart_power import MODULE, SHELL, write


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.module = self.base / "module"
        shutil.copytree(MODULE, self.module, ignore=shutil.ignore_patterns("rilis"))
        self.sys = self.base / "sys"
        self.proc = self.base / "proc"
        self.data = self.base / "manager"
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, CM_SYS=str(self.sys), CM_PROC=str(self.proc),
                        CM_DATA=str(self.data), PATH=f"{self.bin}:{os.environ['PATH']}")
        self.tool("getprop", 'case "$1" in ro.product.device) echo rothko;; ro.board.platform) echo mt6989;; esac')
        for name, value in {"abi": "1", "device": "rothko", "soc": "mt6989", "release": "6.1.176-Cogan-rothko"}.items():
            write(self.sys / "kernel/cogan" / name, value + "\n")
        write(self.proc / "sys/kernel/random/boot_id", "boot-one\n")
        for policy in ("policy0", "policy4"):
            p = self.sys / "devices/system/cpu/cpufreq" / policy
            write(p / "scaling_available_governors", "schedutil sugov_ext performance\n")
            write(p / "scaling_governor", "schedutil\n")
        self.zram = self.sys / "block/zram0"
        write(self.zram / "comp_algorithm", "[lz4] zstd\n")
        write(self.zram / "initstate", "1\n")

    def tearDown(self):
        self.tmp.cleanup()

    def tool(self, name, body):
        p = self.bin / name
        write(p, "#!/bin/sh\n" + body + "\n")
        p.chmod(0o755)

    def report(self, *args):
        r = subprocess.run([SHELL, str(self.module / "manager/report.sh"), *args], env=self.env,
                           text=True, capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout) if r.stdout.strip() else None

    def governors(self):
        return [p.read_text().strip() for p in sorted(self.sys.glob("devices/system/cpu/cpufreq/*/scaling_governor"))]

    def devfreq(self, name, driver, current, available):
        p = self.sys / "class/devfreq" / name
        write(p / "governor", current + "\n")
        write(p / "available_governors", available + "\n")
        target = self.sys / "bus/platform/drivers" / driver
        target.mkdir(parents=True, exist_ok=True)
        (p / "device").mkdir()
        (p / "device/driver").symlink_to(target)
        return p

    def test_identity_preflight_and_all_cpu_policies(self):
        write(self.sys / "kernel/cogan/soc", "mediatek,MT6989\n")
        self.assertEqual(self.report("status")["writable"], 1)
        write(self.sys / "kernel/cogan/device", "other\n")
        self.assertEqual(self.report("apply", "sugov_ext", "default", "0")["ok"], 0)
        self.assertEqual(self.governors(), ["schedutil", "schedutil"])
        write(self.sys / "kernel/cogan/device", "rothko\n")
        write(self.sys / "devices/system/cpu/cpufreq/policy4/scaling_available_governors", "schedutil\n")
        self.assertEqual(self.report("apply", "sugov_ext", "default", "0")["ok"], 0)
        self.assertEqual(self.governors(), ["schedutil", "schedutil"])
        self.assertFalse((self.data / "config").exists())

    def test_cpu_restore_preserves_other_controllers(self):
        self.assertEqual(self.report("apply", "sugov_ext", "default", "0")["ok"], 1)
        self.assertEqual(self.governors(), ["sugov_ext", "sugov_ext"])
        write(self.sys / "devices/system/cpu/cpufreq/policy4/scaling_governor", "performance\n")
        self.report("reset")
        self.assertEqual(self.governors(), ["schedutil", "performance"])

    def test_rejected_path_rolls_back_prior_cpu_writes(self):
        outside = self.base / "outside"
        write(outside, "schedutil\n")
        p = self.sys / "devices/system/cpu/cpufreq/policy4/scaling_governor"
        p.unlink()
        p.symlink_to(outside)
        self.assertEqual(self.report("apply", "sugov_ext", "default", "0")["ok"], 0)
        self.assertEqual(self.governors(), ["schedutil", "schedutil"])

    def test_boot_boundary_discards_old_ownership(self):
        self.report("apply", "sugov_ext", "default", "1")
        write(self.proc / "sys/kernel/random/boot_id", "boot-two\n")
        for p in self.sys.glob("devices/system/cpu/cpufreq/*/scaling_governor"):
            write(p, "performance\n")
        self.report("boot")
        self.report("reset")
        self.assertEqual(self.governors(), ["performance", "performance"])

    def test_active_zram_is_pending_and_never_reset(self):
        self.tool("swapoff", "exit 99")
        self.tool("mkswap", "exit 99")
        before = (self.zram / "comp_algorithm").read_text()
        status = self.report("apply", "default", "heavy", "1")
        self.assertEqual(status["config"]["ram"], "heavy")
        self.assertEqual(status["zram"][0]["current"], "lz4")
        self.assertEqual((self.zram / "comp_algorithm").read_text(), before)
        self.assertFalse((self.zram / "reset").exists())
        self.assertEqual(status["bw_hwmon"], [])
        self.assertEqual(status["ram_state"], "pending_boot")
        write(self.zram / "initstate", "0\n")
        self.report("early")
        self.assertEqual((self.zram / "comp_algorithm").read_text().strip(), "zstd")
        write(self.zram / "initstate", "1\n")
        self.assertEqual(self.report("reset")["restore_pending"], 1)
        self.assertEqual((self.zram / "comp_algorithm").read_text().strip(), "zstd")
        write(self.zram / "initstate", "0\n")
        self.assertEqual(self.report("reset")["restore_pending"], 0)
        self.assertEqual((self.zram / "comp_algorithm").read_text().strip(), "lz4")

    def test_bw_hwmon_only_when_driver_offers_it(self):
        mem = self.devfreq("mtk-dvfsrc-devfreq", "mtk-dvfsrc-devfreq", "userspace", "bw_hwmon userspace")
        # The same global governor list is also exposed on storage and GPU.
        gpu = self.devfreq("13000000.mali", "mali", "dummy", "bw_hwmon userspace")
        ufs = self.devfreq("112b0000.ufshci", "ufshcd-mtk", "simple_ondemand", "bw_hwmon userspace")
        self.report("apply", "default", "snappy", "0", "bw_hwmon")
        self.assertEqual((mem / "governor").read_text().strip(), "bw_hwmon")
        self.assertEqual((gpu / "governor").read_text().strip(), "dummy")
        self.assertEqual((ufs / "governor").read_text().strip(), "simple_ondemand")
        self.report("reset")
        self.assertEqual((mem / "governor").read_text().strip(), "userspace")

    def test_rothko_dram_driver_is_identified_without_guessing_a_governor(self):
        available = "dummy apupassive-pe apuconstrain apuuser apupassive userspace powersave performance simple_ondemand"
        mem = self.devfreq("mtk-dvfsrc-devfreq", "mtk-dvfsrc-devfreq", "userspace", available)
        self.devfreq("13000000.mali", "mali", "dummy", available)
        self.devfreq("112b0000.ufshci", "ufshcd-mtk", "simple_ondemand", available)
        # A memory-looking name is insufficient without the correct driver binding.
        self.devfreq("memory", "ufshcd-mtk", "simple_ondemand", "bw_hwmon userspace")
        s = self.report("status")
        self.assertEqual(s["dram"], [{"name": mem.name, "driver": "mtk-dvfsrc-devfreq", "current": "userspace", "available": available}])
        self.assertEqual(s["bw_hwmon"], [])
        self.assertEqual(self.report("apply", "sugov_ext", "snappy", "0", "bw_hwmon")["ok"], 0)
        self.assertFalse((self.data / "config").exists())
        self.assertEqual(self.governors(), ["schedutil", "schedutil"])
        self.report("apply", "default", "snappy", "0")
        self.assertEqual((mem / "governor").read_text().strip(), "userspace")

    def test_ram_and_bandwidth_are_independent_and_missing_bw_is_an_error(self):
        mem = self.devfreq("memory", "mtk-dvfsrc-devfreq", "performance", "bw_hwmon performance")
        s = self.report("apply", "default", "snappy", "0")
        self.assertEqual((s["config"]["bw"], s["ram_state"]), ("default", "matching"))
        self.assertEqual((mem / "governor").read_text().strip(), "performance")
        self.report("apply", "default", "default", "0", "bw_hwmon")
        self.assertEqual((mem / "governor").read_text().strip(), "bw_hwmon")
        # Old config has no separate BW key. It must follow the system, restoring old ownership.
        config = self.data / "config"
        config.write_text("\n".join(l for l in config.read_text().splitlines() if not l.startswith("BW=")) + "\n")
        self.assertEqual(self.report("status")["config"]["bw"], "default")
        self.report("apply", "default", "snappy", "0")
        self.assertEqual((mem / "governor").read_text().strip(), "performance")
        write(mem / "available_governors", "performance\n")
        before = (self.data / "config").read_text()
        self.assertEqual(self.report("apply", "sugov_ext", "snappy", "0", "bw_hwmon")["ok"], 0)
        self.assertEqual((self.data / "config").read_text(), before)
        self.assertEqual(self.governors(), ["schedutil", "schedutil"])

    def test_ram_reports_a_failed_boot_without_claiming_success_or_resetting_zram(self):
        before = (self.zram / "comp_algorithm").read_text()
        self.assertEqual(self.report("apply", "default", "heavy", "0")["ram_state"], "needs_boot")
        self.assertEqual(self.report("set", "default", "heavy", "1")["ram_state"], "pending_boot")
        self.report("boot")
        self.assertEqual(self.report("status")["ram_state"], "blocked")
        self.assertEqual((self.zram / "comp_algorithm").read_text(), before)
        self.assertFalse((self.zram / "reset").exists())
        self.assertEqual(self.report("set", "default", "snappy", "1")["ram_state"], "matching")
        write(self.proc / "sys/kernel/random/boot_id", "new-boot\n")
        self.assertEqual(self.report("set", "default", "heavy", "1")["ram_state"], "pending_boot")

    def test_ram_status_distinguishes_selected_compression_from_active_swap(self):
        self.report("set", "default", "snappy", "0")
        self.assertEqual(self.report("status")["zram"][0]["swap_active"], -1)
        write(self.proc / "swaps", "Filename Type Size Used Priority\n/dev/block/zram0 partition 1000 10 -2\n")
        self.assertEqual(self.report("status")["zram"][0]["swap_active"], 1)
        write(self.proc / "swaps", "Filename Type Size Used Priority\n")
        self.assertEqual(self.report("status")["zram"][0]["swap_active"], 0)
        write(self.proc / "swaps", "")
        self.assertEqual(self.report("status")["zram"][0]["swap_active"], -1)

    def test_invalid_settings_cannot_reach_a_shell(self):
        self.assertEqual(self.report("apply", "schedutil;id", "default", "0")["ok"], 0)
        self.assertEqual(self.report("set", "schedutil", "heavy", "2")["ok"], 0)
        self.assertEqual(self.report("apply", "schedutil", "snappy", "0", "bw_hwmon;id")["ok"], 0)
        self.assertEqual(self.governors(), ["schedutil", "schedutil"])

    def init_daemon(self, broken=False):
        self.tool("ksud", 'case "$1 $2" in "initrc --help") echo refresh;; "initrc refresh") '
                  + ('echo "synthetic refresh failure" >&2; exit 42' if broken else
                     'echo refresh >> ' + shlex.quote(str(self.base / "refreshes"))) + ';; *) exit 1;; esac')
        self.env["CM_KSUD"] = str(self.bin / "ksud")
        self.env["CM_DEV"] = str(self.base / "dev")
        (self.base / "dev").mkdir(exist_ok=True)
        self.tool("id", 'echo u:r:ksu:s0')

    def run_init_command(self):
        rc = self.module / "initrc/cogan-zram.rc"
        commands = [shlex.split(l) for l in rc.read_text().splitlines() if l.strip().startswith("exec ")]
        self.assertEqual(len(commands), 3)
        self.assertIn('property:ro.product.device=rothko', rc.read_text())
        self.assertIn('property:ro.board.platform=mt6989', rc.read_text())
        cmd = commands[-1]
        self.assertEqual(cmd[1:7], ['u:r:ksu:s0', 'root', 'root', '--', '/system/bin/sh', '-c'])
        # init unescapes $$ before invoking sh. Map only filesystem roots for this fake phone.
        script = cmd[7].replace('$$', '$').replace('/sys/', str(self.sys) + '/')
        script = script.replace('/dev/.cogan_smart_zram_init', str(self.base / 'dev/.cogan_smart_zram_init'))
        r = subprocess.run([SHELL, '-c', script, *cmd[8:]], capture_output=True, text=True, timeout=5)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_native_init_runs_before_initialization_and_leaves_active_zram_alone(self):
        self.init_daemon()
        before = (self.zram / "comp_algorithm").read_text()
        self.assertEqual(self.report("set", "default", "heavy", "1")["init_state"], "ready")
        self.run_init_command()
        self.assertEqual((self.zram / "comp_algorithm").read_text(), before)
        self.assertEqual(self.report("status")["init_seen"], "zstd post-fs pending")
        write(self.zram / "initstate", "0\n")
        self.run_init_command()
        self.assertEqual((self.zram / "comp_algorithm").read_text().strip(), "zstd")
        self.assertEqual(self.report("status")["init_seen"], "zstd post-fs matching")
        self.assertFalse((self.zram / "reset").exists())

    def test_native_init_guards_all_devices_and_identity_and_clears_disabled_boot(self):
        self.init_daemon()
        self.report("set", "default", "heavy", "1")
        refreshes = (self.base / "refreshes").read_text()
        self.report("set", "schedutil", "heavy", "1")
        self.assertEqual((self.base / "refreshes").read_text(), refreshes)
        write(self.zram / "initstate", "0\n")
        write(self.sys / "block/zram1/comp_algorithm", "[lz4]\n")
        write(self.sys / "block/zram1/initstate", "0\n")
        self.run_init_command()
        self.assertEqual((self.zram / "comp_algorithm").read_text(), "[lz4] zstd\n")
        self.assertEqual(self.report("status")["init_seen"], "zstd post-fs unsupported")
        marker = self.base / "dev/.cogan_smart_zram_init"
        marker.unlink()
        write(self.sys / "kernel/cogan/device", "other\n")
        self.run_init_command()
        self.assertFalse(marker.exists())
        write(self.sys / "kernel/cogan/device", "rothko\n")
        self.report("set", "default", "snappy", "0")
        self.assertFalse((self.module / "initrc/cogan-zram.rc").exists())

    def test_native_refresh_failure_rolls_back_rc_and_reports_saved_settings(self):
        self.init_daemon()
        self.report("set", "default", "heavy", "1")
        rc = self.module / "initrc/cogan-zram.rc"
        old = rc.read_bytes()
        self.init_daemon(broken=True)
        self.assertEqual(self.report("set", "default", "snappy", "1")["ok"], 0)
        self.assertEqual(rc.read_bytes(), old)
        s = self.report("status")
        self.assertEqual((s["config"]["ram"], s["init_state"]), ("snappy", "error"))
        self.assertIn('synthetic refresh failure', s["init_error"])
        self.init_daemon()
        self.report("reset")
        self.assertFalse(rc.exists())

    def test_mmd_uses_native_setup_property_without_enabling_the_daemon(self):
        self.tool("getprop", 'case "$1" in ro.product.device) echo rothko;; ro.board.platform) echo mt6989;; mmd.zram.enabled) echo true;; esac')
        s = self.report("set", "default", "heavy", "1")
        self.assertEqual(s["init_state"], "mmd")
        prop = self.module / "system.prop"
        self.assertEqual(prop.read_text(), 'mmd.zram.comp_algorithm=zstd\n')
        self.report("set", "default", "heavy", "0")
        self.assertFalse(prop.exists())

    def test_init_preserves_unrelated_properties_and_rc_files(self):
        self.init_daemon()
        prop = self.module / "system.prop"
        prop.write_text('owner.custom=value\n')
        self.assertEqual(self.report("set", "default", "heavy", "1")["ok"], 0)
        self.assertEqual(prop.read_text(), 'owner.custom=value\n')
        prop.unlink()
        rc = self.module / "initrc/cogan-zram.rc"
        write(rc, '# owner custom init action\n')
        self.assertEqual(self.report("set", "default", "heavy", "1")["ok"], 0)
        self.assertEqual(rc.read_text(), '# owner custom init action\n')
        self.assertEqual(self.report("status")["init_state"], 'error')

    def test_pending_update_cannot_silently_override_the_boot_selection(self):
        self.init_daemon()
        self.report("apply", "sugov_ext", "heavy", "1")
        old = (self.data / "config").read_bytes()
        adb = self.base / "adb"
        self.env['CS_ADB'] = str(adb)
        write(adb / 'modules_update/cogan_smart/module.prop', 'id=cogan_smart\n')
        result = self.report("set", "default", "snappy", "1")
        self.assertEqual(result['ok'], 0)
        self.assertIn('Pembaruan modul', result['error'])
        self.assertEqual((self.data / "config").read_bytes(), old)
        # Reset still restores live controls even if pending-update cache sync is blocked.
        self.assertEqual(self.report('reset')['ok'], 0)
        self.assertEqual(self.governors(), ['schedutil', 'schedutil'])

    def app_fixture(self):
        now = int(time.time())
        apps = ["app.old", "app.new", "app.recent", "app.service", "app.running", "app.unknown", "app.profile"]
        self.tool("pm", "printf '%s\\n' " + " ".join(shlex.quote("package:" + p) for p in apps))
        self.tool("am", 'if [ "$1" = get-current-user ]; then echo 0; else printf "%s\\n" "$@" > ' + shlex.quote(str(self.base / "intent")) + "; fi")
        self.tool("ps", "echo app.running:service")
        packages = ""
        for p in apps:
            date = time.strftime("%Y-%m-%d %H:%M:%S") if p == "app.new" else "2020-01-01 00:00:00"
            packages += f"  Package [{p}] (abc):\n    firstInstallTime={date}\n    User 0: installed=true\n"
        write(self.base / "packages", packages)
        usage = "user=0\nIn-memory yearly stats\n"
        for p in apps:
            if p in ("app.unknown", "app.profile"):
                continue
            last = now - (86400 if p == "app.recent" else 8 * 86400)
            usage += f"  package={p} totalTimeUsed=100 lastTimeUsed={last*1000} lastTimeVisible={last*1000} lastTimeFS={(now if p=='app.service' else 0)*1000}\n"
        usage += f"user=10\n package=app.profile lastTimeUsed={(now-9*86400)*1000}\n"
        write(self.base / "usage", usage)
        self.tool("dumpsys", '[ "$1 $2" = "-t 20" ] || exit 99\nshift 2\ncase "$1" in usagestats) cat ' + shlex.quote(str(self.base / "usage")) +
                  " " + ";; package) cat " + shlex.quote(str(self.base / "packages")) + ";; esac")

    def test_unused_apps_need_positive_evidence_in_the_current_user(self):
        self.app_fixture()
        result = self.report("scan")
        self.assertEqual([a["package"] for a in result["apps"]], ["app.old"])
        self.assertEqual(result["total"], 7)
        self.assertEqual(result["unknown"], 2)
        self.assertEqual(result["apps"][0]["idle_days"], 8)
        self.assertEqual(self.report("app", "app.old")["ok"], 1)
        intent = (self.base / "intent").read_text()
        self.assertIn("android.settings.APPLICATION_DETAILS_SETTINGS", intent)
        self.assertIn("package:app.old", intent)
        self.assertEqual(self.report("app", "system.foo")["ok"], 0)
        self.assertEqual(self.report("app", "app.old;id")["ok"], 0)

    def test_missing_usage_is_unknown_not_a_removal_list(self):
        self.app_fixture()
        write(self.base / "usage", "Permission Denial\n")
        self.assertEqual(self.report("scan")["ok"], 0)

    def test_scan_rejects_failed_empty_denied_and_truncated_reads(self):
        for stage, label in [("list", "daftar aplikasi"), ("usage", "riwayat pemakaian"),
                             ("packages", "tanggal pemasangan"), ("running", "proses berjalan")]:
            for failure in ("exit", "timeout", "denied", "empty"):
                with self.subTest(stage=stage, failure=failure):
                    self.app_fixture()
                    # One fake timeout supervises the existing Android fixtures without waiting.
                    # This catches failures from every command, including ps, with no hardware.
                    body = ('file=list; case "$1" in 25) file=usage; [ "$5" = package ] && file=packages;; '
                            '10) file=running;; esac\nshift\n')
                    injected = {"exit": 'echo \'synthetic: "read failed"\' >&2; exit 42',
                                "timeout": '"$@"; echo "*** SERVICE DUMP TIMEOUT EXPIRED ***"; exit 0',
                                "denied": '"$@"; echo "Permission Denial: synthetic" >&2; exit 0',
                                "empty": 'exit 0'}[failure]
                    self.tool("timeout", body + 'if [ "$file" = ' + stage + ' ]; then ' + injected + '; fi\nexec "$@"')
                    result = self.report("scan")
                    self.assertEqual(result["ok"], 0, result)
                    self.assertNotIn("apps", result)
                    self.assertIn(label, result["error"])
                    if failure == "exit":
                        self.assertIn('kode 42', result["error"])
                        self.assertIn('"read failed"', result["error"])
                    self.assertFalse(list(self.data.glob("scan.*")))
                    self.assertFalse((self.data / "api.lock").exists())
        (self.bin / "timeout").unlink()
        self.assertEqual([a["package"] for a in self.report("scan")["apps"]], ["app.old"])

    def test_webui_drafts_and_concurrent_native_callbacks(self):
        r = subprocess.run(["node", "tests/cogan_smart_client_check.js"], cwd=MODULE.parents[1],
                           capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()

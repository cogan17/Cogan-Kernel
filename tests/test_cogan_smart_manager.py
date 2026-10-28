"""Manager against a fake phone: native identity, governors, live ZRAM and app evidence."""
import json
import os
import shlex
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
        r = subprocess.run([SHELL, str(MODULE / "manager/report.sh"), *args], env=self.env,
                           text=True, capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout) if r.stdout.strip() else None

    def governors(self):
        return [p.read_text().strip() for p in sorted(self.sys.glob("devices/system/cpu/cpufreq/*/scaling_governor"))]

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
        mem = self.sys / "class/devfreq/memory"
        gpu = self.sys / "class/devfreq/mali"
        for p in (mem, gpu):
            write(p / "available_governors", "bw_hwmon performance\n")
            write(p / "governor", "performance\n")
        self.report("apply", "default", "snappy", "0")
        self.assertEqual((mem / "governor").read_text().strip(), "bw_hwmon")
        self.assertEqual((gpu / "governor").read_text().strip(), "performance")
        self.report("reset")
        self.assertEqual((mem / "governor").read_text().strip(), "performance")

    def test_invalid_settings_cannot_reach_a_shell(self):
        self.assertEqual(self.report("apply", "schedutil;id", "default", "0")["ok"], 0)
        self.assertEqual(self.report("set", "schedutil", "heavy", "2")["ok"], 0)
        self.assertEqual(self.governors(), ["schedutil", "schedutil"])

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

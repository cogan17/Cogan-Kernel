#!/usr/bin/env python3
"""Offline tests for the Aplikasi tab of Cogan Smart Kernel (apps/report.sh + apps.awk) against a fake phone:
a scam APK from WhatsApp that made itself device admin, the APK copy it came from, the root manager app,
and the block that takes the install right back from chat apps."""
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from test_cogan_smart_power import AWK, MODULE, SHELL, write

SCAM = "id.scam.undangan"
APPS = ["com.whatsapp", SCAM, "com.bank.app", "com.tool.file", "com.rifsxd.ksunext", "com.tasker", "app.old"]


class AppsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.module = self.base / "module"
        shutil.copytree(MODULE, self.module, ignore=shutil.ignore_patterns("rilis"))
        self.bin, self.state, self.root = self.base / "bin", self.base / "state", self.base / "root"
        self.bin.mkdir(); self.state.mkdir()
        os.symlink(AWK, self.bin / "awk")   # Android's awk is one-true-awk
        self.data = self.base / "adb/cogan_smart/apps"
        self.env = dict(os.environ, CS_ADB=str(self.base / "adb"), CA_ROOT=str(self.root), CA_SLEEP="1", CA_HOST_UID="10999",
                        PATH=f"{self.bin}:{os.environ['PATH']}")
        now = int(time.time())
        q = lambda p: shlex.quote(str(p))
        write(self.state / "installed", "".join(f"package:{p}\n" for p in APPS))
        write(self.state / "admins", f"  {SCAM}/.Admin\n")
        write(self.state / "allowed", "com.whatsapp\ncom.android.chrome\ncom.google.android.gm\n")
        write(self.state / "0.enabled_accessibility_services", f"{SCAM}/.Spy:com.tasker/.Service")
        write(self.state / "0.enabled_notification_listeners", f"{SCAM}/.Otp")
        packages = "Packages:\n"
        meta = {"com.whatsapp": ("com.android.vending", "com.android.vending", 2), SCAM: ("com.miui.packageinstaller", "com.whatsapp", 3),
                "com.bank.app": ("com.android.vending", "com.android.vending", 2), "com.tool.file": ("com.miui.packageinstaller", "com.android.chrome", 4),
                "com.rifsxd.ksunext": ("null", "null", 0), "com.tasker": ("com.android.vending", "com.android.vending", 2),
                "app.old": ("com.xiaomi.market", "null", 0)}
        for i, p in enumerate(APPS):
            inst, init, src = meta[p]
            packages += (f"  Package [{p}] (abc{i}):\n    appId={10200 + i}\n    pkg=Package{{x {p}}}\n"
                         f"    codePath=/data/app/~~x/{p}-1\n    installerPackageName={inst}\n    installerPackageUid=-1\n"
                         f"    initiatingPackageName={init}\n    originatingPackageName=null\n    packageSource={src}\n"
                         f"    User 0: ceDataInode=1 installed=true hidden=false suspended=false\n      installReason=0\n"
                         f"      firstInstallTime={'2020-01-01 00:00:00' if p == 'app.old' else time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                         + ("      runtime permissions:\n        android.permission.READ_SMS: granted=true, flags=[ USER_SET ]\n"
                            "        android.permission.CAMERA: granted=true, flags=[ USER_SET ]\n" if p == SCAM else "")
                         + "    User 999: ceDataInode=2 installed=true hidden=false\n      firstInstallTime=2020-01-01 00:00:00\n"
                         + ("        android.permission.RECEIVE_SMS: granted=true\n" if p == "com.bank.app" else ""))
        # Gmail is a system app: not a user app, but still a source the block covers.
        packages += "  Package [com.google.android.gm] (gm):\n    appId=10150\n    pkgFlags=[ SYSTEM ]\n"
        # A shared user section after the packages must not lend its permissions to the last package.
        packages += "\nShared users:\n  SharedUser [android.uid.phone] (x):\n    User 0:\n      android.permission.READ_SMS: granted=true\n"
        write(self.base / "packages", packages)
        usage = "user=0\n" + "".join(f"  package={p} lastTimeUsed={(now - (10 if p == 'app.old' else 1) * 86400) * 1000}\n" for p in APPS)
        write(self.base / "usage", usage)
        write(self.base / "appops", f"""Current AppOps Service state:
  Uid u0a201:
    state=cch
    Package {SCAM}:
      CAMERA (allow):
        Access: [fg-s] 2026-10-29 10:00:00.000 (-1h2m3s4ms)
      READ_SMS (allow):
        Access: [bg-s] 2026-10-29 11:00:00.000 (-2m5s)
        Access: [fg-s] 2026-10-29 10:00:00.000 (-1d0h0m0s)
      SYSTEM_ALERT_WINDOW (allow):
  Uid u0a203:
    Package com.tool.file:
      SYSTEM_ALERT_WINDOW (allow):
      REQUEST_INSTALL_PACKAGES (allow):
  Uid u999a201:
    Package {SCAM}:
      RECORD_AUDIO (allow):
        Access: [fg-s] 2026-10-29 11:00:00.000 (-5s)
Discrete accesses:
  Uid: 10202
    Package com.bank.app:
      CAMERA (allow):
        Access: [fg-s] 2026-10-29 11:00:00.000 (-1s)
""")
        write(self.base / "battery", "  Estimated power use (mAh):\n    UID u0a201: 12.5 ( fg: cpu=1 )\n    UID u0a202: 3.25 ( cpu=2 )\n    UID 1000: 99 ( )\n")
        week = now - 3 * 86400
        write(self.base / "net", f"""Dev stats:
  ident=[{{type=WIFI}}] uid=-1 set=ALL tag=0x0
    NetworkStatsHistory: bucketDuration=7200
      st={week} rb=999999 rp=1 tb=999999 tp=1 op=0
UID stats:
  Pending bytes: 10
  Complete history:
  ident=[{{type=MOBILE, subId=1}}] uid=10201 set=DEFAULT tag=0x0
    NetworkStatsHistory: bucketDuration=7200
      st={now - 30 * 86400} rb=5000000 rp=1 tb=5000000 tp=1 op=0
      st={week} rb=1500 rp=1 tb=500 tp=1 op=0
  ident=[{{type=WIFI}}] uid=10201 set=FOREGROUND tag=0x0
    NetworkStatsHistory: bucketDuration=7200
      st={week} rb=3000 rp=1 tb=1000 tp=1 op=0
""")
        write(self.base / "launcher", "".join(f"{p}/.Main\n" for p in APPS if p != SCAM))
        self.tool("timeout", 'shift\nexec "$@"')
        self.tool("getprop", 'case "$1" in sys.boot_completed) echo 1;; esac')
        self.tool("ps", f"echo ARGS\necho {SCAM}:remote\necho com.bank.app")
        self.tool("am", f'case "$1" in get-current-user) echo 0;; force-stop) echo "$*" >> {q(self.state / "log")};; esac')
        self.tool("dumpsys", f"""[ "$1" = -t ] && shift 2
case "$1" in
  package) if [ "$2" = packages ]; then cat {q(self.base / "packages")}; else grep -A1 "Package \\[$2\\]" {q(self.base / "packages")} | grep appId; fi ;;
  usagestats) cat {q(self.base / "usage")} ;;
  appops) cat {q(self.base / "appops")} ;;
  batterystats) cat {q(self.base / "battery")} ;;
  netstats) cat {q(self.base / "net")} ;;
  device_policy) echo "Current Device Policy Manager state:"; echo "Enabled Device Admins (User 0, provisioningState: 3):"
    sed 's/$/:/' {q(self.state / "admins")}; echo "  mPasswordOwner=-1" ;;
esac""")
        self.tool("cmd", f"""case "$1 $2" in
  "package query-activities") cat {q(self.base / "launcher")} ;;
  "appops query-op") cat {q(self.state / "allowed")} ;;
  "appops set") echo "$*" >> {q(self.state / "log")}; grep -v -x -F "$5" {q(self.state / "allowed")} > {q(self.state / "a.tmp")}; mv {q(self.state / "a.tmp")} {q(self.state / "allowed")} ;;
  "notification post") echo "notify $*" >> {q(self.state / "log")} ;;
esac""")
        self.tool("settings", f"""f={q(self.state)}/"$2.$5"
case "$3" in get) cat "$f" 2>/dev/null || echo null ;; put) printf '%s' "$6" > "$f" ;; esac""")
        self.tool("pm", f"""case "$1" in
  list) case "$2" in
      users) printf 'Users:\\n\\tUserInfo{{0:Owner:c13}} running\\n\\tUserInfo{{999:XSpace:801010}}\\n' ;;
      packages) cat {q(self.state / "installed")} ;; esac ;;
  path) echo "package:/data/app/~~x/$4-1/base.apk" ;;
  disable) echo "disable $*" >> {q(self.state / "log")}; pkg=${{4%%/*}}; grep -v -F " $pkg/" {q(self.state / "admins")} > {q(self.state / "d.tmp")}; mv {q(self.state / "d.tmp")} {q(self.state / "admins")} ;;
  uninstall) if grep -q -F " $2/" {q(self.state / "admins")}; then echo "Failure [DELETE_FAILED_DEVICE_POLICY_MANAGER]"; exit 1; fi
    grep -v -x -F "package:$2" {q(self.state / "installed")} > {q(self.state / "i.tmp")}; mv {q(self.state / "i.tmp")} {q(self.state / "installed")}
    rm -rf {q(self.root)}/data/app/~~x/"$2"-1; echo Success ;;
esac""")
        # The APK as installed, its copy received in WhatsApp (a path with spaces) and a different APK of the same size.
        write(self.root / f"data/app/~~x/{SCAM}-1/base.apk", "SCAM-APK-BYTES")
        self.copy = self.root / "data/media/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Documents/Undangan Nikah.APK"
        write(self.copy, "SCAM-APK-BYTES")
        self.other = self.root / "data/media/0/Download/game.apk"
        write(self.other, "OTHER-APK-BYTE")
        for d in [f"data/data/{SCAM}", f"data/user/999/{SCAM}", f"data/user_de/0/{SCAM}", f"data/media/0/Android/data/{SCAM}",
                  f"data/media/999/Android/obb/{SCAM}", f"data/misc/profiles/cur/0/{SCAM}"]:
            write(self.root / d / "x", "x")
        write(self.root / f"data/data/{SCAM}.other/keep", "x")   # a longer name must stay

    def tearDown(self):
        self.report("stop")
        self.tmp.cleanup()

    # Binder hands a command's stdout and stderr to system_server; SELinux allows a pipe or /dev/null, not a file in
    # /data/adb, and cmd then fails like on the owner's phone (29 Oct). The fakes of Binder commands do the same.
    BINDER = ("pm", "cmd", "dumpsys", "settings", "am")
    GUARD = ('for fd in 1 2; do case $(readlink /proc/$$/fd/$fd) in /dev/null|pipe:*) ;; *) '
             'echo "cmd: Failure calling service package: Failed transaction (2147483646)" >&2; exit 255;; esac; done\n')

    def tool(self, name, body):
        write(self.bin / name, "#!/bin/sh\n" + (self.GUARD if name in self.BINDER else "") + body + "\n")
        (self.bin / name).chmod(0o755)

    def report(self, *args):
        r = subprocess.run([SHELL, str(self.module / "apps/report.sh"), *args], env=self.env, text=True, capture_output=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout) if r.stdout.strip() else None

    def scan(self):
        result = self.report("scan")
        self.assertEqual(result["ok"], 1, result)
        return {a["p"]: a for a in result["apps"]}, result

    def test_scan_reads_source_rights_access_data_and_battery(self):
        apps, result = self.scan()
        self.assertEqual(result["missing"], [])
        self.assertEqual(list(apps), APPS)
        scam = apps[SCAM]
        self.assertEqual((scam["src"], scam["from"], scam["risk"]), ("chat", "com.whatsapp", 2))
        self.assertEqual(scam["perms"], ["sms", "a11y", "admin", "notif", "overlay", "hidden"])
        self.assertEqual(scam["acc"], {"cam": 3723, "sms": 125})   # the other user's microphone is not ours
        self.assertEqual((scam["net"], scam["bat"], scam["run"]), (6000, 12.5, 1))
        self.assertEqual((apps["com.bank.app"]["src"], apps["com.bank.app"]["risk"], apps["com.bank.app"]["perms"]), ("store", 0, []))
        self.assertEqual(apps["com.bank.app"]["acc"], {})   # discrete history is not parsed as the last access
        self.assertEqual((apps["com.tool.file"]["src"], apps["com.tool.file"]["risk"]), ("file", 1))
        self.assertEqual(apps["com.tool.file"]["perms"], ["overlay", "install"])
        self.assertEqual((apps["com.tasker"]["risk"], apps["com.tasker"]["perms"]), (1, ["a11y"]))
        self.assertEqual((apps["com.rifsxd.ksunext"]["core"], apps["com.rifsxd.ksunext"]["risk"]), (1, 0))
        self.assertEqual(apps["com.whatsapp"]["risk"], 0)
        self.assertLess(apps["app.old"]["used"], time.time() - 9 * 86400)
        self.assertEqual(apps["app.old"]["inst"], "2020-01-01 00:00:00")
        self.assertEqual(apps["com.bank.app"]["net"], 0)
        self.assertEqual(result["block"]["sources"], ["com.whatsapp", "com.google.android.gm"])
        self.assertEqual(result["block"]["on"], 1)
        self.assertFalse(list(self.data.glob("scan.*")))

    def test_a_failed_optional_dump_is_unknown_and_a_core_dump_stops_the_scan(self):
        write(self.base / "appops", "*** SERVICE 'appops' DUMP TIMEOUT EXPIRED ***\n")
        write(self.base / "net", "")
        apps, result = self.scan()
        self.assertEqual(result["missing"], ["akses", "internet"])
        self.assertEqual((apps[SCAM]["acc"], apps[SCAM]["net"]), ({}, -1))
        write(self.base / "packages", "Permission Denial: can't dump\n")
        result = self.report("scan")
        self.assertEqual(result["ok"], 0)
        self.assertIn("data paket", result["error"])

    def test_trust_clears_the_mark_and_protects_from_removal(self):
        self.assertEqual(self.report("trust", "com.tasker")["ok"], 1)
        apps, _ = self.scan()
        self.assertEqual((apps["com.tasker"]["risk"], apps["com.tasker"]["trusted"]), (1, 1))   # the mark stays; shown as trusted
        self.assertEqual(self.report("status")["trusted"], ["com.tasker"])
        self.assertIn("whitelist", self.report("remove", "com.tasker")["error"])
        self.report("untrust", "com.tasker")
        self.assertEqual(self.scan()[0]["com.tasker"]["trusted"], 0)

    def test_remove_goes_down_to_the_roots(self):
        result = self.report("remove", SCAM)
        self.assertEqual(result["ok"], 1, result)
        self.assertEqual(result["admins"], 1)
        self.assertEqual(result["leftovers"], 6)
        self.assertEqual(result["apks"], ["0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Documents/Undangan Nikah.APK"])
        self.assertEqual(result["settings"], 2)
        log = (self.state / "log").read_text()
        self.assertIn(f"disable --user 0 {SCAM}/.Admin", log)
        self.assertIn(f"force-stop --user all {SCAM}", log)
        self.assertNotIn(f"package:{SCAM}", (self.state / "installed").read_text())
        self.assertFalse(self.copy.exists())
        self.assertTrue(self.other.exists())
        self.assertTrue((self.root / f"data/data/{SCAM}.other/keep").exists())
        self.assertFalse((self.root / f"data/user/999/{SCAM}").exists())
        self.assertEqual((self.state / "0.enabled_accessibility_services").read_text(), "com.tasker/.Service")
        self.assertEqual((self.state / "0.enabled_notification_listeners").read_text(), "")

    def test_remove_refuses_what_must_stay(self):
        for pkg, reason in [("com.rifsxd.ksunext", "root manager"), ("com.android.systemui", "tidak ditemukan"),
                            ("../../data", "tidak valid"), ("a.b;reboot", "tidak valid")]:
            with self.subTest(pkg=pkg):
                result = self.report("remove", pkg)
                self.assertEqual(result["ok"], 0)
                self.assertIn(reason, result["error"])
        self.assertTrue((self.root / f"data/data/{SCAM}").exists())

    def test_a_device_admin_that_stays_blocks_the_removal(self):
        self.tool("pm", (self.bin / "pm").read_text().split("\n", 2)[2].replace('disable) echo', 'disable) exit 0; echo'))
        self.tool("sleep", "exit 0")
        result = self.report("remove", SCAM)
        self.assertEqual(result["ok"], 0)
        self.assertIn("Admin perangkat", result["error"])
        self.assertIn(f"package:{SCAM}", (self.state / "installed").read_text())
        self.assertTrue((self.root / f"data/data/{SCAM}").exists())

    def test_a_renamed_root_manager_or_an_unknown_webui_host_is_never_removed(self):
        # Audit 2026-10-29: a renamed manager is found by its native daemon library; an unknown host fails closed.
        write(self.root / "data/app/~~y/com.weonse.bxmfmy-2/lib/arm64/libksud.so", "ELF")
        write(self.state / "installed", (self.state / "installed").read_text() + "package:com.weonse.bxmfmy\n")
        write(self.base / "packages", (self.base / "packages").read_text().replace(
            "Packages:\n", "Packages:\n  Package [com.weonse.bxmfmy] (k):\n    appId=10300\n    User 0: installed=true\n"))
        write(self.base / "launcher", (self.base / "launcher").read_text() + "com.weonse.bxmfmy/.Main\n")
        apps, _ = self.scan()
        self.assertEqual((apps["com.weonse.bxmfmy"]["core"], apps["com.weonse.bxmfmy"]["risk"]), (1, 0))
        self.assertIn("root manager", self.report("remove", "com.weonse.bxmfmy")["error"])
        self.env["CA_HOST_UID"] = "10202"   # the WebUI runs in com.bank.app
        self.assertIn("membuka WebUI", self.report("remove", "com.bank.app")["error"])
        self.env["CA_HOST_UID"] = "0"   # no app among the shell's parents
        self.assertIn("tidak bisa dipastikan", self.report("remove", SCAM)["error"])
        self.assertIn(f"package:{SCAM}", (self.state / "installed").read_text())
        self.assertTrue(self.copy.exists())

    def test_a_scan_that_runs_out_of_time_still_answers_before_the_webui_gives_up(self):
        self.env["CA_BUDGET"] = "0"
        apps, result = self.scan()
        self.assertEqual(result["missing"], ["pemakaian", "akses", "admin", "ikon", "baterai", "internet", "proses"])
        self.assertEqual(apps[SCAM]["src"], "chat")

    def test_a_revoke_that_does_not_hold_is_reported_once_not_claimed(self):
        self.tool("cmd", (self.bin / "cmd").read_text().split("\n", 2)[2].replace('"appops set") echo "$*"', '"appops set") exit 0; echo "$*"'))
        self.report("block", "on"); self.report("block", "on")
        self.report("block", "off")
        log = (self.state / "log").read_text()
        self.assertEqual(log.count("com.whatsapp GAGAL dicabut"), 1, log)   # two passes, one notice per app
        self.assertEqual(log.count("com.google.android.gm GAGAL dicabut"), 1, log)
        self.assertNotIn("com.whatsapp dicabut", log)
        _, result = self.scan()
        self.assertEqual([(e["p"], e["ok"]) for e in result["block"]["events"]][:1], [("com.whatsapp", 0)])

    def test_a_failed_read_back_or_query_is_never_counted_as_revoked(self):
        # Audit 29 Oct: with the query failing after the set, "! query | grep" read as success.
        body = (self.bin / "cmd").read_text().split("\n", 2)[2]
        broken = self.state / "broken"
        self.tool("cmd", f'[ "$1 $2" = "appops query-op" ] && [ -e {broken} ] && {{ echo "Error: Failed transaction" >&2; exit 1; }}\n'
                  + body.replace('"appops set") echo "$*"', f'"appops set") : > {broken}; echo "$*"'))
        self.report("block", "on")
        log = (self.state / "log").read_text()
        self.assertIn("com.whatsapp GAGAL dicabut", log)
        self.assertNotIn("com.whatsapp dicabut", log)
        status = self.report("status")["block"]
        self.assertEqual((status["on"], status["events"][0]["ok"]), (1, 0))
        # A query that cannot be read at all marks the block card, and claims nothing.
        self.report("block", "off"); (self.state / "log").write_text("")
        self.report("block", "on")
        self.assertEqual(self.report("status")["block"]["query_ok"], 0)
        self.assertNotIn("dicabut", (self.state / "log").read_text())

    def test_the_block_status_answers_when_the_package_service_does_not(self):
        self.tool("pm", 'echo "cmd: Failure calling service package: Failed transaction (2147483646)" >&2; exit 255')
        self.assertEqual(self.report("scan")["ok"], 0)
        status = self.report("status")
        self.assertEqual((status["ok"], status["block"]["on"], status["block"]["query_ok"]), (1, 1, 1))

    def test_trust_and_the_block_switch_do_not_wait_for_a_running_scan(self):
        # Owner 29 Oct: Percaya took about 40 s, queued behind a full scan. A slow scan holds the lock here.
        self.tool("dumpsys", (self.bin / "dumpsys").read_text().split("\n", 2)[2].replace("usagestats) cat", "usagestats) sleep 4; cat"))
        scan = subprocess.Popen([SHELL, str(self.module / "apps/report.sh"), "scan"], env=self.env, stdout=subprocess.PIPE, text=True)
        time.sleep(1)
        self.assertTrue((self.data / "api.lock").exists())
        start = time.time()
        self.assertEqual(self.report("trust", "com.tasker")["ok"], 1)
        self.assertEqual(self.report("block", "off")["block"], 0)
        self.assertEqual(self.report("status")["trusted"], ["com.tasker"])
        self.assertLess(time.time() - start, 2.5)
        self.assertEqual(json.loads(scan.communicate(timeout=30)[0])["ok"], 1)

    def test_two_block_workers_started_together_leave_one(self):
        write(self.data / "config", "BLOCK=1\n")
        procs = [subprocess.Popen([SHELL, str(self.module / "apps/block.sh")], env=self.env) for _ in range(2)]
        time.sleep(2.5)
        alive = [p for p in procs if p.poll() is None]
        self.assertEqual(len(alive), 1)
        self.assertEqual((self.data / "run/block.pid").read_text().strip(), str(alive[0].pid))
        self.report("block", "off")
        alive[0].wait(timeout=10)
        self.assertFalse((self.data / "run/block.pid").exists())

    def test_block_takes_the_install_right_back_from_chat_apps_only(self):
        self.assertEqual(self.report("block", "on")["block"], 1)
        log = (self.state / "log").read_text()
        self.assertIn("appops set --user 0 com.whatsapp REQUEST_INSTALL_PACKAGES default", log)
        self.assertIn("appops set --user 999 com.whatsapp REQUEST_INSTALL_PACKAGES default", log)
        self.assertIn("appops set --user 0 com.google.android.gm REQUEST_INSTALL_PACKAGES default", log)
        self.assertIn("notify", log)
        self.assertEqual((self.state / "allowed").read_text(), "com.android.chrome\n")   # browsers keep it
        for _ in range(50):
            if (self.data / "run/block.pid").exists():
                break
            time.sleep(0.1)
        _, result = self.scan()
        self.assertEqual(result["block"]["running"], 1)
        self.assertEqual([e["p"] for e in result["block"]["events"]], ["com.whatsapp", "com.google.android.gm"])
        # Allowed again in Settings: the loop takes it back.
        write(self.state / "allowed", "com.whatsapp\n")
        for _ in range(60):
            if (self.state / "allowed").read_text() == "":
                break
            time.sleep(0.1)
        self.assertEqual((self.state / "allowed").read_text(), "")
        self.assertEqual(self.report("block", "off")["block"], 0)
        self.assertFalse((self.data / "run/block.pid").exists())
        _, result = self.scan()
        self.assertEqual((result["block"]["on"], result["block"]["running"]), (0, 0))


if __name__ == "__main__":
    unittest.main()

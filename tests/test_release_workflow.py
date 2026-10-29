"""Execute the release workflow's shell blocks offline with a fake GitHub CLI; check the Cogan Smart tested label."""
import json
import hashlib
import io
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path
from urllib.parse import unquote

from kernel import release_notes as rn

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/release-from-run.yml"
SOURCE_SHA = "4730fee1297fa5ef1a779a4223136ab1912b09e2"
MAIN_SHA = "3a81421" + "0" * 33


def script(name):
    step = WORKFLOW.read_text().split(f"      - name: {name}\n", 1)[1]
    return textwrap.dedent(step.split("        run: |\n", 1)[1].split("\n      - ", 1)[0])


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ("bin", "info", "files", "kernel"):
            (self.root / name).mkdir()
        (self.root / "run.json").write_text(json.dumps({"head_sha": SOURCE_SHA}))
        (self.root / "info/release.env").write_text("RELEASE=v26.10.24-r2\nRELEASE_NAME=Cogan r2\n")
        build = self.root / "info/build-info-KSUN-176"
        build.mkdir()
        (build / "build.env").write_text("ROOT_NAME=KernelSU Next\nLINUX_VERSION=6.1.176\n")
        (self.root / "files/1-KERNEL_fixture.zip").write_text("kernel fixture")
        (self.root / "notes.md").write_text("notes fixture\n")
        for name in ("release_notes.py", "release_from_run.py", "telegram.py"):
            shutil.copyfile(WORKFLOW.parents[2] / "kernel" / name, self.root / "kernel" / name)
        (self.root / "releases.json").write_text("[]")
        (self.root / "compare.json").write_text('{"commits": []}')
        gh = self.root / "bin/gh"
        gh.write_text('''#!/bin/bash
if [[ "$1 $2" == "release view" ]]; then
  [[ "$CASE" == exists ]] && exit 0
  exit 1
elif [[ "$1 $2" == "release create" ]]; then
  printf '%s\\n' "$@" > called.txt
  case "$CASE" in
    denied) echo 'HTTP 403: Resource not accessible by integration' >&2; exit 1;;
    server-error) echo 'HTTP 500: server error' >&2; exit 1;;
  esac
  echo 'https://github.com/cogan17/Cogan-Kernel/releases/tag/v26.10.24-r2'
elif [[ "$1 $2" == "api repos/cogan17/Cogan-Kernel/contents/.github?ref=$SOURCE_SHA" ]]; then
  echo "$WORKFLOWS_AT_SOURCE"
elif [[ "$1 $2" == "api repos/cogan17/Cogan-Kernel/contents/.github?ref=$GITHUB_SHA" ]]; then
  echo "$WORKFLOWS_AT_MAIN"
elif [[ "$1 $2" == "api --paginate" ]]; then
  cat fixtures.tsv
elif [[ "$1" == api && "$2" =~ /actions/artifacts/([0-9]+)/zip$ ]]; then
  cat "artifacts/${BASH_REMATCH[1]}"
elif [[ "$1" == api && "$2" == *'/releases?per_page=50' ]]; then
  cat releases.json
elif [[ "$1" == api && "$2" == *'/compare/'* ]]; then
  cat compare.json
else
  echo "Unexpected request: $*" >&2
  exit 2
fi
''')
        gh.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.root / 'bin'}:{os.environ['PATH']}",
                        CASE="success", GITHUB_REPOSITORY="cogan17/Cogan-Kernel",
                        GITHUB_SERVER_URL="https://github.com", SOURCE_RUN="40046361218",
                        SOURCE_SHA=SOURCE_SHA, GITHUB_SHA=MAIN_SHA,
                        WORKFLOWS_AT_SOURCE="tree1", WORKFLOWS_AT_MAIN="tree1",
                        GITHUB_STEP_SUMMARY=str(self.root / "summary.md"),
                        RELEASE_TYPE="Pre-Release", TESTED="true", NOTE="Diuji di perangkat saya.",
                        NOTE_EN="Tested on my device.", TEXT_ONLY="false")

    def run_step(self, name, **env):
        return subprocess.run(["bash", "-euo", "pipefail", "-c", script(name)], cwd=self.root,
                              env={**self.env, **env}, capture_output=True, text=True, timeout=10)

    def summary(self):
        path = self.root / "summary.md"
        return path.read_text() if path.exists() else ""

    @staticmethod
    def zip_bytes(entries):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            for name, data in entries.items():
                archive.writestr(name, data)
        return stream.getvalue()

    def artifacts(self, roots=("KSUN", "BSU"), wrapped=False):
        """The failed run's shape: two kernels/managers, separate metadata, duplicate NoMount."""
        shutil.rmtree(self.root / "info")
        shutil.rmtree(self.root / "files")
        self.payloads = []
        self.builds = {}
        for root in roots:
            slug, name = ("KernelSU-Next", "KernelSU Next") if root == "KSUN" else ("BakaSU", "BakaSU")
            kernel = f"1-KERNEL_Cogan-Rothko-ACK-6.1.176_{slug}+SuSFS_v26.10.24-r2.zip"
            content = self.zip_bytes({"Image": f"kernel for {root}"})
            env = dict(RELEASE="v26.10.24-r2", RELEASE_NAME="Cogan-Rothko-ACK v26.10.24-r2",
                       LINUX_VERSION="6.1.176", ACK_TAG="android14-6.1-2026-09_r5", ROOT_NAME=name,
                       ROOT_TAG="main", ROOT_COMMIT=("a" if root == "KSUN" else "b") * 40,
                       KSU_VERSION="33405" if root == "KSUN" else "35222", SUSFS_VERSION="v2.3.0",
                       SUSFS_COMMIT="27e0a0e4" + "0" * 32, NOMOUNT="v2.2.0", NEUTRON="24102026",
                       FEATURES="SUSFS, NoMount", KMI_COMPAT="KMI Xiaomi 14T Pro (rothko): OK; CRC differs 0",
                       ZIP=kernel, ZIP_SHA256=hashlib.sha256(content).hexdigest())
            self.builds[root] = env
            self.payloads += [(kernel, content), (f"2-MANAGER_{slug}_fixture.apk", f"manager {root}".encode()),
                              (f"3-MANAGER-SPOOFED_{slug}_fixture.apk", f"spoofed {root}".encode()),
                              ("4-NOMOUNT-MODULE_v2.2.0.zip", b"shared NoMount")]
        self.payloads += [("5-SUSFS-MODULE-SIDEX15_v1.5.2-CI-fixture.zip", b"sidex15")]
        self.wrapped = wrapped

    def write_artifacts(self):
        storage = self.root / "artifacts"
        storage.mkdir(exist_ok=True)
        payloads = self.payloads + [(f"build-info-{root}-176", self.zip_bytes({"build.env":
                    "".join(f"{key}={value}\n" for key, value in env.items())})) for root, env in self.builds.items()]
        rows = []
        for id_, (name, data) in enumerate(payloads, 1):
            digest = "sha256:" + hashlib.sha256(data).hexdigest()
            if self.wrapped and name[:2] in ("1-", "2-", "3-", "4-", "5-", "6-"):
                data = self.zip_bytes({name: data})
            (storage / str(id_)).write_bytes(data)
            rows.append(f"{id_}\t{name}\t{digest}\n")
        (self.root / "fixtures.tsv").write_text("".join(rows))

    def download(self, **env):
        self.write_artifacts()
        return self.run_step("Unduh file / download the files", **env)

    def test_both_root_managers_publish_together_without_mixing_metadata(self):
        self.artifacts()
        result = self.download(TESTED="false")
        self.assertEqual(result.returncode, 0, result.stderr)
        notes = (self.root / "notes.md").read_text()
        for root, env in self.builds.items():
            metadata = self.root / f"info/build-info-{root}-176/build.env"
            self.assertIn(f"ROOT_NAME={env['ROOT_NAME']}\n", metadata.read_text())
            label = "KSUN" if root == "KSUN" else "BakaSU"
            row = unquote(next(line for line in notes.splitlines() if line.startswith(f"| **{label}**")))
            other = "BakaSU" if root == "KSUN" else "KernelSU-Next"
            self.assertIn(env["ZIP"], row)
            self.assertNotIn(f"2-MANAGER_{other}_", row)
        self.assertIn("**belum diuji di HP**", notes)
        self.assertIn("**not tested on the phone yet**", notes)
        result = self.run_step("Terbitkan / publish", TESTED="false")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "called.txt").read_text().splitlines()
        self.assertEqual(args.count("create"), 1)
        for env in self.builds.values():
            self.assertIn(f"files/{env['ZIP']}", args)
            self.assertIn(env["ZIP"], (self.root / "files/checksums.txt").read_text())
        self.assertEqual(args.count("files/4-NOMOUNT-MODULE_v2.2.0.zip"), 1)
        result = self.run_step("Catatan dan teks Telegram / notes and Telegram text")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("KernelSU Next", self.summary())
        self.assertIn("BakaSU", self.summary())

    def test_whats_new_and_fixes_are_in_the_release_and_one_copyable_post_per_language(self):
        self.artifacts()
        bodies = []
        for env in self.builds.values():
            previous = {**env, "ROOT_COMMIT": "c" * 40, "ACK_TAG": "android14-6.1-2026-09_r4"}
            bodies.append(rn.notes(previous, [], "https://run", "cogan17/Cogan-Kernel"))
        (self.root / "releases.json").write_text(json.dumps([{"tag_name": "v26.10.23-r1", "target_commitish": "e" * 40,
                                                             "body": "\n".join(bodies)}]))
        (self.root / "compare.json").write_text(json.dumps({"commits": [
            {"commit": {"message": "fix(kernel): perbaikan ZIP ARM64 (#1)\n\nRelease-Fix-EN: Fix the ARM64 ZIP package"}},
            {"commit": {"message": "fix(module): unrelated"}}]}))
        result = self.download(TESTED="false")
        self.assertEqual(result.returncode, 0, result.stderr)
        notes = (self.root / "notes.md").read_text()
        self.assertIn("<summary>✨ <b>What's New & Fixes</b></summary>", notes)
        self.assertEqual(sorted(path.name for path in (self.root / "telegram").iterdir()), ["en.txt", "id.txt", "summary.md"])
        for lang in ("id", "en"):  # one post for the release, both root managers in it, each change once
            post = (self.root / f"telegram/{lang}.txt").read_text()
            self.assertIn("BakaSU & KernelSU Next + SUSFS v2.3.0", post)
            self.assertEqual(post.count("perbaikan ZIP ARM64" if lang == "id" else "Fix the ARM64 ZIP package"), 1)
            self.assertEqual(post.count("android14-6.1-2026-09_r4 → android14-6.1-2026-09_r5"), 1)
            self.assertIn("KernelSU Next `cccccccccccc` → `aaaaaaaaaaaa`", post)
            self.assertIn("BakaSU `cccccccccccc` → `bbbbbbbbbbbb`", post)
            if lang == "en":
                self.assertNotIn("perbaikan ZIP ARM64", post)
                self.assertIn("Tested on my device.", post)
                self.assertNotIn("Diuji di perangkat saya.", post)
            self.assertNotIn("unrelated", post)
        self.assertIn("perbaikan ZIP ARM64", notes)
        self.assertIn("Fix the ARM64 ZIP package", notes)
        self.assertIn(f"<!-- cogan-build-sha: {SOURCE_SHA} -->", notes)
        result = self.run_step("Catatan dan teks Telegram / notes and Telegram text")
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = self.summary()
        self.assertEqual(summary.count("```text"), 2)
        self.assertLess(summary.index("```text"), summary.index("Catatan rilis / Release notes"))

    def test_text_only_can_prepare_existing_release_without_publishing(self):
        self.artifacts()
        (self.root / "releases.json").write_text('[{"tag_name":"v26.10.24-r2","body":"existing release"}]')
        result = self.download(TEXT_ONLY="true", CASE="exists")
        self.assertEqual(result.returncode, 0, result.stderr)
        publish = WORKFLOW.read_text().split("      - name: Terbitkan / publish\n", 1)[1].split("        run: |", 1)[0]
        self.assertIn("if: ${{ !inputs.teks_saja }}", publish)
        result = self.run_step("Catatan dan teks Telegram / notes and Telegram text", TEXT_ONLY="true")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("tidak ada rilis yang diterbitkan atau diubah", self.summary())
        self.assertIn("/releases/tag/v26.10.24-r2", self.summary())
        self.assertFalse((self.root / "called.txt").exists())

    def test_text_only_uses_build_download_link_when_release_does_not_exist(self):
        self.artifacts(roots=("KSUN",))
        result = self.download(TEXT_ONLY="true")
        self.assertEqual(result.returncode, 0, result.stderr)
        post = (self.root / "telegram/id.txt").read_text()
        self.assertIn("https://github.com/cogan17/Cogan-Kernel/actions/runs/40046361218", post)
        self.assertNotIn("/releases/tag/", post)
        self.assertNotIn("/releases/download/", (self.root / "notes.md").read_text())

    def test_single_root_and_wrapped_artifacts_still_work(self):
        self.artifacts(roots=("KSUN",), wrapped=True)
        result = self.download()
        self.assertEqual(result.returncode, 0, result.stderr)
        kernel = self.root / "files" / self.builds["KSUN"]["ZIP"]
        with zipfile.ZipFile(kernel) as archive:
            self.assertEqual(archive.namelist(), ["Image"])
        self.assertIn("**Diuji di HP / Tested on the phone**", (self.root / "notes.md").read_text())
        result = self.run_step("Terbitkan / publish")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_second_root_must_pass_kmi(self):
        self.artifacts()
        self.builds["BSU"]["KMI_COMPAT"] = "KMI Xiaomi 14T Pro (rothko): FAILED"
        result = self.download()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("KMI gate did not pass", result.stderr)
        self.assertFalse((self.root / "info/release.env").exists())
        self.assertFalse((self.root / "called.txt").exists())

    def test_both_roots_must_belong_to_the_same_release(self):
        self.artifacts()
        self.builds["BSU"]["RELEASE"] = "v26.10.24-r3"
        result = self.download()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE berbeda", result.stderr)

    def test_kernel_must_match_its_build_digest(self):
        self.artifacts()
        self.builds["KSUN"]["ZIP_SHA256"] = "0" * 64
        result = self.download()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SHA256 berbeda dari build", result.stderr)

    def test_missing_manager_stops_the_release(self):
        self.artifacts()
        self.payloads = [(name, data) for name, data in self.payloads if not name.startswith("2-MANAGER_BakaSU_")]
        result = self.download()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one manager APK", result.stderr)

    def test_missing_susfs_module_stops_the_release(self):
        self.artifacts()
        self.payloads = [(name, data) for name, data in self.payloads if not name.startswith("5-")]
        result = self.download()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing NoMount/SUSFS modules", result.stderr)

    def test_missing_kernel_stops_the_release(self):
        self.artifacts()
        self.payloads = [(name, data) for name, data in self.payloads if name != self.builds["BSU"]["ZIP"]]
        result = self.download()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing kernel ZIP", result.stderr)

    def test_same_named_shared_files_with_different_digests_are_rejected(self):
        self.artifacts()
        self.payloads.append(("4-NOMOUNT-MODULE_v2.2.0.zip", b"different module"))
        result = self.download()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("same artifact name, different contents", result.stdout)

    def test_artifact_download_digest_is_still_checked(self):
        self.artifacts()
        self.write_artifacts()
        (self.root / "artifacts/1").write_bytes(b"wrong download")
        result = self.run_step("Unduh file / download the files")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SHA256 berbeda dari artifact", result.stdout)

    def test_same_workflows_tag_the_build_commit(self):
        result = self.run_step("Terbitkan / publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "called.txt").read_text().splitlines()
        self.assertEqual(args[args.index("--target") + 1], SOURCE_SHA)
        self.assertIn("--prerelease", args)
        self.assertNotIn("--latest", args)
        self.assertIn("Terbit:", self.summary())
        self.assertIn("Published:", self.summary())
        self.assertTrue((self.root / "files/checksums.txt").exists())

    def test_release_choice_marks_latest(self):
        result = self.run_step("Terbitkan / publish", RELEASE_TYPE="Release", TESTED="false", NOTE="")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "called.txt").read_text().splitlines()
        self.assertIn("--latest", args)
        self.assertNotIn("--prerelease", args)
        self.assertNotIn("tested on the phone", self.summary())

    def test_existing_release_is_not_overwritten(self):
        result = self.run_step("Terbitkan / publish", CASE="exists")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / "called.txt").exists())

    def test_different_workflows_tag_this_run_commit(self):
        result = self.run_step("Terbitkan / publish", WORKFLOWS_AT_MAIN="tree2")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "called.txt").read_text().splitlines()
        self.assertEqual(args[args.index("--target") + 1], MAIN_SHA)

    def test_unreadable_workflows_tag_this_run_commit(self):
        result = self.run_step("Terbitkan / publish", WORKFLOWS_AT_SOURCE="", WORKFLOWS_AT_MAIN="")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.root / "called.txt").read_text().splitlines()
        self.assertEqual(args[args.index("--target") + 1], MAIN_SHA)

    def test_refused_release_stops_without_publish_summary(self):
        for case in ("denied", "server-error"):
            with self.subTest(case=case):
                result = self.run_step("Terbitkan / publish", CASE=case)
                self.assertEqual(result.returncode, 1)
                self.assertIn("HTTP", result.stderr)
                self.assertNotIn("Terbit:", self.summary())

class CoganSmartTestedLabelTests(unittest.TestCase):
    """The "tested on the phone" label of a Cogan Smart release, run as written in the workflow."""

    def label(self, notes):
        step = (WORKFLOW.parent / "cogan-smart-release.yml").read_text().split("Mark the release as tested on the phone", 1)[1]
        code = textwrap.dedent(step.split("<<'PY'\n", 1)[1].split("\n          PY\n", 1)[0])
        with tempfile.TemporaryDirectory() as tmp:
            body = Path(tmp) / "body.md"
            body.write_text("## Cogan Smart Kernel\n\n> [!NOTE]\n> note\n\n```text\n" + notes + "```\n", encoding="utf-8")
            env = dict(os.environ, KERNEL_UJI="r6 (6.1.176)", AKSI="Tandai diuji di HP")
            subprocess.run(["python3", "-", str(body)], input=code, text=True, env=env, check=True)
            return body.read_text(encoding="utf-8")

    def test_notes_written_before_the_phone_test_say_so(self):
        body = self.label("PENGUJIAN\n- Belum diuji di HP.\n")
        self.assertIn("kernel Cogan r6 (6.1.176)", body)
        self.assertIn("ditulis sebelum uji HP ini", body)
        self.assertIn("written before this phone test", body)

    def test_notes_that_record_the_phone_test_are_not_called_older(self):
        body = self.label("Diuji owner di HP: Xiaomi 14T Pro dengan kernel Cogan r6.\n")
        self.assertIn("**Diuji owner di Xiaomi 14T Pro**", body)
        self.assertNotIn("sebelum uji HP ini", body)
        self.assertNotIn("written before this phone test", body)


if __name__ == "__main__":
    unittest.main()

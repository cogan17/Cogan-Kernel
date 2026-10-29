#!/usr/bin/env python3
"""Cogan Smart WebUI checks that need Node.js: the shared client and Manager script
(tests/cogan_smart_client_check.js), and English mode leaving no Indonesian page text behind.
Skipped when node is not installed; GitHub's ubuntu runner has it."""
import json
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEBROOT = ROOT / "modules/cogan-smart/webroot"
PAGES = ("index.html", "thermal.html", "manager.html", "modules.html", "apps.html", "about.html", "guide.html")
# Words that mean an English page still shows Indonesian. Names (Cogan17, KernelSU Next, sugov_ext) stay as they are.
INDONESIAN = r"\b(dan|yang|untuk|tidak|belum|sudah|modul|suhu|cas|dari|tekan|aktif|bawaan|setelan|hapus|simpan|pindai|skrip|berhenti|mulai|ringkasan|bila|saat|kamu|lalu|pilih)\b"
TRANSLATE = """
const fs = require('fs'), vm = require('vm');
const ctx = {document: {documentElement: {lang: 'en', dataset: {}}, querySelectorAll: () => [], addEventListener() {}},
  localStorage: {getItem: () => 'en', setItem() {}}, window: {}, MutationObserver: function () { return {observe() {}}; },
  Event: function () {}, console};
ctx.window = ctx; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), ctx);
const texts = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(texts.map(t => ctx.CoganI18n.t(t))));
"""


class PageText(HTMLParser):
    """Visible text the catalog translates: not scripts, styles, code, translate="no" or lang="id|en" blocks."""
    VOID = {"br", "input", "meta", "link", "img"}

    def __init__(self):
        super().__init__()
        self.skip, self.texts = [], []

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        a = dict(attrs)
        own = tag in ("script", "style", "code") or ("lang" in a and tag != "html") or a.get("translate") == "no"
        self.skip.append(own or (self.skip[-1] if self.skip else False))

    def handle_endtag(self, tag):
        if tag not in self.VOID and self.skip:
            self.skip.pop()

    def handle_data(self, data):
        text = " ".join(data.split())
        if text and not (self.skip and self.skip[-1]):
            self.texts.append(text)


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class WebUITests(unittest.TestCase):
    def test_client_and_manager_script(self):
        result = subprocess.run(["node", "tests/cogan_smart_client_check.js"], cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_english_mode_leaves_no_indonesian_page_text(self):
        for page in PAGES:
            parser = PageText()
            parser.feed((WEBROOT / page).read_text())
            texts = sorted(set(parser.texts))
            result = subprocess.run(["node", "-e", TRANSLATE, str(WEBROOT / "i18n.js")], input=json.dumps(texts),
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            left = [(t, e) for t, e in zip(texts, json.loads(result.stdout)) if re.search(INDONESIAN, e, re.I)]
            self.assertEqual(left, [], page)

    def test_mode_dev_and_guide_on_every_page(self):
        for page in PAGES:
            html = (WEBROOT / page).read_text()
            self.assertIn("dataset.dev = localStorage.getItem('cogan.dev')", html, page)
            if page != "guide.html":
                self.assertIn('href="guide.html"', html, page)
        self.assertIn(':root:not([data-dev="1"]) .dev', (WEBROOT / "theme.css").read_text())


if __name__ == "__main__":
    unittest.main()

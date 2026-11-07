#!/usr/bin/env python3
"""Describe what a finished Cogan kernel build really contains.

Reads the resolved O=/.config and the kernel source tree, never the form inputs,
so the line cannot claim a feature the build lacks:
  SUSFS            CONFIG_KSU_SUSFS=y
  BBRv3 / BBR      CONFIG_TCP_CONG_BBR=y; v3 when net/ipv4/tcp_bbr.c defines
                   BBR_VERSION 3 (the BBRv3 patch), "(default)" when it is the
                   default congestion control, "also bbr3" when the bbr3 name
                   patch registers it a second time
  BBG, NoMount     CONFIG_BBG=y, CONFIG_NOMOUNT=y
  Unicode fix      CONFIG_UNICODE=y and fs/unicode/utf8-norm.c checks an empty
                   decomposition before it moves on (WildKernel's unicode bypass fix)
  Cogan Bridge     CONFIG_COGAN_BRIDGE=y
  Disguise         CONFIG_LOCALVERSION in the stock GKI format (the "Samarkan identitas kernel" box)

A feature that is on by default and was turned off is named too, "No <feature>" like "No SUSFS"
(owner 2026-11-02: "lebih bagus lagi dilaporkannya tidak ada susfs/no susfs"), so the flasher and the
release notes say what the kernel lacks. An off-by-default extra (Disguise) is named only when on.

LTO is not named: every build is without LTO, like the stock kernel (owner 2026-11-07).

Prints one line such as "SUSFS, BBRv3 (default), BBG, NoMount, Cogan Bridge" or
"No SUSFS, BBRv3 (default), BBG, No NoMount, Unicode fix, Cogan Bridge".

Usage: kernel_features.py CONFIG KERNEL_SOURCE [--github-env FILE]
"""
import argparse
import re
import sys
from pathlib import Path

BBR_V3 = re.compile(r"^#define\s+BBR_VERSION\s+3\b", re.MULTILINE)
BBR3_NAME = re.compile(r'tcp_bbr3_cong_ops\.name,\s*"bbr3"')
DISGUISE = re.compile(r'^"-android\d+-\d+-g[0-9a-f]{12}-ab\d+"$')
UNICODE_FIX = re.compile(r"ccc == DECOMPOSE\)\s*\{(?:\s*//[^\n]*)?\s*if \(\*LEAF_STR\(leaf\) == '\\0'\)")


def read_config(text):
    values = {}
    for line in text.splitlines():
        if line.startswith("CONFIG_") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
        elif line.startswith("# CONFIG_") and line.endswith(" is not set"):
            values[line[2:-11]] = "n"
    return values


def features(config_text, bbr_source="", unicode_source=""):
    config = read_config(config_text)
    on = lambda key: config.get(key) == "y"  # noqa: E731
    found = []
    found.append("SUSFS" if on("CONFIG_KSU_SUSFS") else "No SUSFS")
    if on("CONFIG_TCP_CONG_BBR"):
        name = "BBRv3" if BBR_V3.search(bbr_source) else "BBR"
        notes = (["default"] if config.get("CONFIG_DEFAULT_TCP_CONG") == '"bbr"' else []) + \
            (["also bbr3"] if name == "BBRv3" and BBR3_NAME.search(bbr_source) else [])
        found.append(name + (f" ({', '.join(notes)})" if notes else ""))
    else:
        found.append("No BBR")
    found.append("BBG" if on("CONFIG_BBG") else "No BBG")
    found.append("NoMount" if on("CONFIG_NOMOUNT") else "No NoMount")
    found.append("Unicode fix" if on("CONFIG_UNICODE") and UNICODE_FIX.search(unicode_source) else "No Unicode fix")
    found.append("Cogan Bridge" if on("CONFIG_COGAN_BRIDGE") else "No Cogan Bridge")
    if DISGUISE.match(config.get("CONFIG_LOCALVERSION", "")):
        found.append("Disguise")
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--github-env")
    args = parser.parse_args(argv)
    try:
        config_text = args.config.read_text(encoding="utf-8")
        bbr = args.source / "net/ipv4/tcp_bbr.c"
        bbr_source = bbr.read_text(encoding="utf-8", errors="replace") if bbr.is_file() else ""
        utf8 = args.source / "fs/unicode/utf8-norm.c"
        unicode_source = utf8.read_text(encoding="utf-8", errors="replace") if utf8.is_file() else ""
    except OSError as exc:
        print("kernel features unreadable: " + str(exc), file=sys.stderr)
        return 1
    line = ", ".join(features(config_text, bbr_source, unicode_source))
    print(line)
    if args.github_env:
        with open(args.github_env, "a", encoding="utf-8") as handle:
            handle.write(f"KERNEL_FEATURES={line}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

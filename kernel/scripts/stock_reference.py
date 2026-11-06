#!/usr/bin/env python3
"""Fetch the ACK source of the phone's own stock kernels, the KMI gate's references (kmi_compat.py).

The references are facts of the phone, not component pins: rothko ships 6.1.138-android14-11
on HyperOS OS3.0.301 and 6.1.157-android14-11 on OS3.0.302 (kmi_compat.DEVICES["rothko"]["stocks"]),
and each version's vendor modules were built against that ABI. A kernel must keep both loadable.
Only what the gate reads: android/ (symbol lists, frozen ABI), arch/arm64/configs/,
build.config.common, include/trace/hooks/, Makefile and modules.bzl - a sparse, shallow,
blob-less fetch of about 10 MB each, into DEST/<version>. Fails unless HEAD is the stock commit
and the Makefile is the stock version.

Usage: stock_reference.py --device rothko DEST
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kmi_compat import DEVICES, kernel_version, stock_name  # noqa: E402

PATHS = ["/android/", "/arch/arm64/configs/", "/build.config.common", "/include/trace/hooks/",
         "/Makefile", "/modules.bzl"]


def git(dest, *args):
    subprocess.run(["git", "-C", str(dest), *args], check=True)


def fetch_one(stock, dest, repo=None):
    dest.mkdir(parents=True)
    git(dest, "init", "-q")
    git(dest, "remote", "add", "origin", repo or stock["repo"])
    git(dest, "sparse-checkout", "set", "--no-cone", *PATHS)
    try:
        git(dest, "fetch", "-q", "--depth=1", "--filter=blob:none", "origin", stock["commit"])
    except subprocess.CalledProcessError:
        print(f"Blob-less fetch of {stock['commit'][:12]} refused, fetching it whole", file=sys.stderr)
        git(dest, "fetch", "-q", "--depth=1", "origin", stock["commit"])
    git(dest, "checkout", "-q", "FETCH_HEAD")
    head = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], check=True,
                          capture_output=True, text=True).stdout.strip()
    if head != stock["commit"]:
        raise ValueError(f"fetched {head}, the stock commit is {stock['commit']}")
    if kernel_version(dest) != stock["version"]:
        raise ValueError(f"fetched kernel {kernel_version(dest)}, the stock kernel is {stock['version']}")


def fetch(device, dest, repo=None):
    stocks = DEVICES[device]["stocks"]
    if dest.exists() and any(dest.iterdir()):
        raise ValueError(f"{dest} is not empty")
    for stock in stocks:
        fetch_one(stock, dest / stock["version"], repo)
    return stocks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", required=True, choices=sorted(d for d in DEVICES if "stocks" in DEVICES[d]))
    parser.add_argument("dest", type=Path)
    parser.add_argument("--repo", help="override the source repository (a local mirror for tests)")
    args = parser.parse_args(argv)
    try:
        stocks = fetch(args.device, args.dest, args.repo)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"BLOCKED: stock kernel reference: {exc}", file=sys.stderr)
        return 1
    for stock in stocks:
        print(f"Stock kernel reference: {stock['kernel']} (HyperOS {stock['hyperos']}, "
              f"{stock['commit'][:12]}) in {args.dest / stock['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

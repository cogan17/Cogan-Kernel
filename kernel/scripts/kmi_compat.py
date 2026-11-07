#!/usr/bin/env python3
"""KMI compatibility gate of a built kernel against a device's vendor modules (offline).

On a GKI phone the boot partition holds only the generic kernel; the SoC and phone
drivers are vendor_dlkm / system_dlkm modules built against the frozen KMI. They
load on another kernel only if:
  1. the KMI generation matches (rothko stock: 6.1.138/6.1.157-android14-11 -> 11);
  2. every symbol of the ACK symbol lists those modules were built with is
     exported (missing exports cannot be forced) - by the kernel, or by a GKI
     module (modules.bzl, e.g. bluetooth.ko) that the phone loads from its stock
     system_dlkm: such symbols are accepted when a GKI module of the exporting
     source's directory exists, and listed in the report;
  3. the Google-signed GKI modules may still export protected symbols: our kernel
     does not trust Google's key, so android/abi_gki_protected_exports_* must be
     gone from the source (GKID removes it; gkid_parity.py for older sublevels);
  4. no symbol CRC differs from the frozen ABI (android/abi_gki_aarch64.stg): a
     difference is a changed KMI type, and the force-load change in
     kernel/module/version.c would load a vendor module against it anyway, so the
     gate fails instead (owner 2026-11-07, security audit r13/r14; every good build
     so far had 0).

Two references hold the GKI build against the phone itself:
  --reference BSP_SRC          the phone maker's own kernel source (rothko: the Xiaomi
                               BSP in cogan17/Xiomi-14t-pro);
  --stock-reference STOCK_SRC  the ACK source of a stock kernel of the phone, once per
                               supported HyperOS version (rothko: 6.1.138 of HyperOS
                               OS3.0.301 and 6.1.157 of OS3.0.302; fetched at the stock
                               commits by stock_reference.py). With any of them given, all
                               must be: a kernel has to keep the vendor modules of every
                               supported HyperOS version loadable.
For each one:
  5. its KMI generation is the phone's (a stock one must also be a stock version);
  6. every symbol of its own symbol lists is exported (as in 2);
  7. every CONFIG_*=y of its gki_defconfig is =y in the built .config, except the
     reviewed exceptions listed per device and reference;
  8. every vendor hook it declares (include/trace/hooks) that the GKI source lacks is
     unused by the vendor modules (its __tracepoint_ symbol is in no symbol list);
     unused ones are only reported. Xiaomi/MediaTek features themselves live in the
     phone's vendor modules, which these checks keep loadable.
A stock reference also checks the CRCs against its stock frozen ABI, the one that
HyperOS version's vendor modules were actually built with: a difference fails too.

Usage: kmi_compat.py --device rothko KERNEL_SRC OUT_DIR [--reference BSP_SRC]
                     [--stock-reference STOCK_SRC ...] [--github-env FILE] [--json FILE]
Exit 1 when 1-8 or the force-load change fail.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Reviewed 2026-10-16 after the first rothko builder run (Xiomi-14t-pro run 38934173981).
SCMVERSION = ("only the modinfo/sysfs scmversion attribute (struct module keeps the field, so module "
              "layout is unchanged); depends on LOCALVERSION_AUTO, which build.sh turns off for the "
              "Cogan version name, as in the device-tested r2/r3 kernels")
DEVICES = {
    # Xiaomi 14T Pro: MediaTek MT6989; stock kernels 6.1.138 and 6.1.157, android14-11.
    "rothko": {"name": "Xiaomi 14T Pro (rothko)", "generation": "11",
               "lists": ["abi_gki_aarch64", "abi_gki_aarch64_mtk", "abi_gki_aarch64_xiaomi"],
               # Xiaomi BSP (6.1.57) gki_defconfig =y options that are not =y in GKID 6.1, reviewed
               # 2026-10-16: none provides anything the phone's vendor modules use.
               "bsp_config_exceptions": {
                   "CONFIG_DEBUG_STACK_USAGE": "debug statistics only",
                   "CONFIG_MEDIA_CEC_RC": "HDMI-CEC remote control keys; no HDMI-CEC on the phone",
                   "CONFIG_MODULE_SCMVERSION": SCMVERSION,
                   "CONFIG_UAPI_HEADER_TEST": "build-time header test, not in the kernel",
               },
               # Stock kernel of each supported HyperOS version = this ACK commit (read from the
               # stock boot.img). A kernel must keep the vendor modules of all of them loadable
               # (owner 2026-11-06), so users still on the older HyperOS get the newest kernel too.
               "stocks": [
                   {"hyperos": "OS3.0.301.0.WNNIDXM",
                    "kernel": "6.1.138-android14-11-g6ab8c9a86a33-ab14396278", "version": "6.1.138",
                    "repo": "https://github.com/aosp-mirror/kernel_common",
                    "tag": "android14-6.1-2025-06_r11",
                    "commit": "6ab8c9a86a331cece499c7edac062ceffbe2e320"},
                   # boot.img SHA256 3c7bd85e...afe43; ACK "ANDROID: GKI: update symbol list file for
                   # xiaomi" (2026-06-16), only on android.googlesource.com, not on the GitHub mirror.
                   {"hyperos": "OS3.0.302.0.WNNIDXM",
                    "kernel": "6.1.157-android14-11-g0baf70f2581d-ab15659624", "version": "6.1.157",
                    "repo": "https://android.googlesource.com/kernel/common",
                    "commit": "0baf70f2581d2bef029fb08cb61255e420858d10"},
               ],
               # Stock gki_defconfig =y options that are not =y in GKID 6.1, reviewed 2026-10-16.
               "stock_config_exceptions": {
                   "CONFIG_MEMFD_ASHMEM_SHIM": "removed from android14-6.1 by Google (ACK 8e481acd, "
                                               "2026-03-10: only needed on 6.12+); exports no symbol",
                   "CONFIG_MODULE_SCMVERSION": SCMVERSION,
                   "CONFIG_UAPI_HEADER_TEST": "build-time header test, not in the kernel",
               }},
}
REFERENCES = {"bsp": "BSP", "stock": "stock"}
FORCE_LOAD = re.compile(r"disagrees about version of symbol.*but ignore")
HOOK = re.compile(r"DECLARE_(?:RESTRICTED_)?HOOK\(\s*(\w+)")


def vendor_hooks(src):
    hooks = set()
    for header in sorted((src / "include/trace/hooks").glob("*.h")):
        hooks.update(HOOK.findall(header.read_text(encoding="utf-8", errors="replace")))
    return hooks
GKI_MODULE = re.compile(r'"([A-Za-z0-9_./-]+\.ko)"')


def gki_module_exports(src, symbols):
    """symbol -> GKI module (modules.bzl) whose directory's sources export it."""
    modules = GKI_MODULE.findall((src / "modules.bzl").read_text(encoding="utf-8")) \
        if (src / "modules.bzl").is_file() else []
    by_dir = {}
    for module in modules:
        by_dir.setdefault(str(Path(module).parent), []).append(module)
    found = {}
    for directory, owners in sorted(by_dir.items()):
        for source in sorted((src / directory).glob("*.c")):
            text = source.read_text(encoding="utf-8", errors="replace")
            for symbol in symbols - found.keys():
                if re.search(r"EXPORT_SYMBOL\w*\(\s*" + re.escape(symbol) + r"\s*[,)]", text):
                    found[symbol] = owners[0] if len(owners) == 1 else " / ".join(owners)
    return found


def read_list(path):
    symbols = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "[")):
            symbols.add(line)
    return symbols


def read_symvers(path):
    exported = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) >= 2:
            exported[fields[1]] = int(fields[0], 16)
    return exported


def read_stg(path):
    """name -> crc of the frozen ABI's elf_symbol blocks that carry a crc."""
    crcs, block = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line == "elf_symbol {":
            block = {}
        elif line == "}" and block is not None:
            if "name" in block and "crc" in block:
                crcs[block["name"]] = int(block["crc"], 16)
            block = None
        elif block is not None and ":" in line:
            key, value = (part.strip() for part in line.split(":", 1))
            block[key] = value.strip('"')
    return crcs


def generation(src):
    match = re.search(r"^KMI_GENERATION=(\d+)$", (src / "build.config.common").read_text(), re.MULTILINE)
    return match.group(1) if match else None


def kernel_version(src):
    """VERSION.PATCHLEVEL.SUBLEVEL of a kernel source's Makefile, None without one."""
    if not (src / "Makefile").is_file():
        return None
    head = (src / "Makefile").read_text(encoding="utf-8", errors="replace")[:1000]
    parts = [re.search(rf"^{key} = (\d+)$", head, re.MULTILINE) for key in ("VERSION", "PATCHLEVEL", "SUBLEVEL")]
    return ".".join(part.group(1) for part in parts) if all(parts) else None


def stock_name(stock):
    return f"{stock['version']} (HyperOS {stock['hyperos']})"


def check(src, out, device, reference=None, stocks=()):
    spec = DEVICES[device]
    report = {"device": spec["name"], "kmi_generation": generation(src), "lists": {}, "errors": []}
    if report["kmi_generation"] != spec["generation"]:
        report["errors"].append(f"KMI generation {report['kmi_generation']}, the phone needs {spec['generation']}")
    symvers = out / "vmlinux.symvers"
    if not symvers.is_file():
        symvers = out / "Module.symvers"
    exported = read_symvers(symvers)
    wanted = set()
    for name in spec["lists"]:
        wanted |= read_list(src / "android" / name)
    from_modules = gki_module_exports(src, wanted - exported.keys())
    report["from_gki_modules"] = dict(sorted(from_modules.items()))
    for name in spec["lists"]:
        symbols = read_list(src / "android" / name)
        missing = sorted(symbols - exported.keys() - from_modules.keys())
        report["lists"][name] = {"symbols": len(symbols), "missing": missing}
        if missing:
            report["errors"].append(f"{name}: {len(missing)} symbol(s) not exported, e.g. {', '.join(missing[:5])}")
    frozen = read_stg(src / "android/abi_gki_aarch64.stg")
    report["crc_differences"] = sorted(name for name in wanted & frozen.keys() & exported.keys()
                                       if frozen[name] != exported[name])
    if report["crc_differences"]:
        report["errors"].append(f"CRC differs from the frozen ABI for {len(report['crc_differences'])} symbol(s), "
                                f"e.g. {', '.join(report['crc_differences'][:5])}")
    report["force_load"] = bool(FORCE_LOAD.search((src / "kernel/module/version.c").read_text(errors="replace")))
    if not report["force_load"]:
        report["errors"].append("module force-load change missing (CRC differences would refuse vendor modules)")
    report["protected_exports"] = sorted(p.name for p in (src / "android").glob("*protected_exports*"))
    if report["protected_exports"]:
        report["errors"].append("protected exports still present: " + ", ".join(report["protected_exports"]))
    report["references"] = {}
    if reference:
        check_reference(report, "bsp", reference, src, out, spec, exported)
    for path in stocks:
        check_reference(report, "stock", path, src, out, spec, exported)
    if stocks:
        given = {ref["version"] for ref in report["references"].values() if ref["kind"] == "stock"}
        for stock in spec["stocks"]:
            if stock["version"] not in given:
                report["errors"].append(f"stock reference of {stock_name(stock)} not given: "
                                        "every supported HyperOS version must be checked")
    return report


def read_config(path):
    values = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("CONFIG_") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def check_reference(report, kind, reference, src, out, spec, exported):
    """Hold the GKI build against one of the phone's own kernel sources (BSP or stock ACK)."""
    ref = {"kind": kind, "kmi_generation": generation(reference), "version": kernel_version(reference),
           "lists": {}}
    label = REFERENCES[kind] if kind == "bsp" else f"stock {ref['version']}"
    if kind == "stock":
        stock = next((s for s in spec["stocks"] if s["version"] == ref["version"]), None)
        if stock:
            ref["hyperos"] = stock["hyperos"]
        else:
            report["errors"].append(f"stock reference is kernel {ref['version']}, the phone's stock kernels are "
                                    + ", ".join(stock_name(s) for s in spec["stocks"]))
        if label in report["references"]:  # keyed by version, e.g. "stock 6.1.157"
            report["errors"].append(f"{label} reference given twice")
    if ref["kmi_generation"] != spec["generation"]:
        report["errors"].append(f"{label} KMI generation {ref['kmi_generation']}, the phone needs {spec['generation']}")
    wanted = set()
    for name in spec["lists"]:
        wanted |= read_list(reference / "android" / name)
    from_modules = gki_module_exports(src, wanted - exported.keys())
    for name in spec["lists"]:
        symbols = read_list(reference / "android" / name)
        missing = sorted(symbols - exported.keys() - from_modules.keys())
        ref["lists"][name] = {"symbols": len(symbols), "missing": missing}
        if missing:
            report["errors"].append(f"{label} {name}: {len(missing)} symbol(s) not exported, "
                                    f"e.g. {', '.join(missing[:5])}")
    defconfig = read_config(reference / "arch/arm64/configs/gki_defconfig")
    built = read_config(out / ".config")
    off = sorted(key for key, value in defconfig.items() if value == "y" and built.get(key) != "y")
    exceptions = spec.get(f"{kind}_config_exceptions", {})
    ref["config_not_enabled"] = {key: exceptions.get(key, "NOT REVIEWED") for key in off}
    unreviewed = [key for key in off if key not in exceptions]
    if unreviewed:
        report["errors"].append(f"{label} gki_defconfig options not enabled: " + ", ".join(unreviewed[:10]))
    every_list = set()
    for path in sorted((reference / "android").glob("abi_gki_aarch64*")):
        if path.suffix != ".stg" and "." not in path.name:
            every_list |= read_list(path)
    absent = sorted(vendor_hooks(reference) - vendor_hooks(src))
    used = [hook for hook in absent if f"__tracepoint_{hook}" in every_list]
    ref["hooks_absent"] = {hook: ("USED by vendor modules" if hook in used else "unused by vendor modules")
                           for hook in absent}
    if used:
        report["errors"].append(f"{label} vendor hooks missing but used by vendor modules: " + ", ".join(used))
    if kind == "stock":
        frozen = read_stg(reference / "android/abi_gki_aarch64.stg")
        ref["crc_differences"] = sorted(name for name in wanted & frozen.keys() & exported.keys()
                                        if frozen[name] != exported[name])
        if ref["crc_differences"]:
            report["errors"].append(f"{label} CRC differs for {len(ref['crc_differences'])} symbol(s), "
                                    f"e.g. {', '.join(ref['crc_differences'][:5])}")
    report["references"][kind if kind == "bsp" else label] = ref


def summary(report):
    def exported(lists):
        return ", ".join(f"{name.replace('abi_gki_aarch64', 'GKI').replace('GKI_', '')} "
                         f"{info['symbols'] - len(info['missing'])}/{info['symbols']}"
                         for name, info in lists.items())
    verdict = "OK" if not report["errors"] else "GAGAL / FAILED"
    line = (f"KMI {report['device']}: {verdict}; generation {report['kmi_generation']}; "
            f"exported {exported(report['lists'])} ({len(report['from_gki_modules'])} via GKI modules); "
            f"CRC differs {len(report['crc_differences'])} (force-load {'on' if report['force_load'] else 'OFF'})")
    for key, ref in report.get("references", {}).items():
        label = REFERENCES[ref["kind"]]
        name = label if key == "bsp" else key
        unreviewed = sum(why == "NOT REVIEWED" for why in ref["config_not_enabled"].values())
        line += (f"; {name}: generation {ref['kmi_generation']}, exported {exported(ref['lists'])}, "
                 f"config =y not enabled {len(ref['config_not_enabled'])} "
                 f"({f'{unreviewed} NOT REVIEWED' if unreviewed else 'reviewed'}), "
                 f"{label}-only vendor hooks {len(ref['hooks_absent'])} (unused)")
        if "crc_differences" in ref:
            line += f", CRC differs {len(ref['crc_differences'])}"
    return line


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", required=True, choices=sorted(DEVICES))
    parser.add_argument("src", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--reference", type=Path, help="phone maker's kernel source (BSP) to hold the build against")
    parser.add_argument("--stock-reference", type=Path, action="append", default=[],
                        help="ACK source of a stock kernel of the phone (once per supported HyperOS version)")
    parser.add_argument("--github-env")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    try:
        report = check(args.src, args.out, args.device, args.reference, args.stock_reference)
    except (OSError, ValueError) as exc:
        print(f"BLOCKED: KMI check could not run: {exc}", file=sys.stderr)
        return 1
    line = summary(report)
    print(line)
    for error in report["errors"]:
        print("BLOCKED: " + error, file=sys.stderr)
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.github_env:
        with open(args.github_env, "a", encoding="utf-8") as handle:
            handle.write(f"KMI_COMPAT={line}\n")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

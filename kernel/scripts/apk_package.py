#!/usr/bin/env python3
"""Package name of an APK, read from its binary AndroidManifest.xml (no Android SDK on the runner).

The experiment ZIP (manager update through TWRP) only updates a manager that is already installed, so it
needs the package name; it differs per build (release, dev, spoofed), so it is read, never assumed.

Usage: apk_package.py FILE.apk   -> prints the package name, exit 1 when it cannot be read
"""
import struct
import sys
import zipfile

STRING_POOL, START_ELEMENT = 0x0001, 0x0102
UTF8 = 0x100


def strings(data, offset):
    """The string pool chunk at offset -> list of str."""
    _, header, _, count, _, flags, start, _ = struct.unpack_from("<HHIIIIII", data, offset)
    offsets = struct.unpack_from(f"<{count}I", data, offset + header)
    found = []
    for item in offsets:
        at = offset + start + item
        if flags & UTF8:
            at += 2 if data[at] & 0x80 else 1          # length in characters
            size = data[at]
            if size & 0x80:
                size = ((size & 0x7F) << 8) | data[at + 1]
                at += 1
            found.append(data[at + 1:at + 1 + size].decode("utf-8", "replace"))
        else:
            size = struct.unpack_from("<H", data, at)[0]
            if size & 0x8000:
                size = ((size & 0x7FFF) << 16) | struct.unpack_from("<H", data, at + 2)[0]
                at += 2
            found.append(data[at + 2:at + 2 + size * 2].decode("utf-16-le", "replace"))
    return found


def package(manifest):
    """The package attribute of the <manifest> element of a binary AndroidManifest.xml."""
    if struct.unpack_from("<H", manifest, 0)[0] != 0x0003:
        raise ValueError("not a binary AndroidManifest.xml")
    pool, offset = None, struct.unpack_from("<H", manifest, 2)[0]
    while offset + 8 <= len(manifest):
        kind, header, size = struct.unpack_from("<HHI", manifest, offset)
        if size < 8:
            break
        if kind == STRING_POOL and pool is None:
            pool = strings(manifest, offset)
        elif kind == START_ELEMENT and pool is not None:
            name = struct.unpack_from("<I", manifest, offset + 20)[0]
            start, attr_size, count = struct.unpack_from("<HHH", manifest, offset + 24)
            if pool[name] == "manifest":
                for i in range(count):
                    at = offset + 16 + start + i * attr_size
                    _, attr, raw = struct.unpack_from("<III", manifest, at)
                    if pool[attr] == "package" and raw != 0xFFFFFFFF:
                        return pool[raw]
                break
        offset += size
    raise ValueError("no package name in the manifest")


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit(__doc__)
    try:
        with zipfile.ZipFile(args[0]) as apk:
            print(package(apk.read("AndroidManifest.xml")))
    except (OSError, KeyError, ValueError, IndexError, struct.error, zipfile.BadZipFile) as error:
        print(f"{args[0]}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

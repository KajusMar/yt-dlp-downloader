#!/usr/bin/env python3
"""
Build a Firefox/Floorp .xpi from the extension/ folder using Python's zipfile.

We deliberately do NOT use PowerShell Compress-Archive: it produces ZIPs whose
nested-path entries Firefox's strict JAR reader sometimes fails to serve
(manifest.json loads but popup/background subfolder files 404). Python's
zipfile emits clean, forward-slashed, deflated entries that Firefox mounts
correctly, so every extension resource is reachable via moz-extension://.
"""
import os, zipfile, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT_DIR = os.path.join(ROOT, "extension")
DIST_DIR = os.path.join(ROOT, "dist")

SKIP = {".DS_Store", "Thumbs.db", ".gitkeep"}


def main():
    import json
    with open(os.path.join(EXT_DIR, "manifest.json"), encoding="utf-8") as f:
        version = json.load(f).get("version", "1.0.0")

    os.makedirs(DIST_DIR, exist_ok=True)
    xpi = os.path.join(DIST_DIR, "yt-dlp-downloader.xpi")
    versioned = os.path.join(DIST_DIR, f"yt-dlp-downloader-v{version}.xpi")

    # Collect files with POSIX-style relative paths, no leading "./"
    files = []
    for base, _dirs, names in os.walk(EXT_DIR):
        for name in names:
            full = os.path.join(base, name)
            rel = os.path.relpath(full, EXT_DIR).replace(os.sep, "/")
            if os.path.basename(full) in SKIP or rel.startswith("."):
                continue
            files.append((full, rel))
    files.sort(key=lambda x: x[1])

    for out in (xpi, versioned):
        if os.path.exists(out):
            os.remove(out)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for full, rel in files:
                z.write(full, rel)
        print(f"built {out} ({os.path.getsize(out)} bytes, {len(files)} entries)")

    # Sanity: every file readable with forward-slash key
    with zipfile.ZipFile(xpi) as z:
        bad = [n for n in z.namelist() if "\\" in n or n.startswith("./")]
        assert not bad, f"bad entries: {bad}"
        for n in z.namelist():
            z.read(n)
    print("OK: all entries readable, no backslashes")


if __name__ == "__main__":
    main()

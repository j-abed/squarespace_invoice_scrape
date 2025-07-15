#!/usr/bin/env python
"""
trimcookies.py  – extract only Squarespace cookies from a Playwright storage file.

USAGE
-----
python trimcookies.py [SOURCE_JSON] [DEST_JSON]

• SOURCE_JSON  (optional) – full Playwright storage JSON (contains "cookies" + "origins").
• DEST_JSON    (optional) – output path for trimmed cookies file.

If you omit filenames:
  • With only SOURCE_JSON given → DEST_JSON becomes "<source>_trimmed.json".
  • With no args → script picks the newest *.json that contains a "cookies" key
    and writes to "cookies.json".
"""

import json, sys, pathlib, glob, os, datetime

def help_exit():
    print(__doc__)
    sys.exit(0)

def newest_storage_json():
    candidates = sorted(glob.glob("*.json"), key=os.path.getmtime, reverse=True)
    for c in candidates:
        try:
            data = json.loads(pathlib.Path(c).read_text())
            if "cookies" in data:
                return pathlib.Path(c)
        except Exception:
            continue
    return None

def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        help_exit()

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(args) >= 2:
        src = pathlib.Path(args[0])
        dst = pathlib.Path(args[1])
    elif len(args) == 1:
        src = pathlib.Path(args[0])
        dst = src.with_stem(src.stem + "_trimmed")
    else:
        src = newest_storage_json()
        if not src:
            print("❌ No storage JSON with 'cookies' found in current directory.")
            help_exit()
        dst = pathlib.Path("cookies.json")

    if not src.exists():
        print(f"❌ Source file not found: {src}")
        sys.exit(1)

    data = json.loads(src.read_text(encoding="utf-8"))
    cookies = data["cookies"] if isinstance(data, dict) and "cookies" in data else data
    needed = [c for c in cookies if c["domain"].endswith(".squarespace.com")]

    dst.write_text(json.dumps(needed, indent=2), encoding="utf-8")
    print(f"✅ Trimmed {len(cookies)} → {len(needed)} cookies\n   {src} → {dst}")

if __name__ == "__main__":
    main()

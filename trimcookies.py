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
    # Print usage instructions and exit
    print(__doc__)
    sys.exit(0)

def newest_storage_json():
    # Find all .json files, sorted by modification time (newest first)
    candidates = sorted(glob.glob("*.json"), key=os.path.getmtime, reverse=True)
    for c in candidates:
        try:
            # Try to load JSON and check if it has a "cookies" key
            data = json.loads(pathlib.Path(c).read_text())
            if "cookies" in data:
                return pathlib.Path(c)
        except Exception:
            continue
    return None  # No suitable file found

def main():
    # Show help if -h or --help is present
    if "-h" in sys.argv or "--help" in sys.argv:
        help_exit()

    # Collect positional arguments (ignore options)
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(args) >= 2:
        # If two arguments: use as source and destination
        src = pathlib.Path(args[0])
        dst = pathlib.Path(args[1])
    elif len(args) == 1:
        # If one argument: use as source, output to "<source>_trimmed.json"
        src = pathlib.Path(args[0])
        dst = src.with_stem(src.stem + "_trimmed")
    else:
        # No arguments: find newest storage JSON with "cookies"
        src = newest_storage_json()
        if not src:
            print("❌ No storage JSON with 'cookies' found in current directory.")
            help_exit()
        dst = pathlib.Path("cookies.json")

    # Check if source file exists
    if not src.exists():
        print(f"❌ Source file not found: {src}")
        sys.exit(1)

    # Load JSON data from source file
    data = json.loads(src.read_text(encoding="utf-8"))
    # If data is a dict with "cookies", extract the list; else, use data directly
    cookies = data["cookies"] if isinstance(data, dict) and "cookies" in data else data
    # Filter cookies for those whose domain ends with ".squarespace.com"
    needed = [c for c in cookies if c["domain"].endswith(".squarespace.com")]

    # Write filtered cookies to destination file, pretty-printed
    dst.write_text(json.dumps(needed, indent=2), encoding="utf-8")
    # Print summary of operation
    print(f"✅ Trimmed {len(cookies)} → {len(needed)} cookies\n   {src} → {dst}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Watches README.md (and the two page templates) and reruns rebuild.sh
whenever one of them changes — the "automatic update" for an editing
session. No dependencies (plain mtime polling), so nothing to install.

    python3 tools/watch.py            # poll every 1s (default)
    python3 tools/watch.py --every 3  # poll every 3s

Stop with Ctrl+C. It rebuilds once immediately on start, then on every
detected change; a failed build prints the error and keeps watching
(a typo in README.md won't kill the watcher).
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
REBUILD = ROOT / "rebuild.sh"
WATCHED = [
    ROOT / "README.md",
    ROOT / "site" / "template.html",
    ROOT / "pdf" / "template.html",
    ROOT / "tools" / "manifesto.py",
]


def mtimes() -> dict:
    return {p: p.stat().st_mtime for p in WATCHED if p.exists()}


def rebuild():
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] change detected — rebuilding...")
    result = subprocess.run(["bash", str(REBUILD)], cwd=ROOT)
    if result.returncode != 0:
        print(f"[{ts}] build failed (exit {result.returncode}) — still watching.")
    else:
        print(f"[{ts}] done.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--every", type=float, default=1.0, help="poll interval in seconds")
    args = ap.parse_args()

    missing = [p for p in WATCHED if not p.exists()]
    for p in missing:
        print(f"note: {p} does not exist yet, will start watching once it appears")

    print(f"Watching {', '.join(str(p.relative_to(ROOT)) for p in WATCHED)}")
    print("Ctrl+C to stop.\n")

    rebuild()
    last = mtimes()

    try:
        while True:
            time.sleep(args.every)
            current = mtimes()
            if current != last:
                rebuild()
                last = current
    except KeyboardInterrupt:
        print("\nstopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()

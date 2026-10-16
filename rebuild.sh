#!/usr/bin/env bash
# Rebuilds the web page (all three languages) and the PDF in one command.
# Run this after any edit to README.md / README.en.md / README.th.md — or
# use tools/watch.py to do it automatically on every save.
set -euo pipefail
cd "$(dirname "$0")"

echo "→ index.html"
python3 build.py

echo "→ IQJ-manifest.pdf"
python3 pdf/build.py

echo "done."

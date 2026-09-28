#!/usr/bin/env bash
# Rebuilds both the web page and the PDF from README.md in one command.
# Run this after any edit to README.md — or use tools/watch.py to do it
# automatically on every save.
set -euo pipefail
cd "$(dirname "$0")"

echo "→ site/index.html"
python3 site/build.py

echo "→ IQJ-manifest.pdf"
python3 pdf/build.py

echo "done."

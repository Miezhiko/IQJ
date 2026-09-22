#!/usr/bin/env bash
# Local preview server for the manifesto web page.
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-8731}"
echo "Serving on http://localhost:${PORT}  (Ctrl+C to stop)"
python3 -m http.server "$PORT"

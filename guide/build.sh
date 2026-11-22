#!/usr/bin/env bash
# Rebuild guide/*.pdf from guide/src/*.html with headless Chrome.
set -euo pipefail
cd "$(dirname "$0")"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
for src in src/*.html; do
  out="$(basename "${src%.html}").pdf"
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$out" "file://$PWD/$src" 2>/dev/null
  echo "built guide/$out"
done

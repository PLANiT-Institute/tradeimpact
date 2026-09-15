#!/bin/bash
# Double-click to open a database in the Trade data catalogue.
#
# With no argument it opens the automotive database. To review a different file, drag the file
# onto this script in a terminal, or run it with a path:
#     ./dbreview.command data/power/database/tradeimpact_power.sqlite
#     ./dbreview.command ~/Downloads/SOMEONES_EXPORT.sqlite
#
# The window stays open while the server runs; close it or press Ctrl-C to stop.
set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || true)"
  if [ -z "$PY" ]; then
    echo "No Python found. Install it, or create the virtual environment with: uv sync"
    read -r -p "Press return to close." _
    exit 1
  fi
  echo "note: .venv not found, falling back to $PY"
fi

if [ ! -f "data/auto/catalogue.html" ]; then
  echo "Building the catalogue page first…"
  "$PY" script/auto/app/build_catalogue.py
fi

echo
"$PY" script/dbreview.py "$@" || {
  echo
  echo "The reviewer stopped with an error."
  read -r -p "Press return to close." _
  exit 1
}

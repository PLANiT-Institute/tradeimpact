#!/bin/sh
# Run the local compute sidecar (port 8901) alongside next dev, and clean it up on exit.
# Used by `npm run dev:local` — the only supported way to run the calculator locally.
set -e
PY="${TI_PYTHON:-../ti-framework/.venv/bin/python}"
if [ ! -x "$PY" ]; then
  echo "dev_local: python not found at $PY (set TI_PYTHON or create ti-framework/.venv)" >&2
  exit 1
fi
"$PY" scripts/dev_compute.py &
COMPUTE_PID=$!
trap 'kill "$COMPUTE_PID" 2>/dev/null' EXIT INT TERM
TI_COMPUTE_URL=http://127.0.0.1:8901/ npx next dev

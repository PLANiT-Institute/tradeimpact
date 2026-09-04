#!/bin/bash
# Double-click to open the dashboard connected to tradeimpact_auto.sqlite.
#
# A browser will not let a page opened from the file system read the database beside it, so
# this starts the repository's small local server (script/auto/serve_dashboard.py), which serves
# data/auto on http://127.0.0.1:8765, and opens database/dashboard.html in the default browser.
# Close this window (or press Ctrl-C) to stop the server.
set -e
cd "$(dirname "$0")/../../.."
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi
exec "$PY" script/auto/serve_dashboard.py --open

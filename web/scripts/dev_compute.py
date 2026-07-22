#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Local stand-in for the Vercel Python function: serves POST /api/compute on :8901.

Usage:  ../ti-framework/.venv/bin/python scripts/dev_compute.py
Then:   TI_COMPUTE_URL=http://127.0.0.1:8901/ npm run dev
"""

import sys
from http.server import HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
from compute import handler  # noqa: E402

if __name__ == "__main__":
    print("dev compute server on http://127.0.0.1:8901")
    HTTPServer(("127.0.0.1", 8901), handler).serve_forever()

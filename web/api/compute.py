# SPDX-License-Identifier: GPL-3.0-or-later
"""Vercel Python function: POST fixture-shaped inputs -> engine result JSON.

The engine (ti_framework) and the service layer (compute_service) are vendored into
api/_engine by scripts/prepare.mjs at build time — single source of truth, no port.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "_engine"))

from compute_service import compute  # noqa: E402


class handler(BaseHTTPRequestHandler):  # noqa: N801 - Vercel contract
    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("content-length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            result = compute(payload)
            status, body = 200, json.dumps(result)
        except (KeyError, ValueError, TypeError) as e:
            status, body = 400, json.dumps({"error": f"{type(e).__name__}: {e}"})
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

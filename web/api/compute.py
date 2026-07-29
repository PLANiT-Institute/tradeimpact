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

from compute_service import MAX_REQUEST_BYTES, compute  # noqa: E402


class handler(BaseHTTPRequestHandler):  # noqa: N801 - Vercel contract
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        raw_length = self.headers.get("content-length")
        if raw_length is None:
            self._send_json(411, {"error": "Content-Length header required"})
            return
        try:
            length = int(raw_length)
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length header"})
            return
        if length <= 0:
            self._send_json(400, {"error": "Request body must not be empty"})
            return
        if length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": f"Request body exceeds {MAX_REQUEST_BYTES} bytes"})
            return
        try:
            raw_body = self.rfile.read(length)
            if len(raw_body) != length:
                raise ValueError("Incomplete request body")
            payload = json.loads(raw_body)
            result = compute(payload)
            self._send_json(200, result)
        except (KeyError, ValueError, TypeError) as e:
            self._send_json(400, {"error": f"{type(e).__name__}: {e}"})
        except Exception as e:  # pragma: no cover - platform-level defensive boundary
            self.log_error("compute failed: %s", type(e).__name__)
            self._send_json(500, {"error": "Internal calculation error"})

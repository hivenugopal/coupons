"""Vercel endpoint for the protected, requests-only coupon crawler."""

from __future__ import annotations

import json
import os
import secrets
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

# The Vercel function bundle includes src/ through vercel.json.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from couponfinder.service import fetch_and_store


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        expected_token = os.getenv("ADMIN_API_TOKEN", "")
        provided_token = self.headers.get("X-Admin-Token", "")
        if not expected_token:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": "ADMIN_API_TOKEN is not configured."})
            return
        if not secrets.compare_digest(provided_token, expected_token):
            self._send_json(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "Admin authorization is required."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            result = fetch_and_store(payload.get("urls", []), timeout=payload.get("timeout", 8.0))
            self._send_json(HTTPStatus.OK, result)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
        except Exception:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": "Coupon fetching failed."})

    def do_GET(self) -> None:  # noqa: N802
        self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, {"ok": False, "error": "Use POST."})

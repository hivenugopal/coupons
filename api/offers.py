"""Vercel endpoint for public offer metadata and on-demand coupon codes."""

from __future__ import annotations

import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# The Vercel function bundle includes src/ through vercel.json.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from couponfinder.database import get_coupon_code, list_public_offers


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        try:
            query = parse_qs(urlparse(self.path).query)
            code_for = query.get("code_for", [""])[0]
            if code_for:
                try:
                    offer_id = int(code_for)
                except ValueError:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "code_for must be a numeric offer id."})
                    return
                code = get_coupon_code(offer_id)
                if not code:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "Coupon code not found."})
                    return
                self._send_json(HTTPStatus.OK, {"code": code})
                return

            self._send_json(HTTPStatus.OK, {"offers": list_public_offers()})
        except Exception as exc:
            import traceback

            traceback.print_exc()
            message = "Could not load offers."
            detail = str(exc)
            if "DATABASE_URL" in detail:
                message = "DATABASE_URL is not configured."
            elif "psycopg" in detail.lower():
                message = "Database driver is unavailable. Add a root requirements.txt and redeploy."
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": message})


    def do_POST(self) -> None:  # noqa: N802
        self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "Use GET."})

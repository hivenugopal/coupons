"""Public endpoint that records a user click before provider redirect."""

from __future__ import annotations

import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

# The Vercel function bundle includes src/ through vercel.json.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from couponfinder.claims import validate_claim_payload
from couponfinder.database import record_user_claim


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
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            offer_id, email = validate_claim_payload(payload)
            claim = record_user_claim(offer_id, email)
            if not claim:
                self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Offer is no longer available."})
                return
            self._send_json(
                HTTPStatus.CREATED,
                {
                    "ok": True,
                    "claim_id": claim["id"],
                    "date_clicked": claim["date_clicked"],
                    "redirect_url": claim["url"],
                },
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
        except Exception:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": "Could not record click."})

    def do_GET(self) -> None:  # noqa: N802
        self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, {"ok": False, "error": "Use POST."})

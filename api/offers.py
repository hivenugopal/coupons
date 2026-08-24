"""Vercel endpoint for public offer metadata and on-demand coupon codes."""

from __future__ import annotations

import json
import os
import re
import sys
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# The Vercel function bundle includes src/ through vercel.json.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from couponfinder.database import get_claim_details, list_offer_locations, list_public_offers, recent_db_logs


def _public_error_detail(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        text = text.replace(database_url, "[DATABASE_URL]")
    return re.sub(r"(://[^:]+:)([^@]+)(@)", r"\1***\3", text)


class handler(BaseHTTPRequestHandler):
    def log_request(self, code: object = "-", size: object = "-") -> None:
        extra = getattr(self, "_error_summary", "")
        if extra:
            self.log_message('"%s" %s %s %s', self.requestline, str(code), str(size), extra)
            return
        super().log_request(code, size)

    def _send_json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        self._error_summary = ""
        try:
            query = parse_qs(urlparse(self.path).query)
            code_for = query.get("code_for", [""])[0]
            if code_for:
                try:
                    offer_id = int(code_for)
                except ValueError:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "code_for must be a numeric offer id."})
                    return
                details = get_claim_details(offer_id)
                if not details:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "Coupon code not found."})
                    return
                self._send_json(HTTPStatus.OK, details)
                return

            state = (query.get("state", [""])[0] or "").strip()
            city = (query.get("city", [""])[0] or "").strip()
            if state and city:
                self._send_json(HTTPStatus.OK, {"offers": list_public_offers(state, city)})
                return

            pairs = list_offer_locations()
            cities_by_state: dict[str, list[str]] = {}
            for pair in pairs:
                cities_by_state.setdefault(pair["state"], [])
                if pair["city"] not in cities_by_state[pair["state"]]:
                    cities_by_state[pair["state"]].append(pair["city"])
            self._send_json(
                HTTPStatus.OK,
                {"states": sorted(cities_by_state), "citiesByState": cities_by_state},
            )
        except Exception as exc:
            traceback.print_exc()
            detail = _public_error_detail(exc)
            message = "Could not load offers."
            if "DATABASE_URL" in str(exc):
                message = "DATABASE_URL is not configured."
            elif "psycopg" in str(exc).lower() or "psycopg" in type(exc).__name__.lower():
                message = "Database driver is unavailable."
            db_logs = recent_db_logs()
            self._error_summary = f"error={message} detail={detail} db_logs={db_logs}"
            print("OFFERS_API_ERROR", self._error_summary, file=sys.stderr, flush=True)
            for line in db_logs:
                print(line, file=sys.stderr, flush=True)
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": message, "detail": detail, "db_logs": db_logs},
            )


    def do_POST(self) -> None:  # noqa: N802
        self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "Use GET."})

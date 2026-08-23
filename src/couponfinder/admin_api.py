"""Minimal admin API to trigger coupon fetching from a URL list."""

from __future__ import annotations

import json
import os
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
from typing import Any

from .cli import CSV_FIELDNAMES, _load_config, _write_csv
from .crawler import FetchError, fetch_html, fetch_rendered_html
from .database import insert_coupon_rows
from .extractor import extract_coupon_codes, extract_offer_details


def _as_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _load_local_env(path: str = ".env") -> None:
    """Load local secrets without overriding variables explicitly exported by the shell."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name and name not in os.environ:
            os.environ[name] = value.strip().strip('"').strip("'")


def _insert_rows_to_postgres(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Upsert extracted rows using the same database path as the deployed API."""
    records_inserted = insert_coupon_rows(rows)
    return {
        "schema": os.getenv("DB_SCHEMA", "coupons"),
        "table": os.getenv("DB_TABLE", "gc_coupons"),
        "records_inserted": records_inserted,
    }


def _offer_preview(row: dict[str, Any]) -> dict[str, str]:
    """Public fields shown in the local admin JSON after a URL is processed."""
    return {
        "coupon": row.get("code", "") or "",
        "price": row.get("price", "") or "",
        "address_line1": row.get("address_line1", "") or "",
        "address_line2": row.get("address_line2", "") or "",
        "city": row.get("city", "") or "",
        "state": row.get("state", "") or "",
    }


def _render_fetch_page(result: dict[str, Any] | None = None, error_message: str = "") -> str:
    result_json = ""
    if result:
        result_json = json.dumps(result, indent=2)

    error_html = (
        f'<p style="color:#b00020;font-weight:600;">{escape(error_message)}</p>' if error_message else ""
    )
    result_html = (
        f"<pre style=\"background:#f7f7f7;padding:12px;border-radius:8px;overflow:auto;\">{escape(result_json)}</pre>"
        if result_json
        else ""
    )
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Fetch Coupons Admin</title>
    <style>
      body {{ font-family: Segoe UI, Arial, sans-serif; margin: 28px; max-width: 960px; }}
      textarea {{ width: 100%; min-height: 160px; padding: 10px; font-family: Consolas, monospace; }}
      .row {{ display: flex; gap: 12px; align-items: center; margin: 10px 0; flex-wrap: wrap; }}
      input[type=text], input[type=number] {{ padding: 6px 8px; min-width: 220px; }}
      button {{ padding: 8px 14px; cursor: pointer; }}
      .hint {{ color: #555; font-size: 0.95rem; }}
    </style>
  </head>
  <body>
    <h1>Fetch Coupons</h1>
    <p class=\"hint\">This local-only tool opens a browser, appends results to CSV, and upserts them into Supabase.</p>
    <p class=\"hint\"><strong>Warning:</strong> clicking Print Coupon can redeem or invalidate a one-time offer. Confirm only when you intend to reveal the offer.</p>
    {error_html}
    <form method=\"post\" action=\"/fetch-coupons\">
      <textarea name=\"urls_text\" placeholder=\"https://offers.greatclips.com/vqZhNYR&#10;https://offers.greatclips.com/DRd0nhA\"></textarea>
      <div class=\"row\">
        <label>Timeout (seconds): <input type=\"number\" step=\"0.5\" name=\"timeout\" value=\"10\" /></label>
        <label><input type=\"checkbox\" name=\"render\" value=\"1\" checked /> Render page</label>
        <label><input type=\"checkbox\" name=\"insert_db\" value=\"1\" checked /> Insert into DB</label>
      </div>
      <div class=\"row\">
        <label>Click selector: <input type=\"text\" name=\"click_selector\" value=\"#redemption\" /></label>
        <label>Wait selector: <input type=\"text\" name=\"wait_selector\" value=\"#credential-code\" /></label>
      </div>
      <div class=\"row\">
        <label><input type=\"checkbox\" name=\"confirm_reveal\" value=\"1\" /> I understand this click may redeem or invalidate an offer.</label>
      </div>
      <button type=\"submit\">Process URLs</button>
    </form>
    {result_html}
  </body>
</html>
"""


def _build_rows_for_url(
    url: str,
    timeout: float,
    render: bool,
    wait_selector: str | None,
    click_selector: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        if render or wait_selector or click_selector:
            html = fetch_rendered_html(
                url,
                timeout=timeout,
                wait_selector=wait_selector,
                click_selector=click_selector,
            )
        else:
            html = fetch_html(url, timeout=timeout)
    except FetchError as exc:
        row = {field: "" for field in CSV_FIELDNAMES} | {"url": url, "error": str(exc)}
        return [row], {
            "url": url,
            "ok": False,
            "error": str(exc),
            "rows_written": 1,
            "offers": [_offer_preview(row)],
        }

    codes = extract_coupon_codes(html, url=url)
    details_list = extract_offer_details(html, url=url)
    rows: list[dict[str, Any]] = []

    for details in details_list:
        base_row = {
            "url": url,
            "price": details.price or "",
            "location": details.location or "",
            "store_name": details.store_name or "",
            "address_line1": details.address_line1 or "",
            "address_line2": details.address_line2 or "",
            "city": details.city or "",
            "state": details.state or "",
            "expires": details.expires or "",
            "error": "",
        }
        if codes:
            for code in codes:
                rows.append({**base_row, "code": code.code, "confidence": code.confidence, "source": code.source})
        else:
            rows.append({**base_row, "code": "", "confidence": "", "source": ""})

    return rows, {
        "url": url,
        "ok": True,
        "codes_found": len(codes),
        "rows_written": len(rows),
        "offers": [_offer_preview(row) for row in rows],
    }


def run_fetch(
    urls: list[str],
    timeout: float = 10.0,
    render: bool = True,
    wait_selector: str | None = "#credential-code",
    click_selector: str | None = "#redemption",
    output_file: str | None = None,
    insert_db: bool = True,
    confirm_reveal: bool = False,
) -> dict[str, Any]:
    config = _load_config("config.ini")
    output_path = output_file or config.get("output-file")
    if not output_path:
        raise ValueError("No output file configured. Set output-file in config.ini or pass output_file.")
    if click_selector and not confirm_reveal:
        raise ValueError(
            "Confirm the reveal action before clicking a coupon button; it may redeem or invalidate a one-time offer."
        )

    deduped_urls = list(dict.fromkeys(url.strip() for url in urls if url and url.strip()))
    if not deduped_urls:
        raise ValueError("Provide at least one URL")

    all_rows: list[dict[str, Any]] = []
    per_url: list[dict[str, Any]] = []
    for url in deduped_urls:
        rows, meta = _build_rows_for_url(url, timeout, render, wait_selector, click_selector)
        all_rows.extend(rows)
        per_url.append(meta)

    _write_csv(output_path, all_rows)
    payload = {
        "ok": True,
        "output_file": output_path,
        "urls_received": len(urls),
        "urls_processed": len(deduped_urls),
        "rows_appended": len(all_rows),
        "offers": [_offer_preview(row) for row in all_rows],
        "results": per_url,
    }
    if insert_db:
        payload["database"] = _insert_rows_to_postgres(all_rows)
    return payload


class _Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/" or self.path == "":
            self._send_json(
                200,
                {
                    "ok": True,
                    "service": "couponfinder-admin-api",
                    "usage": "POST /fetch-coupons with JSON: {\"urls\": [\"https://...\"]}",
                },
            )
            return

        if self.path == "/fetch-coupons":
            self._send_html(200, _render_fetch_page())
            return

        self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/fetch-coupons":
            self._send_json(404, {"ok": False, "error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length)
            content_type = (self.headers.get("Content-Type") or "").lower()
            is_form = "application/x-www-form-urlencoded" in content_type

            if is_form:
                form = parse_qs(raw.decode("utf-8"), keep_blank_values=True)
                urls_text = (form.get("urls_text", [""])[0] or "").strip()
                urls = [line.strip() for line in urls_text.splitlines() if line.strip()]
                payload = {
                    "urls": urls,
                    "timeout": form.get("timeout", ["10"])[0],
                    "render": "render" in form,
                    "insert_db": "insert_db" in form,
                    "confirm_reveal": "confirm_reveal" in form,
                    "wait_selector": form.get("wait_selector", ["#credential-code"])[0],
                    "click_selector": form.get("click_selector", ["#redemption"])[0],
                }
            else:
                payload = json.loads(raw.decode("utf-8") or "{}")

            urls = payload.get("urls") or []
            result = run_fetch(
                urls=urls,
                timeout=float(payload.get("timeout", 10.0)),
                render=_as_bool(payload.get("render", True)),
                insert_db=_as_bool(payload.get("insert_db", True)),
                confirm_reveal=_as_bool(payload.get("confirm_reveal", False), default=False),
                wait_selector=payload.get("wait_selector", "#credential-code"),
                click_selector=payload.get("click_selector", "#redemption"),
                output_file=payload.get("output_file"),
            )
            if is_form:
                self._send_html(200, _render_fetch_page(result=result))
            else:
                self._send_json(200, result)
        except Exception as exc:  # broad on purpose for API response safety
            if (self.headers.get("Content-Type") or "").lower().startswith("application/x-www-form-urlencoded"):
                self._send_html(400, _render_fetch_page(error_message=str(exc)))
            else:
                self._send_json(400, {"ok": False, "error": str(exc)})


def main(host: str = "127.0.0.1", port: int = 8000) -> int:
    _load_local_env()
    server = ThreadingHTTPServer((host, port), _Handler)
    print(f"couponfinder admin API listening at http://{host}:{port}")
    print("Open /fetch-coupons to use the local Playwright reveal workflow.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

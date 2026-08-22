"""Serverless-safe coupon fetching orchestration."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from .cli import CSV_FIELDNAMES
from .crawler import FetchError, fetch_html
from .database import insert_coupon_rows
from .extractor import extract_coupon_codes, extract_offer_details

MAX_URLS_PER_REQUEST = 10


def _allowed_hosts() -> set[str]:
    configured = os.getenv("ALLOWED_COUPON_HOSTS", "offers.greatclips.com")
    return {host.strip().lower() for host in configured.split(",") if host.strip()}


def _validate_url(url: str) -> str:
    cleaned = url.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() not in _allowed_hosts():
        allowed_hosts = ", ".join(sorted(_allowed_hosts()))
        raise ValueError(f"URL must use HTTPS and target an allowed host: {allowed_hosts}")
    return cleaned


def _build_rows_for_url(url: str, timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch one URL without a browser and turn the extraction result into DB rows."""
    try:
        html = fetch_html(url, timeout=timeout)
    except FetchError as exc:
        row = {field: "" for field in CSV_FIELDNAMES} | {"url": url, "error": str(exc)}
        return [row], {"url": url, "ok": False, "error": str(exc), "rows_written": 1}

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
            rows.extend(
                {**base_row, "code": code.code, "confidence": code.confidence, "source": code.source}
                for code in codes
            )
        else:
            rows.append({**base_row, "code": "", "confidence": "", "source": ""})

    return rows, {"url": url, "ok": True, "codes_found": len(codes), "rows_written": len(rows)}


def fetch_and_store(urls: list[str], timeout: float = 8.0) -> dict[str, Any]:
    """Fetch URLs, persist their extracted records, and return per-URL status.

    This intentionally uses requests only: Vercel serverless functions cannot run
    the Playwright-based reveal path used by the former local admin server.
    """
    if not isinstance(urls, list):
        raise ValueError("'urls' must be an array.")
    if len(urls) > MAX_URLS_PER_REQUEST:
        raise ValueError(f"Submit no more than {MAX_URLS_PER_REQUEST} URLs at a time.")

    deduped_urls = list(dict.fromkeys(_validate_url(url) for url in urls if isinstance(url, str) and url.strip()))
    if not deduped_urls:
        raise ValueError("Provide at least one allowed URL.")

    timeout = min(max(float(timeout), 1.0), 10.0)
    rows: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for url in deduped_urls:
        url_rows, metadata = _build_rows_for_url(url, timeout)
        rows.extend(url_rows)
        results.append(metadata)

    return {
        "ok": True,
        "urls_received": len(urls),
        "urls_processed": len(deduped_urls),
        "rows_stored": insert_coupon_rows(rows),
        "results": results,
    }

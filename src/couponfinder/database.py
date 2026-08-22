"""PostgreSQL persistence and read helpers for the deployed coupon finder."""

from __future__ import annotations

import datetime as dt
import os
import re
from typing import Any

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_OFFER_COLUMNS = [
    "url",
    "code",
    "confidence",
    "source",
    "price",
    "location",
    "store_name",
    "address_line1",
    "address_line2",
    "city",
    "state",
    "expires",
    "error",
    "status",
]


def normalize_expiry_date(value: str) -> str | None:
    """Convert supported crawler expiry formats into a PostgreSQL date value."""
    value = (value or "").strip()
    for pattern in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            continue
    return None


def rows_to_db_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map extractor rows into the database's normalized record shape."""
    return [
        {
            "url": row.get("url", ""),
            "code": row.get("code", ""),
            "confidence": row.get("confidence", ""),
            "source": row.get("source", ""),
            "price": row.get("price", ""),
            "location": row.get("location", ""),
            "store_name": row.get("store_name", ""),
            "address_line1": row.get("address_line1", ""),
            "address_line2": row.get("address_line2", ""),
            "city": row.get("city", ""),
            "state": row.get("state", ""),
            "expires": normalize_expiry_date(row.get("expires", "")),
            "error": row.get("error", ""),
            "status": "failed" if row.get("error") else "fetched",
        }
        for row in rows
    ]


def _database_settings() -> tuple[str, str, str]:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise ValueError("DATABASE_URL is not configured.")

    schema = _safe_identifier(os.getenv("DB_SCHEMA", "coupons"), "schema")
    table = _safe_identifier(os.getenv("DB_TABLE", "gc_coupons"), "table")
    return database_url, schema, table


def _safe_identifier(value: str, kind: str) -> str:
    cleaned = value.strip()
    if not _IDENTIFIER_PATTERN.fullmatch(cleaned):
        raise ValueError(f"Invalid database {kind}: {value!r}")
    return cleaned


def _connect() -> Any:
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("The psycopg dependency is unavailable.") from exc
    database_url, _, _ = _database_settings()
    return psycopg.connect(database_url)


def insert_coupon_rows(rows: list[dict[str, Any]]) -> int:
    """Insert extraction rows, updating a matching URL/code/location record."""
    if not rows:
        return 0

    _, schema, table = _database_settings()
    records = rows_to_db_records(rows)
    values = [tuple(record[column] for column in _OFFER_COLUMNS) for record in records]
    placeholders = ", ".join(["%s"] * len(_OFFER_COLUMNS))
    update_columns = ", ".join(
        f"{column} = EXCLUDED.{column}" for column in _OFFER_COLUMNS if column not in {"url", "code", "location"}
    )
    sql = (
        f'INSERT INTO "{schema}"."{table}" ({", ".join(_OFFER_COLUMNS)}) VALUES ({placeholders}) '
        f'ON CONFLICT (url, code, location) DO UPDATE SET {update_columns}'
    )
    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(sql, values)
        conn.commit()
    return len(records)


def list_public_offers() -> list[dict[str, Any]]:
    """Return offer details without coupon codes; codes are fetched on demand."""
    _, schema, table = _database_settings()
    sql = (
        f'SELECT id, url, price, location, store_name AS "storeName", '
        f'address_line1 AS "addressLine1", address_line2 AS "addressLine2", city, state, expires, '
        f'(code <> \'\') AS "hasCode" '
        f'FROM "{schema}"."{table}" '
        "WHERE status = 'fetched' AND error = '' AND location <> '' "
        "ORDER BY expires NULLS LAST, city, location"
    )
    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            columns = [column.name for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_coupon_code(offer_id: int) -> str | None:
    """Return a stored coupon code for a public offer identifier."""
    _, schema, table = _database_settings()
    sql = (
        f'SELECT code FROM "{schema}"."{table}" '
        "WHERE id = %s AND status = 'fetched' AND error = ''"
    )
    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (offer_id,))
            row = cursor.fetchone()
    return row[0] if row and row[0] else None

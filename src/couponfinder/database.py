"""PostgreSQL persistence and read helpers for the deployed coupon finder."""

from __future__ import annotations

import datetime as dt
import os
import re
import sys
from typing import Any
from urllib.parse import parse_qs, urlparse

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
_DB_DEBUG_EVENTS: list[str] = []


def _db_log(message: str) -> None:
    line = f"[couponfinder.db] {message}"
    _DB_DEBUG_EVENTS.append(line)
    print(line, file=sys.stderr, flush=True)


def recent_db_logs() -> list[str]:
    """Return in-process database debug lines for API error responses."""
    return list(_DB_DEBUG_EVENTS)


recent_db_logs = recent_db_logs


def _reset_db_logs() -> None:
    _DB_DEBUG_EVENTS.clear()


def _safe_url_summary(database_url: str) -> dict[str, Any]:
    parsed = urlparse(database_url)
    query = parse_qs(parsed.query)
    return {
        "scheme": parsed.scheme or "",
        "user": parsed.username or "",
        "host": parsed.hostname or "",
        "port": parsed.port,
        "database": (parsed.path or "").lstrip("/"),
        "password_set": bool(parsed.password),
        "sslmode": (query.get("sslmode") or [None])[0],
        "query_keys": sorted(query),
    }


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
    raw_schema = os.getenv("DB_SCHEMA", "coupons")
    raw_table = os.getenv("DB_TABLE", "gc_coupons")
    _db_log(
        "settings: "
        f"DATABASE_URL_set={bool(database_url)} "
        f"DB_SCHEMA={raw_schema!r} DB_TABLE={raw_table!r}"
    )
    if not database_url:
        _db_log("settings: DATABASE_URL is missing or empty")
        raise ValueError("DATABASE_URL is not configured.")

    schema = _safe_identifier(raw_schema, "schema")
    table = _safe_identifier(raw_table, "table")
    return database_url, schema, table


def _safe_identifier(value: str, kind: str) -> str:
    cleaned = value.strip()
    if not _IDENTIFIER_PATTERN.fullmatch(cleaned):
        raise ValueError(f"Invalid database {kind}: {value!r}")
    return cleaned


def _connect() -> Any:
    _db_log("connect: start")
    try:
        import psycopg
    except ImportError as exc:
        _db_log(f"connect: psycopg import failed: {exc}")
        raise RuntimeError("The psycopg dependency is unavailable.") from exc

    _db_log(f"connect: psycopg imported version={getattr(psycopg, '__version__', 'unknown')}")
    database_url, schema, table = _database_settings()
    summary = _safe_url_summary(database_url)
    _db_log(
        "connect: env "
        f"url_set=True schema={schema} table={table} "
        f"scheme={summary['scheme']} user={summary['user']} host={summary['host']} "
        f"port={summary['port']} database={summary['database']} "
        f"password_set={summary['password_set']} sslmode={summary['sslmode']}"
    )
    if not summary["host"]:
        _db_log("connect: URL did not parse a host; check password URL-encoding")
    if "sslmode=" not in database_url.lower():
        joiner = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{joiner}sslmode=require"
        _db_log("connect: appended sslmode=require")
    else:
        _db_log("connect: sslmode already present in URL")

    try:
        # Transaction pooler (port 6543 / PgBouncer) does not support prepared statements.
        _db_log("connect: opening psycopg connection prepare_threshold=None connect_timeout=10")
        conn = psycopg.connect(database_url, prepare_threshold=None, connect_timeout=10)
    except Exception as exc:
        _db_log(f"connect: failed ({type(exc).__name__}): {exc}")
        raise

    _db_log(f"connect: opened autocommit={getattr(conn, 'autocommit', None)}")
    return conn


def insert_coupon_rows(rows: list[dict[str, Any]]) -> int:
    """Insert extraction rows, updating a matching URL/code/location record."""
    _reset_db_logs()
    if not rows:
        _db_log("insert: skipped empty row list")
        return 0

    _, schema, table = _database_settings()
    _db_log(f"insert: {len(rows)} source rows into {schema}.{table}")
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
    _db_log(f"insert: committed {len(records)} records")
    return len(records)


def list_public_offers() -> list[dict[str, Any]]:
    """Return offer details without coupon codes; codes are fetched on demand."""
    _reset_db_logs()
    _, schema, table = _database_settings()
    _db_log(f"list_public_offers: querying {schema}.{table}")
    sql = (
        f'SELECT id, url, price, location, store_name AS "storeName", '
        f'address_line1 AS "addressLine1", address_line2 AS "addressLine2", city, state, expires, '
        f'(code <> \'\') AS "hasCode" '
        f'FROM "{schema}"."{table}" '
        "WHERE status = 'fetched' AND error = '' AND location <> '' "
        "ORDER BY expires NULLS LAST, city, location"
    )
    try:
        with _connect() as conn:
            with conn.cursor() as cursor:
                _db_log("list_public_offers: executing SELECT")
                cursor.execute(sql)
                columns = [column.name for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as exc:
        _db_log(f"list_public_offers: failed ({type(exc).__name__}): {exc}")
        raise
    _db_log(f"list_public_offers: returned {len(rows)} rows columns={columns}")
    return rows


def get_coupon_code(offer_id: int) -> str | None:
    """Return a stored coupon code for a public offer identifier."""
    _reset_db_logs()
    _, schema, table = _database_settings()
    _db_log(f"get_coupon_code: id={offer_id} from {schema}.{table}")
    sql = (
        f'SELECT code FROM "{schema}"."{table}" '
        "WHERE id = %s AND status = 'fetched' AND error = ''"
    )
    try:
        with _connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (offer_id,))
                row = cursor.fetchone()
    except Exception as exc:
        _db_log(f"get_coupon_code: failed ({type(exc).__name__}): {exc}")
        raise
    found = bool(row and row[0])
    _db_log(f"get_coupon_code: found={found}")
    return row[0] if found else None


recent_db_logs = recent_db_logs

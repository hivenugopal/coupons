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


def _env_identifier(name: str, default: str, kind: str) -> str:
    raw = os.getenv(name, default)
    cleaned = (raw or "").strip().strip('"').strip("'")
    if _IDENTIFIER_PATTERN.fullmatch(cleaned):
        return cleaned
    _db_log(
        f"settings: {name} is not a valid {kind} identifier "
        f"(looks_like_url={cleaned.lower().startswith(('postgres', 'http'))}); using {default!r}"
    )
    return default


def _database_settings() -> tuple[str, str, str]:
    database_url = os.getenv("DATABASE_URL", "").strip()
    schema = _env_identifier("DB_SCHEMA", "coupons", "schema")
    table = _env_identifier("DB_TABLE", "gc_coupons", "table")
    _db_log(
        "settings: "
        f"DATABASE_URL_set={bool(database_url)} "
        f"schema={schema} table={table}"
    )
    if not database_url:
        _db_log("settings: DATABASE_URL is missing or empty")
        raise ValueError("DATABASE_URL is not configured.")
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
    if summary["host"] and "pooler.supabase.com" in summary["host"] and summary["user"] == "postgres":
        _db_log(
            "connect: pooler URLs must use user postgres.<project-ref>, not postgres; "
            "copy the Transaction pooler URI from Supabase"
        )
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
    """Insert extraction rows. If a URL was fetched before, mark old rows inactive."""
    _reset_db_logs()
    if not rows:
        _db_log("insert: skipped empty row list")
        return 0

    _, schema, table = _database_settings()
    _db_log(f"insert: {len(rows)} source rows into {schema}.{table}")
    records = rows_to_db_records(rows)
    values = [tuple(record[column] for column in _OFFER_COLUMNS) for record in records]
    placeholders = ", ".join(["%s"] * len(_OFFER_COLUMNS))
    sql = (
        f'INSERT INTO "{schema}"."{table}" ({", ".join(_OFFER_COLUMNS)}) VALUES ({placeholders})'
    )
    urls = list(dict.fromkeys(record["url"] for record in records if record.get("url")))
    with _connect() as conn:
        with conn.cursor() as cursor:
            if urls:
                cursor.execute(
                    f'UPDATE "{schema}"."{table}" '
                    "SET status = 'inactive', updated_at = NOW() "
                    "WHERE url = ANY(%s) AND status <> 'inactive'",
                    (urls,),
                )
                _db_log(f"insert: marked {cursor.rowcount} existing row(s) inactive for {len(urls)} URL(s)")
            cursor.executemany(sql, values)
        conn.commit()
    _db_log(f"insert: committed {len(records)} new records")
    return len(records)


_ACTIVE_OFFER_FILTER = (
    "status = 'fetched' AND COALESCE(status, '') <> 'inactive' AND error = '' "
    "AND location <> '' AND code IS NOT NULL AND BTRIM(code) <> ''"
)


def list_offer_locations() -> list[dict[str, str]]:
    """Return distinct active cities grouped by state for the offers picker."""
    _reset_db_logs()
    _, schema, table = _database_settings()
    sql = (
        f'SELECT DISTINCT state, city FROM "{schema}"."{table}" '
        f"WHERE {_ACTIVE_OFFER_FILTER} AND state <> '' AND city <> '' "
        "ORDER BY state, city"
    )
    _db_log(f"list_offer_locations: querying {schema}.{table}")
    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = [{"state": row[0], "city": row[1]} for row in cursor.fetchall()]
    _db_log(f"list_offer_locations: returned {len(rows)} pairs")
    return rows


def list_public_offers(state: str, city: str) -> list[dict[str, Any]]:
    """Return active offers for one city, without coupon codes."""
    _reset_db_logs()
    _, schema, table = _database_settings()
    _db_log(f"list_public_offers: querying {schema}.{table} state={state!r} city={city!r}")
    sql = (
        f'SELECT id, url, price, location, store_name AS "storeName", '
        f'address_line1 AS "addressLine1", address_line2 AS "addressLine2", city, state, expires, '
        f'(code <> \'\') AS "hasCode" '
        f'FROM "{schema}"."{table}" '
        f"WHERE {_ACTIVE_OFFER_FILTER} AND state = %s AND city = %s "
        "ORDER BY expires NULLS LAST, location"
    )
    try:
        with _connect() as conn:
            with conn.cursor() as cursor:
                _db_log("list_public_offers: executing SELECT")
                cursor.execute(sql, (state, city))
                columns = [column.name for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as exc:
        _db_log(f"list_public_offers: failed ({type(exc).__name__}): {exc}")
        raise
    _db_log(f"list_public_offers: returned {len(rows)} rows")
    return rows


def get_claim_details(offer_id: int) -> dict[str, Any] | None:
    """Return coupon and offer copy for the claim page."""
    _reset_db_logs()
    _, schema, table = _database_settings()
    _db_log(f"get_claim_details: id={offer_id} from {schema}.{table}")
    sql = (
        f'SELECT code AS coupon, price, location, city, state, expires '
        f'FROM "{schema}"."{table}" '
        f"WHERE id = %s AND {_ACTIVE_OFFER_FILTER}"
    )
    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (offer_id,))
            row = cursor.fetchone()
            if not row:
                _db_log("get_claim_details: not found")
                return None
            columns = [column.name for column in cursor.description]
    details = dict(zip(columns, row))
    _db_log("get_claim_details: found")
    return details


def get_coupon_code(offer_id: int) -> str | None:
    """Return a stored coupon code for a public offer identifier."""
    details = get_claim_details(offer_id)
    if not details:
        return None
    code = details.get("coupon")
    return code if code else None

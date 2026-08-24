from couponfinder import database
from couponfinder.database import _safe_url_summary, normalize_expiry_date, rows_to_db_records


def test_normalize_expiry_date_returns_iso_date():
    assert normalize_expiry_date("08/23/2026") == "2026-08-23"
    assert normalize_expiry_date("08/23/26") == "2026-08-23"
    assert normalize_expiry_date("not a date") is None


def test_rows_to_db_records_sets_status_and_normalizes_expiry():
    records = rows_to_db_records(
        [
            {"url": "https://offers.greatclips.com/example", "code": "SAVE20", "expires": "08/23/2026"},
            {"url": "https://offers.greatclips.com/failed", "error": "timed out"},
        ]
    )

    assert records[0]["status"] == "fetched"
    assert records[0]["expires"] == "2026-08-23"
    assert records[1]["status"] == "failed"


def test_safe_url_summary_omits_password():
    summary = _safe_url_summary(
        "postgresql://postgres.abc:secret-pass@aws-0-us-west-2.pooler.supabase.com:6543/postgres"
    )
    assert summary["host"] == "aws-0-us-west-2.pooler.supabase.com"
    assert summary["port"] == 6543
    assert summary["user"] == "postgres.abc"
    assert summary["password_set"] is True
    assert "secret-pass" not in str(summary)


class _FakeCursor:
    def __init__(self) -> None:
        self.statements: list[tuple[str, object]] = []
        self.rowcount = 2

    def execute(self, sql, params=None):
        self.statements.append((sql, params))

    def executemany(self, sql, values):
        self.statements.append((sql, values))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_insert_coupon_rows_inactivates_existing_url_then_inserts(monkeypatch):
    cursor = _FakeCursor()
    conn = _FakeConnection(cursor)
    monkeypatch.setattr(database, "_database_settings", lambda: ("postgresql://unused", "coupons", "gc_coupons"))
    monkeypatch.setattr(database, "_connect", lambda: conn)

    count = database.insert_coupon_rows(
        [{"url": "https://offers.greatclips.com/OloluXg", "code": "SAVE20", "location": "Ft. Wayne"}]
    )

    assert count == 1
    assert conn.committed is True
    update_sql, update_params = cursor.statements[0]
    assert "status = 'inactive'" in update_sql
    assert "ON CONFLICT" not in update_sql
    assert update_params == (["https://offers.greatclips.com/OloluXg"],)
    insert_sql, insert_values = cursor.statements[1]
    assert insert_sql.strip().startswith("INSERT INTO")
    assert "ON CONFLICT" not in insert_sql
    assert insert_values[0][0] == "https://offers.greatclips.com/OloluXg"

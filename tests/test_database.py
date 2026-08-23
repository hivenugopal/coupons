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

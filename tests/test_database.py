from couponfinder.database import normalize_expiry_date, rows_to_db_records


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

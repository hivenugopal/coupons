import pytest

from couponfinder import database
from couponfinder.claims import validate_claim_payload


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"offer_id": 7, "email": "Jane.Doe+tag@Gmail.com "}, (7, "jane.doe+tag@gmail.com")),
        ({"offer_id": "12", "email": "first.last@company.co.uk"}, (12, "first.last@company.co.uk")),
    ],
)
def test_validate_claim_payload_accepts_offer_id_and_email(payload, expected):
    assert validate_claim_payload(payload) == expected


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"offer_id": 0, "email": "jane.doe@gmail.com"},
        {"offer_id": True, "email": "jane.doe@gmail.com"},
        {"offer_id": 1, "email": "not-an-email"},
        {"offer_id": 1, "email": ""},
        {"offer_id": 1, "email": "abc@abc.abc"},
        {"offer_id": 1, "email": "user@example.com"},
        {"offer_id": 1, "email": "test@mail.com"},
        {"offer_id": 1, "email": "a@b.c"},
        {"offer_id": 1, "email": "name@localhost"},
        {"offer_id": 1, "email": "jane@domain.c"},
        {"offer_id": 1, "email": "jane@domain.123"},
    ],
)
def test_validate_claim_payload_rejects_invalid_values(payload):
    with pytest.raises(ValueError):
        validate_claim_payload(payload)


class _Column:
    def __init__(self, name):
        self.name = name


class _ClaimCursor:
    def __init__(self, offer):
        self.offer = offer
        self.statements = []
        self.description = []
        self._result = None

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        if len(self.statements) == 1:
            self._result = self.offer
        else:
            self._result = (41, "2026-08-25T12:00:00+00:00")
            self.description = [_Column("id"), _Column("date_clicked")]

    def fetchone(self):
        return self._result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _ClaimConnection:
    def __init__(self, cursor):
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


def test_record_user_claim_uses_database_offer_url_and_leaves_code_null(monkeypatch):
    cursor = _ClaimCursor(("https://offers.greatclips.com/offer",))
    conn = _ClaimConnection(cursor)
    monkeypatch.setattr(database, "_database_settings", lambda: ("postgresql://unused", "coupons", "gc_coupons"))
    monkeypatch.setattr(database, "_connect", lambda: conn)

    result = database.record_user_claim(9, "user@example.com")

    assert result == {
        "id": 41,
        "date_clicked": "2026-08-25T12:00:00+00:00",
        "url": "https://offers.greatclips.com/offer",
    }
    assert conn.committed is True
    assert cursor.statements[0][1] == (9,)
    insert_sql, insert_params = cursor.statements[1]
    assert "coupon_code" in insert_sql
    assert "NULL" in insert_sql
    assert insert_params == ("user@example.com", 9, "https://offers.greatclips.com/offer")


def test_record_user_claim_skips_inactive_or_unknown_offer(monkeypatch):
    cursor = _ClaimCursor(None)
    conn = _ClaimConnection(cursor)
    monkeypatch.setattr(database, "_database_settings", lambda: ("postgresql://unused", "coupons", "gc_coupons"))
    monkeypatch.setattr(database, "_connect", lambda: conn)

    assert database.record_user_claim(9, "user@example.com") is None
    assert len(cursor.statements) == 1
    assert conn.committed is False

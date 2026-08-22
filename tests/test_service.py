import pytest

from couponfinder.service import _validate_url


def test_validate_url_allows_default_coupon_host(monkeypatch):
    monkeypatch.delenv("ALLOWED_COUPON_HOSTS", raising=False)
    assert _validate_url("https://offers.greatclips.com/abc") == "https://offers.greatclips.com/abc"


@pytest.mark.parametrize(
    "url",
    [
        "http://offers.greatclips.com/abc",
        "https://example.com/abc",
        "https://127.0.0.1/private",
    ],
)
def test_validate_url_rejects_disallowed_or_insecure_urls(url):
    with pytest.raises(ValueError):
        _validate_url(url)

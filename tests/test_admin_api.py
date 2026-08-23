from couponfinder import admin_api
from couponfinder.models import CouponCode, OfferDetails


def test_local_admin_uses_rendered_html_with_configured_selectors(monkeypatch):
    captured: dict[str, object] = {}

    def fake_rendered_html(url, timeout, wait_selector, click_selector):
        captured.update(
            url=url,
            timeout=timeout,
            wait_selector=wait_selector,
            click_selector=click_selector,
        )
        return "<html>rendered</html>"

    monkeypatch.setattr(admin_api, "fetch_rendered_html", fake_rendered_html)
    monkeypatch.setattr(
        admin_api,
        "extract_coupon_codes",
        lambda html, url: [CouponCode("SAVE20", url, "high", "test")],
    )
    monkeypatch.setattr(
        admin_api,
        "extract_offer_details",
        lambda html, url: [
            OfferDetails(
                url=url,
                price="$9.99",
                location="Example store",
                address_line1="Eagle Eye Plaza",
                address_line2="4840 Asbury Rd",
                city="Ft. Wayne",
                state="IN",
            )
        ],
    )

    rows, metadata = admin_api._build_rows_for_url(
        "https://offers.greatclips.com/example",
        timeout=12.0,
        render=True,
        wait_selector="#revealed-code",
        click_selector="button.print-coupon",
    )

    assert captured == {
        "url": "https://offers.greatclips.com/example",
        "timeout": 12.0,
        "wait_selector": "#revealed-code",
        "click_selector": "button.print-coupon",
    }
    assert metadata["codes_found"] == 1
    assert rows[0]["code"] == "SAVE20"
    assert metadata["offers"] == [
        {
            "coupon": "SAVE20",
            "price": "$9.99",
            "address_line1": "Eagle Eye Plaza",
            "address_line2": "4840 Asbury Rd",
            "city": "Ft. Wayne",
            "state": "IN",
        }
    ]


def test_run_fetch_requires_confirmation_before_clicking(monkeypatch):
    monkeypatch.setattr(admin_api, "_load_config", lambda path: {"output-file": "results.csv"})

    try:
        admin_api.run_fetch(
            ["https://offers.greatclips.com/example"],
            click_selector="button.print-coupon",
            confirm_reveal=False,
        )
    except ValueError as exc:
        assert "Confirm the reveal action" in str(exc)
    else:
        raise AssertionError("Expected a confirmation error")


def test_run_fetch_upserts_revealed_rows(monkeypatch):
    written_rows: list[dict[str, object]] = []
    inserted_rows: list[dict[str, object]] = []
    monkeypatch.setattr(admin_api, "_load_config", lambda path: {"output-file": "results.csv"})
    monkeypatch.setattr(
        admin_api,
        "_build_rows_for_url",
        lambda *args: (
            [
                {
                    "url": "https://offers.greatclips.com/example",
                    "code": "SAVE20",
                    "price": "$9.99",
                    "address_line1": "",
                    "address_line2": "",
                    "city": "Ft. Wayne",
                    "state": "",
                }
            ],
            {"url": "https://offers.greatclips.com/example", "ok": True, "codes_found": 1, "rows_written": 1, "offers": []},
        ),
    )
    monkeypatch.setattr(admin_api, "_write_csv", lambda path, rows: written_rows.extend(rows))
    monkeypatch.setattr(admin_api, "insert_coupon_rows", lambda rows: inserted_rows.extend(rows) or len(rows))

    result = admin_api.run_fetch(
        ["https://offers.greatclips.com/example"],
        click_selector="button.print-coupon",
        confirm_reveal=True,
    )

    assert written_rows == inserted_rows
    assert result["database"]["records_inserted"] == 1
    assert result["offers"] == [
        {
            "coupon": "SAVE20",
            "price": "$9.99",
            "address_line1": "",
            "address_line2": "",
            "city": "Ft. Wayne",
            "state": "",
        }
    ]

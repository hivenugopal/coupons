from couponfinder.extractor import clean_text, extract_coupon_codes, extract_offer_details


def test_finds_code_after_keyword():
    html = "<html><body><p>Use code SAVE20 at checkout for 20% off.</p></body></html>"
    results = extract_coupon_codes(html, url="https://example.com")
    codes = [r.code for r in results]
    assert "SAVE20" in codes


def test_finds_code_in_data_attribute():
    html = '<div class="coupon-box" data-code="WELCOME15">Welcome offer</div>'
    results = extract_coupon_codes(html, url="https://example.com")
    codes = [r.code for r in results]
    assert "WELCOME15" in codes
    assert results[0].confidence == "high"


def test_ignores_plain_text_without_code_pattern():
    html = "<p>Thanks for visiting our store, enjoy your day!</p>"
    results = extract_coupon_codes(html, url="https://example.com")
    assert results == []


def test_offer_ended_banner_returns_no_codes():
    html = (
        "<html><body><p>We\u2019re sorry! This offer has ended.</p>"
        '<div class="coupon-box" data-code="WELCOME15">Welcome offer</div></body></html>'
    )
    results = extract_coupon_codes(html, url="https://example.com")
    assert results == []


def test_hidden_offer_ended_banner_does_not_block_codes():
    # Offer pages commonly pre-render every outcome banner and hide all but the
    # active one via inline display:none; a hidden banner must not suppress codes.
    html = (
        '<html><body><div style="display:none">We\u2019re sorry! This offer has ended.</div>'
        '<div class="coupon-box" data-code="WELCOME15">Welcome offer</div></body></html>'
    )
    results = extract_coupon_codes(html, url="https://example.com")
    codes = [r.code for r in results]
    assert "WELCOME15" in codes


def test_clean_text_strips_scripts_styles_and_tags():
    html = """
    <html><head><style>body { color: red; }</style></head>
    <body>
    <script>var trackingId = 42;</script>
    <p>Hello <strong>World</strong></p>
    </body></html>
    """
    text = clean_text(html)
    assert "Hello" in text
    assert "World" in text
    assert "color: red" not in text
    assert "trackingId" not in text


def test_finds_code_inside_bracket_segment():
    html = """
    <html><body>
    <p>Description</p>
    <p>&lt;Get a great haircut for $9.99&gt; at Great Clips Eagle Eye Plaza at 4840 Asbury Rd in Dubuque.
    To redeem the offer now, click &quot;Redeem Now&quot;.</p>
    <p>Terms and Conditions</p>
    <p>&lt;Valid at Great Clips Eagle Eye Plaza at 4840 Asbury Rd in Dubuque, IA&gt;. Not valid with any
    other offer. Limit one coupon per customer. No copies. Taxes may apply. &lt;Expires 10/09/2026&gt;.</p>
    <p>All Great Clips salons are independently owned and operated.</p>
    <p>&lt;2MXK6M
    Offer expires 10/09/2026&gt;</p>
    </body></html>
    """
    results = extract_coupon_codes(html, url="https://example.com")
    codes = {r.code: r for r in results}
    assert "2MXK6M" in codes
    assert codes["2MXK6M"].confidence == "high"
    assert codes["2MXK6M"].source == "bracket_segment"
    # Dates and plain description words inside other bracketed segments must not match.
    assert "2026" not in codes
    assert "9" not in codes


def test_extract_offer_details_finds_price_expires_and_location():
    html = """
    <html><body>
    <p>Get a great haircut for $9.99 at Great Clips Eagle Eye Plaza at 4840 Asbury Rd in Dubuque.</p>
    <p>Valid at Great Clips Eagle Eye Plaza at 4840 Asbury Rd in Dubuque, IA. Not valid with any other
    offer. Limit one coupon per customer. No copies. Taxes may apply. Expires 10/09/2026.</p>
    </body></html>
    """
    details = extract_offer_details(html, url="https://example.com")[0]
    assert details.price == "$9.99"
    assert details.expires == "10/09/2026"
    assert details.location == "Great Clips Eagle Eye Plaza at 4840 Asbury Rd in Dubuque, IA"


def test_extract_offer_details_finds_percentage_off_price():
    html = "<p>Get a great haircut for 50% off at participating Tulsa area Great Clips salons.</p>"
    details = extract_offer_details(html, url="https://example.com")[0]
    assert details.price == "50% off"


def test_extract_offer_details_finds_dollar_off_price():
    html = "<p>Get a great haircut for $7.00 off at participating Tulsa area Great Clips salons.</p>"
    details = extract_offer_details(html, url="https://example.com")[0]
    assert details.price == "$7.00 off"


def test_extract_offer_details_handles_missing_fields():
    html = "<p>Thanks for visiting our store, enjoy your day!</p>"
    details = extract_offer_details(html, url="https://example.com")[0]
    assert details.price is None
    assert details.expires is None
    assert details.location is None


def test_extract_offer_details_strips_generic_valid_only_at_prefix():
    html = "<p>Valid only at participating Tulsa area Great Clips salons.</p>"
    details = extract_offer_details(html, url="https://example.com")[0]
    assert details.location == "participating Tulsa area Great Clips salons"


def test_extract_offer_details_splits_street_address_location():
    html = "<p>Valid at Great Clips Eagle Eye Plaza at 4840 Asbury Rd in Dubuque, IA.</p>"
    details = extract_offer_details(html, url="https://example.com")[0]
    assert details.store_name == "Great Clips"
    assert details.address_line1 == "Eagle Eye Plaza"
    assert details.address_line2 == "4840 Asbury Rd"
    assert details.city == "Dubuque"
    assert details.state == "IA"


def test_extract_offer_details_splits_generic_area_location():
    html = "<p>Valid only at participating Cincinnati area Great Clips salons.</p>"
    details = extract_offer_details(html, url="https://example.com")[0]
    assert details.store_name == "Great Clips"
    assert details.address_line1 is None
    assert details.address_line2 is None
    assert details.city == "Cincinnati"
    assert details.state is None


def test_extract_offer_details_keeps_abbreviated_city_names():
    html = (
        "<p>Get a great student haircut for $9.99 only at participating Ft. Wayne area "
        "Great Clips salons.</p>"
        "<p>Valid only at participating Ft. Wayne area Great Clips salons. Not valid with "
        "any other offer. Offer expires 08/28/2026.</p>"
    )
    details = extract_offer_details(html, url="https://offers.greatclips.com/OloluXg")[0]
    assert details.location == "participating Ft. Wayne area Great Clips salons"
    assert details.city == "Ft. Wayne"
    assert details.store_name == "Great Clips"
    assert details.price == "$9.99"


def test_extract_offer_details_splits_multi_city_location_into_separate_entries():
    html = "<p>Valid only at participating Shreveport & Marshall area Great Clips salons.</p>"
    details_list = extract_offer_details(html, url="https://example.com")
    assert len(details_list) == 2

    cities = [d.city for d in details_list]
    assert cities == ["Shreveport", "Marshall"]
    for d in details_list:
        assert d.store_name == "Great Clips"
        assert d.address_line1 is None
        assert d.address_line2 is None
        assert d.state is None
        assert d.location == "participating Shreveport & Marshall area Great Clips salons"

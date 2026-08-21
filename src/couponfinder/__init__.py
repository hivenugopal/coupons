"""couponfinder: crawl web pages and detect coupon-code naming patterns."""

from __future__ import annotations

from .crawler import FetchError, fetch_html, fetch_many, fetch_rendered_html
from .extractor import clean_text, extract_coupon_codes, extract_offer_details
from .models import CouponCode, OfferDetails

__all__ = [
    "CouponCode",
    "FetchError",
    "OfferDetails",
    "clean_text",
    "extract_coupon_codes",
    "extract_offer_details",
    "fetch_html",
    "fetch_many",
    "fetch_rendered_html",
    "find_coupon_codes",
]


def find_coupon_codes(
    url: str,
    timeout: float = 10.0,
    render: bool = False,
    wait_selector: str | None = None,
    click_selector: str | None = None,
) -> list[CouponCode]:
    """Crawl a single URL and return the coupon codes found on that page.

    Set render=True (or pass wait_selector/click_selector) for pages that inject the code via
    JavaScript after load. click_selector clicks a reveal button before capturing the page —
    on real offer sites that may perform an irreversible one-time redemption, so only pass it
    when you intend that (requires the 'render' extra; see fetch_rendered_html).
    """
    if render or wait_selector or click_selector:
        html = fetch_rendered_html(url, timeout=timeout, wait_selector=wait_selector, click_selector=click_selector)
    else:
        html = fetch_html(url, timeout=timeout)
    return extract_coupon_codes(html, url=url)

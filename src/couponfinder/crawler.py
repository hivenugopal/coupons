"""Fetch raw HTML for one or more URLs."""

import logging
from typing import Dict, Iterable, Optional

import requests

from .patterns import OFFER_ENDED_PATTERN

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; CouponFinderBot/1.0; "
        "+https://github.com/) requests"
    )
}


class FetchError(RuntimeError):
    """Raised when a URL could not be fetched."""


def fetch_html(url: str, timeout: float = 10.0) -> str:
    """Fetch the raw HTML content for a single URL."""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Failed to fetch {url}: {exc}") from exc
    return response.text


def fetch_many(urls: Iterable[str], timeout: float = 10.0) -> Dict[str, str]:
    """Fetch HTML for multiple URLs, logging and skipping any that fail."""
    pages: Dict[str, str] = {}
    for url in urls:
        try:
            pages[url] = fetch_html(url, timeout=timeout)
        except FetchError as exc:
            logger.warning(str(exc))
    return pages


def fetch_rendered_html(
    url: str,
    timeout: float = 15.0,
    wait_selector: Optional[str] = None,
    click_selector: Optional[str] = None,
) -> str:
    """Fetch a page's HTML after letting its JavaScript run (for client-rendered offer pages).

    Requires the optional 'render' extra: pip install -e ".[render]" && playwright install chromium

    By default this only loads the page passively (no clicks). Pass click_selector to click a
    button/link that reveals the code (e.g. "Redeem Now"/"Print Coupon") before capturing the
    HTML — be aware that action may be irreversible on the real site (one-time redemption,
    marking the offer used, etc.), so only set it when you intend that to happen.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise FetchError(
            "Rendering requires the 'render' extra. Install with: "
            'pip install -e ".[render]" && playwright install chromium'
        ) from exc

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(user_agent=DEFAULT_HEADERS["User-Agent"])
                page.goto(url, timeout=timeout * 1000, wait_until="networkidle")

                if OFFER_ENDED_PATTERN.search(page.inner_text("body")):
                    logger.info("Offer has ended for %s; skipping click/wait actions", url)
                    return page.content()

                if click_selector:
                    page.click(click_selector, timeout=timeout * 1000)
                    page.wait_for_load_state("networkidle", timeout=timeout * 1000)
                if wait_selector:
                    page.wait_for_selector(wait_selector, timeout=timeout * 1000)
                return page.content()
            finally:
                browser.close()
    except Exception as exc:
        raise FetchError(f"Failed to render {url}: {exc}") from exc

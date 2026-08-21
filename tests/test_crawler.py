import sys
import types

import pytest

from couponfinder.crawler import fetch_rendered_html


class _FakePage:
    def __init__(self, body_text, html):
        self._body_text = body_text
        self._html = html
        self.clicked = False
        self.waited_for_selector = False

    def goto(self, url, timeout=None, wait_until=None):
        pass

    def inner_text(self, selector):
        return self._body_text

    def click(self, selector, timeout=None):
        self.clicked = True

    def wait_for_load_state(self, state, timeout=None):
        pass

    def wait_for_selector(self, selector, timeout=None):
        self.waited_for_selector = True

    def content(self):
        return self._html


class _FakeBrowser:
    def __init__(self, page):
        self._page = page
        self.closed = False

    def new_page(self, user_agent=None):
        return self._page

    def close(self):
        self.closed = True


class _FakeChromium:
    def __init__(self, browser):
        self._browser = browser

    def launch(self):
        return self._browser


class _FakeSyncPlaywright:
    def __init__(self, browser):
        self._browser = browser

    def __enter__(self):
        return types.SimpleNamespace(chromium=_FakeChromium(self._browser))

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


@pytest.fixture
def fake_playwright(monkeypatch):
    def _install(body_text, html):
        page = _FakePage(body_text, html)
        browser = _FakeBrowser(page)

        fake_sync_api = types.ModuleType("playwright.sync_api")
        fake_sync_api.sync_playwright = lambda: _FakeSyncPlaywright(browser)
        fake_playwright_pkg = types.ModuleType("playwright")
        fake_playwright_pkg.sync_api = fake_sync_api

        monkeypatch.setitem(sys.modules, "playwright", fake_playwright_pkg)
        monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_sync_api)
        return page

    return _install


def test_offer_ended_banner_skips_click_and_wait(fake_playwright):
    page = fake_playwright("We're sorry! This offer has ended.", "<html>ended</html>")

    html = fetch_rendered_html(
        "https://example.com",
        wait_selector="#credential-code",
        click_selector="#redemption",
    )

    assert html == "<html>ended</html>"
    assert page.clicked is False
    assert page.waited_for_selector is False


def test_normal_offer_performs_click_and_wait(fake_playwright):
    page = fake_playwright("20% off your next visit", "<html>ok</html>")

    html = fetch_rendered_html(
        "https://example.com",
        wait_selector="#credential-code",
        click_selector="#redemption",
    )

    assert html == "<html>ok</html>"
    assert page.clicked is True
    assert page.waited_for_selector is True

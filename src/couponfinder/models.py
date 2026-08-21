"""Data models for coupon codes and offer metadata found on a page."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CouponCode:
    """A coupon code candidate discovered while scanning a page."""

    code: str
    url: str
    confidence: str  # "high", "medium", or "low"
    source: str  # e.g. "html_attribute", "context_keyword", "standalone"
    context: str = ""

    def __str__(self) -> str:
        return f"{self.code} [{self.confidence}] ({self.source})"


@dataclass
class OfferDetails:
    """Page-level offer metadata: price, expiration date, and valid location."""

    url: str
    price: Optional[str] = None
    expires: Optional[str] = None
    location: Optional[str] = None
    store_name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

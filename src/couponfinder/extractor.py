"""Extract candidate coupon codes from an HTML page."""

from typing import Dict, List, Tuple

from bs4 import BeautifulSoup

from .models import CouponCode, OfferDetails
from .patterns import (
    ATTRIBUTE_KEYWORDS,
    BRACKET_SEGMENT_PATTERN,
    CONTEXT_CODE_PATTERN,
    EXPIRES_PATTERN,
    KNOWN_STORE_NAMES,
    LOCATION_ADDRESS_PATTERN,
    LOCATION_AREA_PATTERN,
    LOCATION_PATTERN,
    OFFER_ENDED_PATTERN,
    PRICE_PATTERN,
    STANDALONE_CODE_PATTERN,
    US_STATE_ABBREVIATIONS,
    find_state,
    looks_like_code,
    split_multi_values,
)

_CONFIDENCE_RANK = {"high": 2, "medium": 1, "low": 0}


def _confidence_rank(confidence: str) -> int:
    return _CONFIDENCE_RANK.get(confidence, 0)


def clean_text(html: str) -> str:
    """Strip script/style tags and return the page's visible text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ")


def _from_attributes(html: str, url: str) -> List[CouponCode]:
    """Look for elements whose class/id/data-* attributes mark them as coupon-related."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for tag in soup.find_all(True):
        class_attr = tag.get("class")
        haystacks = [
            " ".join(class_attr) if class_attr else "",
            tag.get("id", ""),
        ]
        combined = " ".join(haystacks).lower()
        if not any(keyword in combined for keyword in ATTRIBUTE_KEYWORDS):
            continue

        candidate = tag.get("data-code") or tag.get("data-coupon") or tag.get_text(strip=True)
        candidate = (candidate or "").strip()
        if candidate and len(candidate) <= 20 and " " not in candidate:
            results.append(
                CouponCode(
                    code=candidate.upper(),
                    url=url,
                    confidence="high",
                    source="html_attribute",
                    context=str(tag)[:120],
                )
            )
    return results


def _from_bracket_segments(text: str, url: str) -> List[CouponCode]:
    """Look for codes inside segments explicitly delimited by literal < > markers.

    Sites sometimes wrap the meaningful highlights of an offer (description,
    terms, and the code itself) in "<...>" markers. The code is picked out by
    scanning only inside those segments for a token that mixes letters and
    digits, which reliably separates it from surrounding prose and dates.
    """
    results = []
    for bracket_match in BRACKET_SEGMENT_PATTERN.finditer(text):
        segment = bracket_match.group(1)
        for token_match in STANDALONE_CODE_PATTERN.finditer(segment):
            token = token_match.group(0)
            if looks_like_code(token):
                results.append(
                    CouponCode(
                        code=token,
                        url=url,
                        confidence="high",
                        source="bracket_segment",
                        context=segment.strip(),
                    )
                )
    return results


def _from_context(text: str, url: str) -> List[CouponCode]:
    """Look for codes mentioned right after a coupon-related keyword."""
    results = []
    for match in CONTEXT_CODE_PATTERN.finditer(text):
        code = match.group(1)
        if looks_like_code(code):
            start, end = max(match.start() - 30, 0), min(match.end() + 10, len(text))
            results.append(
                CouponCode(
                    code=code,
                    url=url,
                    confidence="high",
                    source="context_keyword",
                    context=text[start:end].strip(),
                )
            )
    return results


def _from_standalone(text: str, url: str) -> List[CouponCode]:
    """Look for bare tokens that have the shape of a coupon code, without any keyword context."""
    results = []
    for match in STANDALONE_CODE_PATTERN.finditer(text):
        code = match.group(0)
        if looks_like_code(code):
            results.append(
                CouponCode(code=code, url=url, confidence="low", source="standalone")
            )
    return results


_HIDDEN_STYLE_KEYWORDS = ("display:none", "visibility:hidden")


def _is_offer_ended(html: str) -> bool:
    """Return True only if an "offer has ended" banner is actually visible in the markup.

    Offer pages commonly embed every possible outcome banner (ended, expired, not yet
    active, etc.) in the DOM and hide all but the applicable one with inline
    display:none/visibility:hidden/[hidden], so a blind text search would treat every
    page as ended. Only count it when the banner (or none of its ancestors) is hidden.
    """
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.find_all(string=OFFER_ENDED_PATTERN):
        element = node.parent
        hidden = False
        while element is not None:
            style = (element.get("style") or "").replace(" ", "").lower()
            if any(keyword in style for keyword in _HIDDEN_STYLE_KEYWORDS) or element.has_attr("hidden"):
                hidden = True
                break
            element = element.parent
        if not hidden:
            return True
    return False


def extract_coupon_codes(html: str, url: str = "") -> List[CouponCode]:
    """Find and rank candidate coupon codes within an HTML page."""
    text = clean_text(html)
    if _is_offer_ended(html):
        return []

    found: Dict[str, CouponCode] = {}

    all_candidates = [
        *_from_attributes(html, url),
        *_from_bracket_segments(text, url),
        *_from_context(text, url),
        *_from_standalone(text, url),
    ]
    for candidate in all_candidates:
        existing = found.get(candidate.code)
        if existing is None or _confidence_rank(candidate.confidence) > _confidence_rank(existing.confidence):
            found[candidate.code] = candidate

    return sorted(found.values(), key=lambda r: (-_confidence_rank(r.confidence), r.code))


def _split_store_prefix(prefix: str) -> Tuple[str, str]:
    """Split a store name off the front of a location prefix, e.g. "Great Clips Eagle Eye Plaza"."""
    prefix = prefix.strip()
    for name in KNOWN_STORE_NAMES:
        if prefix.lower() == name.lower():
            return name, ""
        if prefix.lower().startswith(name.lower() + " "):
            return name, prefix[len(name):].strip()
    return "", prefix


def _expand_multi_location(base: Dict[str, str], city_raw: str, state_raw: str) -> List[Dict[str, str]]:
    """Pair up cities/states into one entry each when a location mentions more than one, e.g.
    "Shreveport & Marshall" yields two entries with all other fields identical.
    """
    cities = split_multi_values(city_raw) or [""]
    states = [
        state.upper() if state.upper() in US_STATE_ABBREVIATIONS else state
        for state in (split_multi_values(state_raw) or [""])
    ]

    if len(cities) > 1 and len(cities) == len(states):
        pairs = list(zip(cities, states))
    elif len(cities) > 1:
        pairs = [(city, states[0]) for city in cities]
    elif len(states) > 1:
        pairs = [(cities[0], state) for state in states]
    else:
        pairs = [(cities[0], states[0])]

    return [{**base, "city": city, "state": state} for city, state in pairs]


def _parse_location(location: str) -> List[Dict[str, str]]:
    """Split a free-form location string into one or more store/address/city/state entries."""
    location = location.strip()

    match = LOCATION_ADDRESS_PATTERN.match(location)
    if match:
        store_name, remainder = _split_store_prefix(match.group("prefix"))
        address2 = match.group("address2").strip()
        if remainder:
            address_line1, address_line2 = remainder, address2
        else:
            address_line1, address_line2 = address2, ""
        state = match.group("state").strip()
        base = {
            "store_name": store_name,
            "address_line1": address_line1,
            "address_line2": address_line2,
        }
        return _expand_multi_location(base, match.group("city"), state)

    match = LOCATION_AREA_PATTERN.search(location)
    if match:
        store_name, _ = _split_store_prefix(match.group("store").strip())
        base = {
            "store_name": store_name or match.group("store").strip(),
            "address_line1": "",
            "address_line2": "",
        }
        return _expand_multi_location(base, match.group("city"), find_state(location))

    # No recognizable structure: just pull out a known store name if present.
    store_name, remainder = _split_store_prefix(location)
    return [
        {
            "store_name": store_name,
            "address_line1": remainder,
            "address_line2": "",
            "city": "",
            "state": find_state(location),
        }
    ]


def extract_offer_details(html: str, url: str = "") -> List[OfferDetails]:
    """Pull the offer's price, expiration date, and valid location(s) out of the page text.

    A location mentioning multiple cities or states (e.g. "Shreveport & Marshall area ... salons")
    yields one OfferDetails entry per city/state, with all other fields identical.
    """
    text = " ".join(clean_text(html).split())

    price_match = PRICE_PATTERN.search(text)
    expires_match = EXPIRES_PATTERN.search(text)
    location_match = LOCATION_PATTERN.search(text)
    location = location_match.group(1).strip().strip("<>").strip() if location_match else None
    location_parts_list = _parse_location(location) if location else [{}]

    return [
        OfferDetails(
            url=url,
            price=price_match.group(0) if price_match else None,
            expires=expires_match.group(1) if expires_match else None,
            location=location,
            store_name=parts.get("store_name") or None,
            address_line1=parts.get("address_line1") or None,
            address_line2=parts.get("address_line2") or None,
            city=parts.get("city") or None,
            state=parts.get("state") or None,
        )
        for parts in location_parts_list
    ]

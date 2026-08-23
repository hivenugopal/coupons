"""Regex patterns and keyword lists used to recognize coupon-code naming conventions."""

import re
from typing import List

# Phrases that typically precede a coupon code in page copy.
_CONTEXT_KEYWORDS = (
    r"coupon\s*code|promo\s*code|promotional\s*code|discount\s*code|"
    r"voucher\s*code|use\s*code|enter\s*code|apply\s*code|redeem\s*code|code"
)

# Matches "<keyword> [is/:/-] CODE" so the code can be pulled out of a capture group.
CONTEXT_CODE_PATTERN = re.compile(
    rf"(?:{_CONTEXT_KEYWORDS})\s*(?:is|:|-)?\s*[\"'`]?\b([A-Za-z0-9][A-Za-z0-9\-]{{3,19}})\b",
    re.IGNORECASE,
)

# Bare uppercase/digit tokens found anywhere in the page text (low confidence alone).
STANDALONE_CODE_PATTERN = re.compile(r"\b[A-Z0-9][A-Z0-9\-]{3,14}\b")

# Text wrapped in literal < > markers, e.g. "<2MXK6M Offer expires ...>".
# Non-greedy/no-nesting so adjacent bracketed segments aren't merged into one match.
BRACKET_SEGMENT_PATTERN = re.compile(r"<([^<>]+)>", re.DOTALL)

# HTML class/id/data-attribute fragments that flag an element as coupon-related.
ATTRIBUTE_KEYWORDS = (
    "coupon",
    "promo",
    "voucher",
    "discount-code",
    "code-box",
    "credential-code",
    "code",
)

# Offer metadata found alongside the code, e.g. "Get a great haircut for $9.99",
# "Get a great haircut for $7.00 off", or "Get a great haircut for 50% off".
PRICE_PATTERN = re.compile(r"\$\s?\d+(?:\.\d{1,2})?(?:\s*off)?|\d+%\s*off", re.IGNORECASE)

# e.g. "Offer expires 10/09/2026" or "Expires 10/09/2026".
EXPIRES_PATTERN = re.compile(r"expires\s+(\d{1,2}/\d{1,2}/\d{2,4})", re.IGNORECASE)

# e.g. "Valid at Great Clips Eagle Eye Plaza at 4840 Asbury Rd in Dubuque, IA." or
# "Valid only at participating Ft. Wayne area Great Clips salons."
# Stop at a sentence-ending period, but not after abbreviations such as Ft. / St. / Ave.
LOCATION_PATTERN = re.compile(
    r"valid\s+(?:only\s+)?at\s+(.+?(?:salons?|,\s*[A-Za-z]{2}(?:\s*(?:&|/|,|\band\b)\s*[A-Za-z]{2})*))"
    r"(?=\s*\.|$)",
    re.IGNORECASE,
)

# Shown instead of a redeemable code/credential once a deal is no longer active.
OFFER_ENDED_PATTERN = re.compile(r"we[\u2019']re sorry!?\s*this offer has ended\.?", re.IGNORECASE)

# Store chains recognized as a prefix of the location text, e.g. "Great Clips Eagle Eye Plaza ...".
KNOWN_STORE_NAMES = ("Great Clips",)

# e.g. "Great Clips Eagle Eye Plaza at 4840 Asbury Rd in Dubuque, IA" -> prefix/address2/city/state.
# City and state may each list more than one value, e.g. "in Dubuque & Asbury, IA & IL".
LOCATION_ADDRESS_PATTERN = re.compile(
    r"^(?P<prefix>.+?)\s+at\s+(?P<address2>.+?)\s+in\s+(?P<city>[^,]+),\s*"
    r"(?P<state>[A-Za-z]{2,}(?:\s*(?:&|/|,|\band\b)\s*[A-Za-z]{2,})*)$",
    re.IGNORECASE,
)

# e.g. "participating Cincinnati area Great Clips salons" -> city/store, no street address.
# The city portion may list more than one city, e.g. "Shreveport & Marshall area ... salons",
# and may include abbreviations such as "Ft. Wayne".
LOCATION_AREA_PATTERN = re.compile(
    r"(?:participating\s+)?(?P<city>[A-Za-z][A-Za-z.\s&,/]*?)\s+area\s+(?P<store>.+?)\s+salons?\b",
    re.IGNORECASE,
)

# Separators used when a location mentions more than one city or state, e.g. "Shreveport & Marshall".
MULTI_VALUE_SPLIT_PATTERN = re.compile(r"\s*(?:&|/|,|\band\b)\s*", re.IGNORECASE)


def split_multi_values(text: str) -> List[str]:
    """Split a string like "Shreveport & Marshall" into ["Shreveport", "Marshall"]."""
    return [part.strip() for part in MULTI_VALUE_SPLIT_PATTERN.split(text.strip()) if part.strip()]

US_STATE_ABBREVIATIONS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}

US_STATE_NAMES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC",
}

# Matches a full state name anywhere in the text, longest names first to avoid partial overlaps.
_STATE_NAME_PATTERN = re.compile(
    r"\b(" + "|".join(sorted((re.escape(name) for name in US_STATE_NAMES), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_STATE_NAMES_LOWER = {name.lower(): abbr for name, abbr in US_STATE_NAMES.items()}

# A 2-letter state abbreviation only counts when it follows a comma, e.g. ", IA", to avoid
# matching common words that happen to be valid abbreviations (e.g. "in", "or").
_STATE_ABBR_AFTER_COMMA_PATTERN = re.compile(r",\s*([A-Za-z]{2})\b")


def find_state(text: str) -> str:
    """Return the US state abbreviation found in free-form text, or "" if none is present."""
    abbr_match = _STATE_ABBR_AFTER_COMMA_PATTERN.search(text)
    if abbr_match and abbr_match.group(1).upper() in US_STATE_ABBREVIATIONS:
        return abbr_match.group(1).upper()
    name_match = _STATE_NAME_PATTERN.search(text)
    if name_match:
        return _STATE_NAMES_LOWER[name_match.group(1).lower()]
    return ""


def looks_like_code(token: str) -> bool:
    """Return True if a token has the shape of a real coupon code (not just a keyword match)."""
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9\-]{3,19}", token):
        return False
    # Require a mix of letters and digits so plain words and bare numbers/dates are excluded.
    return any(c.isdigit() for c in token) and any(c.isalpha() for c in token)

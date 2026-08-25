"""Validation helpers for public coupon click records."""

from __future__ import annotations

import re
from typing import Any

_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
_EMAIL_ERROR = "Enter a valid email address, such as name@gmail.com."


def validate_email(email: Any) -> str:
    """Normalize and accept emails that match the public claim regex."""
    if not isinstance(email, str):
        raise ValueError(_EMAIL_ERROR)

    cleaned = email.strip()
    if not _EMAIL_PATTERN.fullmatch(cleaned):
        raise ValueError(_EMAIL_ERROR)
    return cleaned.lower()


def validate_claim_payload(payload: Any) -> tuple[int, str]:
    """Return a validated offer ID and normalized email from a request payload."""
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    offer_id = payload.get("offer_id")
    if isinstance(offer_id, bool):
        raise ValueError("offer_id must be a positive integer.")
    try:
        offer_id = int(offer_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("offer_id must be a positive integer.") from exc
    if offer_id <= 0:
        raise ValueError("offer_id must be a positive integer.")

    return offer_id, validate_email(payload.get("email"))

"""Validation helpers for public coupon click records."""

from __future__ import annotations

import re
from typing import Any

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_EMAIL_LENGTH = 254


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

    email = payload.get("email")
    if not isinstance(email, str):
        raise ValueError("email must be a valid email address.")
    email = email.strip().lower()
    if len(email) > _MAX_EMAIL_LENGTH or not _EMAIL_PATTERN.fullmatch(email):
        raise ValueError("email must be a valid email address.")
    return offer_id, email

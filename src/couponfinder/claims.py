"""Validation helpers for public coupon click records."""

from __future__ import annotations

import re
from typing import Any

_MAX_EMAIL_LENGTH = 254
_MAX_LOCAL_LENGTH = 64
_EMAIL_SHAPE = re.compile(
    r"^[a-z0-9](?:[a-z0-9._%+-]{0,62}[a-z0-9])?@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$",
)
_TLD_PATTERN = re.compile(r"^[a-z]{2,24}$")
_LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_RESERVED_DOMAINS = frozenset(
    {
        "example.com",
        "example.net",
        "example.org",
        "example.edu",
        "invalid",
        "localhost",
        "local",
        "test",
    }
)
_PLACEHOLDER_LOCAL_PARTS = frozenset(
    {
        "abc",
        "asdf",
        "email",
        "fake",
        "foo",
        "test",
        "testing",
        "username",
    }
)
_EMAIL_ERROR = "Enter a valid email address, such as name@gmail.com."


def validate_email(email: Any) -> str:
    """Normalize and accept only realistically formed personal email addresses."""
    if not isinstance(email, str):
        raise ValueError(_EMAIL_ERROR)

    cleaned = email.strip().lower()
    if not cleaned or len(cleaned) > _MAX_EMAIL_LENGTH or ".." in cleaned:
        raise ValueError(_EMAIL_ERROR)
    if not _EMAIL_SHAPE.fullmatch(cleaned):
        raise ValueError(_EMAIL_ERROR)

    local, _, domain = cleaned.partition("@")
    labels = domain.split(".")
    if (
        not local
        or len(local) > _MAX_LOCAL_LENGTH
        or local.startswith(".")
        or local.endswith(".")
        or len(labels) < 2
        or any(not _LABEL_PATTERN.fullmatch(label) for label in labels)
        or not _TLD_PATTERN.fullmatch(labels[-1])
        or labels[-1] == labels[-2]
        or domain in _RESERVED_DOMAINS
        or labels[-1] in _RESERVED_DOMAINS
        or local in _PLACEHOLDER_LOCAL_PARTS
    ):
        raise ValueError(_EMAIL_ERROR)
    return cleaned


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

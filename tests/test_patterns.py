from couponfinder.patterns import CONTEXT_CODE_PATTERN, looks_like_code


def test_context_pattern_matches_common_phrasing():
    text = "Enter promo code FALL2024 during checkout."
    match = CONTEXT_CODE_PATTERN.search(text)
    assert match is not None
    assert match.group(1) == "FALL2024"


def test_looks_like_code_requires_a_digit():
    assert looks_like_code("SAVE20") is True
    assert looks_like_code("HELLO") is False


def test_looks_like_code_rejects_too_short_tokens():
    assert looks_like_code("A1") is False

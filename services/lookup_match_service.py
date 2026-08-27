from __future__ import annotations

from difflib import SequenceMatcher


def normalize_name(value: str) -> str:
    return " ".join(value.split()).strip()


def names_match(expected: str, actual: str, threshold: float = 0.85) -> bool:
    expected_norm = normalize_name(expected)
    actual_norm = normalize_name(actual)
    if not expected_norm or not actual_norm:
        return False
    if expected_norm in actual_norm or actual_norm in expected_norm:
        return True
    return SequenceMatcher(None, expected_norm, actual_norm).ratio() >= threshold

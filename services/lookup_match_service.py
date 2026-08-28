from __future__ import annotations

from difflib import SequenceMatcher


def normalize_name(value: str) -> str:
    cleaned = (
        value.replace(".", "")
        .replace(",", "")
        .replace("·", "")
        .replace(" ", "")
    )
    return cleaned.strip()


def thai_only(value: str) -> str:
    return "".join(ch for ch in value if "\u0E00" <= ch <= "\u0E7F")


def last_token(value: str) -> str:
    parts = value.split()
    if not parts:
        return normalize_name(value)
    return normalize_name(parts[-1])


def name_similarity(expected: str, actual: str) -> float:
    expected_norm = normalize_name(expected)
    actual_norm = normalize_name(actual)
    if not expected_norm or not actual_norm:
        return 0.0
    if expected_norm in actual_norm or actual_norm in expected_norm:
        return 1.0

    full_ratio = SequenceMatcher(None, expected_norm, actual_norm).ratio()
    expected_thai = thai_only(expected_norm)
    actual_thai = thai_only(actual_norm)
    if expected_thai and actual_thai:
        thai_ratio = SequenceMatcher(None, expected_thai, actual_thai).ratio()
        if expected_thai in actual_thai or actual_thai in expected_thai:
            thai_ratio = max(thai_ratio, 0.95)
        return max(full_ratio, thai_ratio)
    return full_ratio


def names_match(expected: str, actual: str, threshold: float = 0.85) -> bool:
    if name_similarity(expected, actual) < threshold:
        return False

    expected_last = last_token(expected)
    actual_last = last_token(actual)
    if len(expected_last) >= 2 and len(actual_last) >= 2:
        tail_ratio = SequenceMatcher(None, expected_last, actual_last).ratio()
        if tail_ratio < 0.95:
            return False

    return True


def names_match_complete(expected: str, actual: str, threshold: float = 0.85) -> bool:
    """ตรงครบ — ไม่ยอมรับแถวที่สั้นกว่า query (เช่น ขาด '1' ท้ายชื่อ)"""
    if not names_match(expected, actual, threshold):
        return False

    expected_norm = normalize_name(expected)
    actual_norm = normalize_name(actual)
    if expected_norm == actual_norm:
        return True

    if len(actual_norm) < len(expected_norm) and expected_norm.startswith(actual_norm):
        return False

    expected_tokens = expected.split()
    actual_tokens = actual.split()
    if len(actual_tokens) < len(expected_tokens):
        return False

    return True

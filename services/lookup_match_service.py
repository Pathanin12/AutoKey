from __future__ import annotations

import unicodedata
from difflib import SequenceMatcher


def tidy_vendor_name(value: str) -> str:
    """ช่องว่างทุกแบบ → ช่องว่างปกติ แล้วตัดซ้ำ (ใช้เทียบชื่อ ไม่ใช่ตอนวาง Express)"""
    text = "".join(" " if unicodedata.category(ch) == "Zs" else ch for ch in (value or ""))
    return " ".join(text.split())


def to_express_vendor_name(value: str) -> str:
    """วางชื่อตาม Excel — ไม่ยุบช่องว่าง ไม่แปลงเป็น NBSP"""
    return (value or "").strip()


def normalize_name(value: str) -> str:
    cleaned = (
        tidy_vendor_name(value)
        .replace(".", "")
        .replace(",", "")
        .replace("·", "")
        .replace(" ", "")
    )
    return cleaned.strip()


def fold_for_ocr(value: str) -> str:
    """ตัดวรรณยุกต์/เครื่องหมาย fore OCR เทียบตัวอักษรหลัก"""
    return "".join(ch for ch in normalize_name(value) if unicodedata.category(ch) != "Mn")


def _levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    prev = list(range(len(right) + 1))
    for i, left_ch in enumerate(left, start=1):
        current = [i]
        for j, right_ch in enumerate(right, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = prev[j] + 1
            replace_cost = prev[j - 1] + (left_ch != right_ch)
            current.append(min(insert_cost, delete_cost, replace_cost))
        prev = current
    return prev[-1]


def _common_prefix_len(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    index = 0
    while index < limit and left[index] == right[index]:
        index += 1
    return index


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
    if not is_plausible_vendor_name(actual):
        return False
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


def is_incomplete_same_vendor(expected: str, actual: str) -> bool:
    """อ่านได้ชื่อจริงที่สั้นกว่า query — ควร Down ไปแถวถัดไป"""
    if not is_plausible_vendor_name(actual):
        return False
    expected_norm = normalize_name(expected)
    actual_norm = normalize_name(actual)
    if not expected_norm or not actual_norm or actual_norm == expected_norm:
        return False
    return expected_norm.startswith(actual_norm) and len(actual_norm) >= 4


def is_ocr_of_expected(expected: str, actual: str) -> bool:
    """ชื่อเดียวกันที่ OCR เพี้ยนแค่ท้ายคำ (เช่น ค้า→ดํา) — ไม่รับบริษัทอื่นที่ย่านคล้าย"""
    left = fold_for_ocr(expected)
    right = fold_for_ocr(actual)
    if not left or not right:
        return False
    if abs(len(left) - len(right)) > 2:
        return False
    distance = _levenshtein(left, right)
    if distance > 2:
        return False
    prefix = _common_prefix_len(left, right)
    return prefix >= max(len(left), len(right)) - 2


def is_plausible_vendor_name(value: str) -> bool:
    """กรอง OCR ขยะ — ต้องมีตัวไทย/ตัวอักษรพอสมควร"""
    text = value.strip()
    if len(text) < 2:
        return False

    noise_chars = sum(1 for ch in text if ch in "[]|#+*\"{}\\")
    if noise_chars >= 1 and (noise_chars >= 2 or text.lstrip().startswith("[")):
        return False

    compact = text.replace(" ", "")
    if not compact:
        return False

    thai_count = sum(1 for ch in compact if "\u0E00" <= ch <= "\u0E7F")
    letter_count = sum(1 for ch in compact if ch.isalpha() or "\u0E00" <= ch <= "\u0E7F")
    if letter_count == 0:
        return False

    if thai_count == 0 and letter_count / len(compact) < 0.5:
        return False

    if thai_count > 0 and thai_count / len(compact) < 0.2:
        return False

    return True


def clipboard_matches_query(clipboard: str, query: str) -> bool:
    clip = clipboard.strip()
    name = query.strip()
    if not clip or not name:
        return False
    if clip == name or name in clip or clip in name:
        return True
    return normalize_name(clip) == normalize_name(name)

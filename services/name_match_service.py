from __future__ import annotations

import unicodedata


_LEGAL_PREFIXES = (
    "ห้างหุ้นส่วนสามัญนิติบุคคล",
    "ห้างหุ้นส่วนสามัญ",
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วน",
    "บริษัทจำกัดมหาชน",
    "บริษัทมหาชนจำกัด",
    "บริษัท",
    "บมจ.",
    "บมจ",
    "บจก.",
    "บจก",
    "หจก.",
    "หจก",
    "หสน.",
    "หสน",
)

_LEGAL_SUFFIXES = (
    "จำกัดมหาชน",
    "จำกัด",
)


def tidy_name(value: str) -> str:
    """ช่องว่างทุกแบบ (รวม NBSP) → ช่องว่างปกติ แล้วตัดซ้ำ"""
    text = unicodedata.normalize("NFC", value or "")
    text = "".join(" " if ch.isspace() else ch for ch in text)
    return " ".join(text.split())


def compact_name(value: str) -> str:
    return (
        tidy_name(value)
        .replace(".", "")
        .replace(",", "")
        .replace("·", "")
        .replace(" ", "")
    )


def core_company_name(value: str) -> str:
    text = tidy_name(value)
    changed = True
    while text and changed:
        changed = False
        for prefix in _LEGAL_PREFIXES:
            if text.startswith(prefix):
                text = tidy_name(text[len(prefix) :].lstrip(" ."))
                changed = True
                break
    for suffix in _LEGAL_SUFFIXES:
        if text.endswith(suffix) and len(text) > len(suffix):
            text = tidy_name(text[: -len(suffix)].rstrip(" ."))
            break
    return text


def names_match(left: str, right: str) -> bool:
    left_tidy = tidy_name(left)
    right_tidy = tidy_name(right)
    if not left_tidy or not right_tidy:
        return False
    if left_tidy == right_tidy:
        return True
    if compact_name(left_tidy) == compact_name(right_tidy):
        return True
    left_core = compact_name(core_company_name(left_tidy))
    right_core = compact_name(core_company_name(right_tidy))
    return bool(left_core) and left_core == right_core

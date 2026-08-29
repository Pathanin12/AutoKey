from __future__ import annotations

import re


_SHEET_PERIOD_PATTERN = re.compile(r"(\d{4})\s+(\d{2})\s*$")


def parse_sheet_period(sheet_name: str) -> tuple[int, int]:
    match = _SHEET_PERIOD_PATTERN.search(sheet_name.strip())
    if not match:
        raise ValueError(f"ไม่สามารถอ่านปี/เดือนจาก Sheet: {sheet_name}")
    return int(match.group(1)), int(match.group(2))


def build_nrg_tax_reference(sheet_name: str, sequence: int) -> str:
    year, month = parse_sheet_period(sheet_name)
    return f"NRG{year}{month:02d}{int(sequence):04d}"


def format_tax_payer_id(value: str) -> str:
    text = value.strip().replace("-", "").replace(" ", "")
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".", 1)[0]
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return ""
    if len(digits) < 13:
        return digits.zfill(13)
    return digits


def resolve_tax_payer_id(row_tax_id: str, ui_fallback: str = "") -> str:
    candidate = row_tax_id.strip() or ui_fallback.strip()
    if not candidate:
        return ""
    return format_tax_payer_id(candidate)

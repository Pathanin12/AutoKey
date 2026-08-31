from __future__ import annotations

import re


_PERIOD_PATTERN = re.compile(r"(\d{4})\s+(\d{2})")


def parse_sheet_period(text: str) -> tuple[int, int]:
    match = _PERIOD_PATTERN.search(text.strip())
    if not match:
        raise ValueError(f"ไม่สามารถอ่านปี/เดือนจาก: {text}")
    return int(match.group(1)), int(match.group(2))


def build_nrg_tax_reference(period_text: str, sequence: int) -> str:
    year, month = parse_sheet_period(period_text)
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


def resolve_tax_payer_id(ui_value: str) -> str:
    candidate = ui_value.strip()
    if not candidate:
        return ""
    return format_tax_payer_id(candidate)

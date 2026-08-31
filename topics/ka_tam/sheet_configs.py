from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SheetColumnMap:
    header_row: int
    subheader_row: int | None
    data_start_row: int
    legal_name: int
    month: int
    tax_id: int
    service_amount: int
    vat_amount: int
    credit_amount: int | None
    wt_amount: int
    invoice_number: int | None = None


_LEGAL_SPECIAL = ("นิติบุคคล (special)", "นิติบุคคล(special)")
_LEGAL = ("นิติบุคคล",)
_MONTH = ("เดือน",)
_TAX_ID = ("tax id", "taxid")
_SERVICE = ("srv",)
_VAT = ("vat",)
_WT = ("wt",)
_INVOICE = ("เลขที่ใบกำกับ",)
_CREDIT = ("ค่าบริการ",)


def _cell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value != value:
        return ""
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    return " ".join(text.lower().split())


def _find_header(headers: list[str], names: tuple[str, ...]) -> int | None:
    for name in names:
        if name in headers:
            return headers.index(name)
    return None


def _is_sequence_cell(value) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and value != value:
        return False
    try:
        int(float(value))
        return True
    except (TypeError, ValueError):
        return False


def detect_column_map(preview_rows: list[tuple]) -> SheetColumnMap:
    """หาคอลัมน์จากหัวตาราง — ไม่ผูกชื่อชีต"""
    best: tuple[int, int, list[str]] | None = None
    for index, raw in enumerate(preview_rows[:8]):
        headers = [_cell_text(value) for value in raw]
        score = 0
        if _find_header(headers, _LEGAL_SPECIAL) is not None or _find_header(headers, _LEGAL) is not None:
            score += 2
        for group in (_SERVICE, _VAT, _WT, _INVOICE, _MONTH, _TAX_ID):
            if _find_header(headers, group) is not None:
                score += 1
        if best is None or score > best[0]:
            best = (score, index, headers)

    if best is None or best[0] < 4:
        raise ValueError("ไม่พบหัวคอลัมน์ นิติบุคคล / srv / vat / wt ในไฟล์ Excel")

    header_row = best[1]
    headers = best[2]
    legal_name = _find_header(headers, _LEGAL_SPECIAL)
    if legal_name is None:
        legal_name = _find_header(headers, _LEGAL)
    service_amount = _find_header(headers, _SERVICE)
    vat_amount = _find_header(headers, _VAT)
    wt_amount = _find_header(headers, _WT)
    missing = [
        label
        for label, index in (
            ("นิติบุคคล", legal_name),
            ("srv", service_amount),
            ("vat", vat_amount),
            ("wt", wt_amount),
        )
        if index is None
    ]
    if missing:
        raise ValueError("ไม่พบคอลัมน์: " + ", ".join(missing))

    month = _find_header(headers, _MONTH)
    tax_id = _find_header(headers, _TAX_ID)
    data_start_row = header_row + 1
    while data_start_row < len(preview_rows) and not _is_sequence_cell(
        preview_rows[data_start_row][0] if preview_rows[data_start_row] else None
    ):
        data_start_row += 1

    return SheetColumnMap(
        header_row=header_row,
        subheader_row=header_row + 1 if data_start_row > header_row + 1 else None,
        data_start_row=data_start_row,
        legal_name=legal_name,
        month=month if month is not None else -1,
        tax_id=tax_id if tax_id is not None else -1,
        service_amount=service_amount,
        vat_amount=vat_amount,
        credit_amount=_find_header(headers, _CREDIT),
        wt_amount=wt_amount,
        invoice_number=_find_header(headers, _INVOICE),
    )

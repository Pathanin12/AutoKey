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


SHEET_COLUMN_MAPS: dict[str, SheetColumnMap] = {
    "NRG srv 2026 03": SheetColumnMap(
        header_row=0,
        subheader_row=1,
        data_start_row=2,
        legal_name=2,
        month=4,
        tax_id=7,
        service_amount=8,
        vat_amount=9,
        credit_amount=None,
        wt_amount=10,
    ),
    "NRG srv 2026 04": SheetColumnMap(
        header_row=0,
        subheader_row=1,
        data_start_row=2,
        legal_name=2,
        month=4,
        tax_id=7,
        service_amount=8,
        vat_amount=9,
        credit_amount=None,
        wt_amount=10,
    ),
    "srv 2026 06": SheetColumnMap(
        header_row=1,
        subheader_row=None,
        data_start_row=2,
        legal_name=2,
        month=4,
        tax_id=5,
        service_amount=7,
        vat_amount=8,
        credit_amount=6,
        wt_amount=9,
        invoice_number=1,
    ),
    "srv 2026 07": SheetColumnMap(
        header_row=1,
        subheader_row=None,
        data_start_row=2,
        legal_name=2,
        month=3,
        tax_id=4,
        service_amount=6,
        vat_amount=7,
        credit_amount=5,
        wt_amount=8,
        invoice_number=1,
    ),
}


def get_sheet_column_map(sheet_name: str) -> SheetColumnMap:
    if sheet_name not in SHEET_COLUMN_MAPS:
        raise ValueError(f"ยังไม่รองรับ Sheet: {sheet_name}")
    return SHEET_COLUMN_MAPS[sheet_name]

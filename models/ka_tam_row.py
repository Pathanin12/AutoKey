from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KaTamRow:
    row_number: int
    sequence: int
    sheet_name: str
    legal_name: str
    service_amount: float
    vat_amount: float
    wt_amount: float
    invoice_number: str = ""
    tax_id: str = ""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KaTamSheetMap:
    header_row: int
    data_start_row: int
    legal_name: int
    service_amount: int
    vat_amount: int
    wt_amount: int
    tax_id: int
    invoice_number: int

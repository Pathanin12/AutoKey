from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WcfSheetMap:
    header_row: int
    data_start_row: int
    shop_name: int
    alt_name: int
    pay_date: int
    contrib_amount: int
    surcharge: int
    paid_amount: int
    year: int
    receipt_no: int
    notice_no: int

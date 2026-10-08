from __future__ import annotations

from dataclasses import dataclass

from services.pp30_amount_service import has_amount


@dataclass(frozen=True)
class WcfRow:
    row_number: int
    shop_name: str
    match_name: str
    pv_date: str
    contrib_amount: float
    surcharge: float
    paid_amount: float
    period: str
    receipt_no: str = ""

    @property
    def has_contrib(self) -> bool:
        return has_amount(self.contrib_amount)

    @property
    def has_surcharge(self) -> bool:
        return has_amount(self.surcharge)

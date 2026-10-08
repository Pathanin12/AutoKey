from __future__ import annotations

from dataclasses import dataclass

from services.pp30_amount_service import has_amount


@dataclass(frozen=True)
class SsoFormValues:
    contrib_amount: float
    surcharge: float
    paid_amount: float
    pv_date: str
    receipt_no: str = ""

    @property
    def has_contrib(self) -> bool:
        return has_amount(self.contrib_amount)

    @property
    def has_surcharge(self) -> bool:
        return has_amount(self.surcharge)

    @property
    def has_paid(self) -> bool:
        return has_amount(self.paid_amount)

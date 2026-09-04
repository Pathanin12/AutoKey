from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pp30FormValues:
    vat_sale: float
    vat_purchase: float
    amount_due: float
    pv_date: str

    @property
    def amount_due_decimal(self) -> float:
        return round(self.amount_due - int(self.amount_due), 2)

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pp30FormValues:
    vat_sale: float
    vat_purchase: float
    amount_due: float
    pv_date: str
    line_8: float = 0.0
    line_9: float = 0.0
    line_10: float = 0.0
    line_12: float = 0.0
    line_13: float = 0.0
    line_14: float = 0.0
    line_15: float = 0.0

    @property
    def line_5(self) -> float:
        return self.vat_sale

    @property
    def line_7(self) -> float:
        return self.vat_purchase

    @property
    def line_11(self) -> float:
        return self.amount_due

    @property
    def amount_due_decimal(self) -> float:
        return round(self.amount_due - int(self.amount_due), 2)

    @property
    def line_15_decimal(self) -> float:
        return round(self.line_15 - int(self.line_15), 2)

    @property
    def penalty_amount(self) -> float:
        return round(self.line_13 + self.line_14, 2)

    @property
    def is_all_zero(self) -> bool:
        return all(
            abs(value) < 0.005
            for value in (
                self.vat_sale,
                self.vat_purchase,
                self.amount_due,
                self.line_8,
                self.line_9,
                self.line_10,
                self.line_12,
                self.line_13,
                self.line_14,
                self.line_15,
            )
        )

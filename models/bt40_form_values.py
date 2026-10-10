from __future__ import annotations

from dataclasses import dataclass

from models.month_year_period import MonthYearPeriod
from services.pp30_amount_service import has_amount


@dataclass(frozen=True)
class Bt40FormValues:
    line7_receipt: float
    line13: float = 0.0
    line14: float = 0.0
    line17: float = 0.0
    pv_date: str = ""
    period: MonthYearPeriod | None = None

    @property
    def penalty_amount(self) -> float:
        return round(self.line13 + self.line14, 2)

    @property
    def tax_amount(self) -> float:
        return round(self.line17 - self.penalty_amount, 2)

    @property
    def line17_integer(self) -> float:
        return float(int(self.line17))

    @property
    def line17_decimal(self) -> float:
        return round(self.line17 - int(self.line17), 2)

    @property
    def has_receipt(self) -> bool:
        return has_amount(self.line7_receipt)

    @property
    def has_tax(self) -> bool:
        return has_amount(self.line17)

    @property
    def has_penalty(self) -> bool:
        return has_amount(self.penalty_amount)

    @property
    def has_decimal(self) -> bool:
        return has_amount(self.line17_decimal)

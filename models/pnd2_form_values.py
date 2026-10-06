from __future__ import annotations

from dataclasses import dataclass

from constants.routes import PND2_DESCRIPTION, PND2_TAX_DESCRIPTION
from models.month_year_period import MonthYearPeriod
from services.pp30_amount_service import has_amount


@dataclass(frozen=True)
class Pnd2FormValues:
    people_count: int
    income_amount: float
    tax_withheld: float
    surcharge: float = 0.0
    pv_date: str = ""
    period: MonthYearPeriod | None = None

    @property
    def description(self) -> str:
        return PND2_DESCRIPTION.format(count=self.people_count)

    @property
    def tax_description(self) -> str:
        period = self.period.text if self.period and self.period.is_valid else ""
        return PND2_TAX_DESCRIPTION.format(period=period)

    @property
    def has_surcharge(self) -> bool:
        return has_amount(self.surcharge)

    @property
    def has_tax(self) -> bool:
        return has_amount(self.tax_withheld)

    @property
    def has_income(self) -> bool:
        return has_amount(self.income_amount)

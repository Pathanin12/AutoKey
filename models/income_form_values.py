from __future__ import annotations

from dataclasses import dataclass

from constants.date_utils import express_month_year_label, is_complete_express_date
from constants.routes import INCOME_RV_TAX


@dataclass(frozen=True)
class IncomeFormValues:
    company_name: str
    branch_last5: str
    invoice_date: str
    invoice_number: str
    tax_id: str
    total_amount: float
    wht_amount: float
    vat_amount: float
    bill_count: int
    kind: str = INCOME_RV_TAX
    period_date: str = ""
    base_amount: float = 0.0
    deposit_amount: float = 0.0

    @property
    def has_total(self) -> bool:
        return (
            abs(self.total_amount) >= 0.005
            or abs(self.base_amount) >= 0.005
            or abs(self.deposit_amount) >= 0.005
        )

    @property
    def month_date(self) -> str:
        return self.invoice_date or self.period_date

    def description_month_year(self, fallback: str) -> tuple[int, str]:
        source = self.period_date if is_complete_express_date(self.period_date) else fallback
        return express_month_year_label(source)

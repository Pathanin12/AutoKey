from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IncomeReportRow:
    shop_name: str
    tax_id: str
    branch: str
    income: float = 0.0
    sale_vat: float = 0.0
    sale_wht: float = 0.0
    royalty: float = 0.0
    buy_vat: float = 0.0
    buy_wht: float = 0.0
    number: int | None = None
    is_total: bool = False

    @property
    def amounts(self) -> tuple[float, float, float, float, float, float]:
        return (self.income, self.sale_vat, self.sale_wht, self.royalty, self.buy_vat, self.buy_wht)

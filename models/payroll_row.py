from __future__ import annotations

from dataclasses import dataclass

from services.pp30_amount_service import has_amount


@dataclass(frozen=True)
class PayrollRow:
    row_number: int
    legal_name: str
    match_names: tuple[str, ...]
    salary: float
    sso5: float
    welfare025: float
    sso10: float
    welfare: float
    tax: float
    net: float

    @property
    def has_salary(self) -> bool:
        return has_amount(self.salary)

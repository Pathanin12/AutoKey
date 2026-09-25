from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pnd3FormValues:
    tax_withheld: float
    surcharge: float
    pv_date: str

    @property
    def has_surcharge(self) -> bool:
        return abs(self.surcharge) >= 0.005

    @property
    def has_tax(self) -> bool:
        return abs(self.tax_withheld) >= 0.005

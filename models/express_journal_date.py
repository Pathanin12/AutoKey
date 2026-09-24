from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressJournalDate:
    voudat: str
    voucher: str
    descrp: str

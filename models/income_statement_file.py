from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IncomeStatementFile:
    file_id: str
    report_type: str
    store_id: str

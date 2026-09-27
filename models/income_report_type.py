from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IncomeReportType:
    code: str
    name: str

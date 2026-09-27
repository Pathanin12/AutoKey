from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IncomeExcelSheetMap:
    header_row: int
    data_start_row: int
    legal_name: int
    username: int
    password: int
    sheet_name: str

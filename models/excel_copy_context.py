from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.ka_tam_row import KaTamRow
from topics.ka_tam.sheet_configs import get_sheet_column_map


@dataclass(frozen=True)
class ExcelCopyContext:
    excel_path: Path
    sheet_name: str
    row_number: int
    legal_name: str
    legal_name_column: int

    @classmethod
    def from_row(cls, excel_path: Path, row: KaTamRow) -> ExcelCopyContext:
        column_map = get_sheet_column_map(row.sheet_name)
        return cls(
            excel_path=excel_path,
            sheet_name=row.sheet_name,
            row_number=row.row_number,
            legal_name=row.legal_name.strip(),
            legal_name_column=column_map.legal_name,
        )

    @property
    def cell_address(self) -> str:
        column = _column_index_to_letter(self.legal_name_column)
        sheet = self.sheet_name.replace("'", "''")
        return f"'{sheet}'!{column}{self.row_number}"


def _column_index_to_letter(index: int) -> str:
    number = index + 1
    letters = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters

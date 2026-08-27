from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from models.ka_tam_row import KaTamRow


@dataclass
class ExcelSheetSummary:
    name: str
    row_count: int


@dataclass
class RunConfig:
    topic: str
    excel_path: Path
    pv_date: str
    description: str = ""
    tax_payer_id: str = ""
    start_from_no: int = 1
    sheet_summaries: list[ExcelSheetSummary] | None = None
    sheet_rows: dict[str, list[KaTamRow]] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.excel_path.exists():
            errors.append(f"ไม่พบไฟล์ Excel: {self.excel_path}")
        if not self.pv_date.strip():
            errors.append("กรุณากรอกวันที่ใบสำคัญ")
        if self.start_from_no < 1:
            errors.append("เริ่มที่ No. ต้อง ≥ 1")
        if self.sheet_summaries is not None and not self.sheet_summaries:
            errors.append("ไม่พบข้อมูลที่รองรับในไฟล์ Excel")
        if self.sheet_summaries and self.sheet_rows and self.planned_row_count() == 0:
            errors.append(f"ไม่พบแถวที่ No. ≥ {self.start_from_no}")
        return errors

    def filter_rows(self, rows: list[KaTamRow]) -> list[KaTamRow]:
        if self.start_from_no <= 1:
            return rows
        return [row for row in rows if row.sequence >= self.start_from_no]

    def planned_row_count(self) -> int:
        if not self.sheet_summaries:
            return 0
        if self.sheet_rows:
            total = 0
            for summary in self.sheet_summaries:
                rows = self.sheet_rows.get(summary.name, [])
                total += len(self.filter_rows(rows))
            return total
        return self.total_rows

    @property
    def sheet_names(self) -> list[str]:
        if not self.sheet_summaries:
            return []
        return [sheet.name for sheet in self.sheet_summaries]

    @property
    def total_rows(self) -> int:
        if not self.sheet_summaries:
            return 0
        return sum(sheet.row_count for sheet in self.sheet_summaries)

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExcelSheetSummary:
    name: str
    row_count: int


@dataclass
class RunConfig:
    topic: str
    excel_path: Path
    pv_date: str
    description: str
    tax_payer_id: str = ""
    company_name: str = ""
    next_company_name: str = ""
    switch_company: bool = False
    use_work_date: bool = True
    sheet_summaries: list[ExcelSheetSummary] | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.excel_path.exists():
            errors.append(f"ไม่พบไฟล์ Excel: {self.excel_path}")
        if not self.description.strip():
            errors.append("กรุณากรอกรายละเอียด")
        if not self.company_name.strip():
            errors.append("กรุณากรอกชื่อบริษัท (โฟล์แรก — ค้นหาในหน้าเลือกข้อมูล)")
        if not self.use_work_date and not self.pv_date.strip():
            errors.append("กรุณากรอกวันที่ใบสำคัญ")
        if self.switch_company and not self.next_company_name.strip():
            errors.append("กรุณากรอกชื่อบริษัทถัดไป (โฟล์สุดท้าย — กด 8 เปลี่ยนบริษัท)")
        if self.sheet_summaries is not None and not self.sheet_summaries:
            errors.append("ไม่พบข้อมูลที่รองรับในไฟล์ Excel")
        return errors

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

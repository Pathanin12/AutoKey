from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Pp30FormConfig:
    pdf_folder: Path
    excel_path: Path
    jv_date: str
    jv_description: str
    pv_description: str
    pdf_files: list[Path] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors: list[str] = []
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append("กรุณาเลือกโฟลเดอร์ PDF")
        elif not self.pdf_files:
            errors.append("ไม่พบไฟล์ PDF ในโฟลเดอร์นี้")
        if not self.excel_path.expanduser().exists():
            errors.append("กรุณาเลือกไฟล์ Excel สำหรับเทียบชื่อ")
        if not self.jv_date.strip():
            errors.append("กรุณากรอกวันที่ JV")
        return errors

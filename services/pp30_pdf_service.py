from __future__ import annotations

from pathlib import Path

from models.pp30_matched_job import Pp30PdfRecord
from services.lookup_match_service import is_plausible_vendor_name, tidy_vendor_name


_COMPANY_PREFIXES = (
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญนิติบุคคล",
    "ห้างหุ้นส่วนสามัญ",
    "บริษัทจำกัดมหาชน",
    "บริษัท ",
    "บจก.",
    "หจก.",
)

_SKIP_LINES = {
    "แบบแสดงรายการภาษีมูลค่าเพิ่ม",
    "ชื่อผู้ประกอบการ",
    "ชื่อสถานประกอบการ",
    "มาหักในการคำนวณภาษีเดือนนี้",
    "ภ.พ.30",
    "ภพ.30",
    "ภพ30",
}


class Pp30PdfService:
    @staticmethod
    def read_text(pdf_path: Path) -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        pages: list[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    @staticmethod
    def extract_company_name(text: str) -> str:
        lines = [tidy_vendor_name(line) for line in (text or "").splitlines()]
        lines = [line for line in lines if line]
        after_label: str | None = None
        saw_label = False
        for line in lines:
            if "ชื่อผู้ประกอบการ" in line.replace(" ", ""):
                saw_label = True
                continue
            if saw_label and after_label is None and _is_company_line(line):
                after_label = line
                break
        if after_label:
            return after_label
        for line in lines:
            if _is_company_line(line):
                return line
        return ""

    @staticmethod
    def load_records(pdf_files: list[Path]) -> list[Pp30PdfRecord]:
        records: list[Pp30PdfRecord] = []
        for pdf_path in pdf_files:
            name = Pp30PdfService.extract_company_name(Pp30PdfService.read_text(pdf_path))
            records.append(Pp30PdfRecord(pdf_path=pdf_path, company_name=name))
        return records


def _is_company_line(line: str) -> bool:
    if line in _SKIP_LINES or not is_plausible_vendor_name(line):
        return False
    compact = line.replace(" ", "")
    if compact in {item.replace(" ", "") for item in _SKIP_LINES}:
        return False
    return any(line.startswith(prefix) for prefix in _COMPANY_PREFIXES)

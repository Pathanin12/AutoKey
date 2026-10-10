from __future__ import annotations

from pathlib import Path

from models.bt40_form_values import Bt40FormValues
from models.bt40_pdf_record import Bt40PdfRecord
from services.bt40_extract_service import extract_bt40_amounts, extract_bt40_period, extract_bt40_pv_date
from services.name_match_service import tidy_name

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
    "แบบแสดงรายการภาษีธุรกิจเฉพาะ",
    "ตามประมวลรัษฎากร",
    "ภ.ธ.40",
    "ภธ.40",
    "ภธ40",
}
_NAME_LABEL = "ชื่อผู้ประกอบกิจการ"
_NAME_CUTS = (" (1)", " (2)", " (3)")


class Bt40PdfService:
    @staticmethod
    def read_text(pdf_path: Path) -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        pages: list[str] = []
        for page in reader.pages:
            layout = ""
            try:
                layout = page.extract_text(extraction_mode="layout") or ""
            except TypeError:
                layout = ""
            plain = page.extract_text() or ""
            pages.append("\n".join(part for part in (layout, plain) if part))
        return "\n".join(pages)

    @staticmethod
    def extract_company_name(text: str) -> str:
        lines = [_clean_company_line(line) for line in (text or "").splitlines()]
        lines = [line for line in lines if line]
        after_label: str | None = None
        saw_label = False
        for line in lines:
            compact = line.replace(" ", "")
            if _NAME_LABEL.replace(" ", "") in compact:
                saw_label = True
                rest = tidy_name(line.split("กิจการ", 1)[-1]) if "กิจการ" in line else ""
                if _is_company_line(rest):
                    return rest
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
    def extract_form_values(text: str) -> Bt40FormValues | None:
        amounts = extract_bt40_amounts(text)
        if amounts is None:
            return None
        line7, line13, line14, line17 = amounts
        return Bt40FormValues(
            line7_receipt=line7,
            line13=line13,
            line14=line14,
            line17=line17,
            pv_date=extract_bt40_pv_date(text),
            period=extract_bt40_period(text),
        )

    @staticmethod
    def load_record(pdf_path: Path) -> Bt40PdfRecord:
        text = Bt40PdfService.read_text(pdf_path)
        name = Bt40PdfService.extract_company_name(text)
        if not name:
            name = tidy_name(pdf_path.stem)
        return Bt40PdfRecord(
            pdf_path=pdf_path,
            company_name=name,
            form_values=Bt40PdfService.extract_form_values(text),
        )


def _clean_company_line(line: str) -> str:
    text = tidy_name(line).rstrip(" .")
    for marker in _NAME_CUTS:
        if marker in text:
            text = tidy_name(text.split(marker, 1)[0])
    return text.rstrip(" .")


def _is_company_line(line: str) -> bool:
    if not line or line in _SKIP_LINES:
        return False
    compact = line.replace(" ", "")
    if compact in {item.replace(" ", "") for item in _SKIP_LINES}:
        return False
    return any(line.startswith(prefix) for prefix in _COMPANY_PREFIXES)

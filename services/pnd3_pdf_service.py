from __future__ import annotations

from pathlib import Path

from models.pnd3_form_values import Pnd3FormValues
from models.pnd3_pdf_record import Pnd3PdfRecord
from services.name_match_service import tidy_name
from services.pnd3_extract_service import extract_line_2_and_3
from services.pnd30_extract_service import extract_pv_date

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
    "แบบยื่นรายการภาษีเงินได้หัก ณ ที่จ่าย",
    "ภ.ง.ด.3",
    "ภงด.3",
    "ภงด3",
    "ภ.ง.ด.53",
    "ภงด.53",
    "ภงด53",
}
_NAME_LABEL = "ชื่อผู้มีหน้าที่หักภาษี"
_NAME_CUTS = (" (1)", " (2)", " (3)", " มาตรา")


class Pnd3PdfService:
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
            if _NAME_LABEL in line.replace(" ", ""):
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
    def extract_form_values(text: str) -> Pnd3FormValues | None:
        pv_date = extract_pv_date(text)
        lines = extract_line_2_and_3(text)
        if lines is None or not pv_date:
            return None
        tax_withheld, surcharge = lines
        return Pnd3FormValues(tax_withheld=tax_withheld, surcharge=surcharge, pv_date=pv_date)

    @staticmethod
    def load_record(pdf_path: Path) -> Pnd3PdfRecord:
        text = Pnd3PdfService.read_text(pdf_path)
        name = Pnd3PdfService.extract_company_name(text)
        if not name:
            name = tidy_name(pdf_path.stem)
        return Pnd3PdfRecord(
            pdf_path=pdf_path,
            company_name=name,
            form_values=Pnd3PdfService.extract_form_values(text),
        )


def _clean_company_line(line: str) -> str:
    text = tidy_name(line).rstrip(" .")
    for marker in _NAME_CUTS:
        if marker in text:
            text = tidy_name(text.split(marker, 1)[0])
    return text.rstrip(" .")


def _is_company_line(line: str) -> bool:
    if line in _SKIP_LINES:
        return False
    compact = line.replace(" ", "")
    if compact in {item.replace(" ", "") for item in _SKIP_LINES}:
        return False
    return any(line.startswith(prefix) for prefix in _COMPANY_PREFIXES)

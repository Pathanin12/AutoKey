from __future__ import annotations

from pathlib import Path

from models.sso_form_values import SsoFormValues
from models.sso_pdf_record import SsoPdfRecord
from services.name_match_service import tidy_name
from services.sso_extract_service import extract_sso_date, extract_sso_receipt_no, extract_sso_values

_COMPANY_PREFIXES = (
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญนิติบุคคล",
    "ห้างหุ้นส่วนสามัญ",
    "บริษัทจำกัดมหาชน",
    "บริษัท ",
    "บจก.",
    "หจก.",
)
_PAYER_LABEL = "ผู้ชำระเงิน"
_NAME_CUTS = ("เงินสมทบนายจ้าง", "เงินสมทบผู้ประกันตน", "เลขที่บัญชีนายจ้าง")


class SsoPdfService:
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
        for line in lines:
            if _PAYER_LABEL in line.replace(" ", ""):
                name = _company_from_line(line)
                if name:
                    return name
        for line in lines:
            name = _company_from_line(line)
            if name:
                return name
        return ""

    @staticmethod
    def extract_form_values(text: str) -> SsoFormValues | None:
        amounts = extract_sso_values(text)
        pv_date = extract_sso_date(text)
        if amounts is None or not pv_date:
            return None
        contrib_amount, surcharge, paid_amount = amounts
        return SsoFormValues(
            contrib_amount=contrib_amount,
            surcharge=surcharge,
            paid_amount=paid_amount,
            pv_date=pv_date,
            receipt_no=extract_sso_receipt_no(text),
        )

    @staticmethod
    def load_record(pdf_path: Path) -> SsoPdfRecord:
        text = SsoPdfService.read_text(pdf_path)
        name = SsoPdfService.extract_company_name(text)
        if not name:
            name = tidy_name(pdf_path.stem)
        return SsoPdfRecord(
            pdf_path=pdf_path,
            company_name=name,
            form_values=SsoPdfService.extract_form_values(text),
        )


def _clean_company_line(line: str) -> str:
    text = tidy_name(line).rstrip(" .")
    for marker in _NAME_CUTS:
        if marker in text:
            text = tidy_name(text.split(marker, 1)[0])
    if _PAYER_LABEL in text:
        text = tidy_name(text.split(_PAYER_LABEL, 1)[-1]).lstrip(" .")
    return text.rstrip(" .")


def _company_from_line(line: str) -> str:
    if not any(line.startswith(prefix) or prefix in line for prefix in _COMPANY_PREFIXES):
        return ""
    for prefix in _COMPANY_PREFIXES:
        if prefix in line:
            start = line.find(prefix)
            return tidy_name(line[start:]).rstrip(" .")
    return ""

from __future__ import annotations

from pathlib import Path

from models.income_form_values import IncomeFormValues
from models.income_pdf_record import IncomePdfRecord
from services.income_extract_service import extract_income_values
from services.income_sap_text_service import IncomeSapTextService


class IncomePdfService:
    @staticmethod
    def read_text(pdf_path: Path) -> str:
        return "\n".join(IncomePdfService._page_texts(pdf_path))

    @staticmethod
    def load_record(pdf_path: Path) -> IncomePdfRecord:
        texts = IncomePdfService._page_texts(pdf_path)
        return IncomePdfRecord(
            pdf_path=pdf_path,
            invoices=_invoices(texts),
            has_text=any(text.strip() for text in texts),
        )

    @staticmethod
    def load_invoices(pdf_path: Path) -> list[IncomeFormValues]:
        return _invoices(IncomePdfService._page_texts(pdf_path))

    @staticmethod
    def shop_name(pdf_path: Path) -> str:
        invoices = IncomePdfService.load_invoices(pdf_path)
        return invoices[0].company_name if invoices else ""

    @staticmethod
    def _page_texts(pdf_path: Path) -> list[str]:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        try:
            return [_best_page_text(page) for page in reader.pages]
        finally:
            closer = getattr(reader, "close", None)
            if closer:
                closer()


def _invoices(texts: list[str]) -> list[IncomeFormValues]:
    invoices: list[IncomeFormValues] = []
    seen: set[tuple[str, str, str, float]] = set()
    for text in texts:
        values = extract_income_values(text)
        if values is None:
            continue
        key = (values.kind, values.invoice_number, values.branch_last5, round(values.total_amount, 2))
        if key in seen:
            continue
        seen.add(key)
        invoices.append(values)
    return invoices


def _best_page_text(page) -> str:
    raw = _pypdf_page(page)
    if extract_income_values(raw):
        return raw
    decoded = IncomeSapTextService.read_page(page)
    if extract_income_values(decoded):
        return decoded
    return raw


def _pypdf_page(page) -> str:
    layout = ""
    try:
        layout = page.extract_text(extraction_mode="layout") or ""
    except TypeError:
        layout = ""
    plain = page.extract_text() or ""
    return "\n".join(part for part in (layout, plain) if part)

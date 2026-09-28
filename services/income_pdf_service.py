from __future__ import annotations

from pathlib import Path

from models.income_form_values import IncomeFormValues
from models.income_pdf_record import IncomePdfRecord
from services.income_extract_service import extract_income_values
from services.income_sap_text_service import IncomeSapTextService
from services.pdf_password_service import PdfLockedError, PdfPasswordService


class IncomePdfService:
    @staticmethod
    def read_text(pdf_path: Path) -> str:
        return "\n".join(IncomePdfService._page_texts(pdf_path))

    @staticmethod
    def load_record(pdf_path: Path, password: str = "") -> IncomePdfRecord:
        try:
            pages = IncomePdfService._read_pages(pdf_path, password)
        except PdfLockedError:
            return IncomePdfRecord(pdf_path=pdf_path, invoices=[], has_text=False, locked=True)
        texts = [text or "" for text in pages]
        return IncomePdfRecord(
            pdf_path=pdf_path,
            invoices=invoices_from_texts(texts),
            has_text=any(text.strip() for text in texts),
            broken_pages=[number for number, text in enumerate(pages, start=1) if text is None],
        )

    @staticmethod
    def load_invoices(pdf_path: Path) -> list[IncomeFormValues]:
        return invoices_from_texts(IncomePdfService._page_texts(pdf_path))

    @staticmethod
    def shop_name(pdf_path: Path) -> str:
        invoices = IncomePdfService.load_invoices(pdf_path)
        return invoices[0].company_name if invoices else ""

    @staticmethod
    def _page_texts(pdf_path: Path, password: str = "") -> list[str]:
        return [text or "" for text in IncomePdfService._read_pages(pdf_path, password)]

    @staticmethod
    def _read_pages(pdf_path: Path, password: str = "") -> list[str | None]:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        try:
            PdfPasswordService.unlock(reader, password)
            return [_safe_page_text(reader, index) for index in range(len(reader.pages))]
        finally:
            closer = getattr(reader, "close", None)
            if closer:
                closer()


def invoices_from_texts(texts: list[str]) -> list[IncomeFormValues]:
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


def _safe_page_text(reader, index: int) -> str | None:
    try:
        return _best_page_text(reader.pages[index])
    except Exception:
        return None


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

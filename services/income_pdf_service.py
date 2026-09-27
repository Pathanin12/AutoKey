from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from models.income_form_values import IncomeFormValues
from models.income_pdf_record import IncomePdfRecord
from services.income_extract_service import extract_income_invoice
from services.income_ocr_service import IncomeOcrService
from services.income_pdf_render_service import IncomePdfRenderService
from services.income_sap_text_service import IncomeSapTextService


class IncomePdfService:
    @staticmethod
    def read_text(pdf_path: Path) -> str:
        return "\n".join(IncomePdfService._page_texts(pdf_path))

    @staticmethod
    def load_record(pdf_path: Path) -> IncomePdfRecord:
        return IncomePdfRecord(pdf_path=pdf_path, invoices=IncomePdfService.load_invoices(pdf_path))

    @staticmethod
    def load_invoices(pdf_path: Path) -> list[IncomeFormValues]:
        invoices: list[IncomeFormValues] = []
        seen: set[tuple[str, str]] = set()
        for text in IncomePdfService._page_texts(pdf_path):
            values = extract_income_invoice(text)
            if values is None:
                continue
            key = (values.invoice_number, values.branch_last5)
            if key in seen:
                continue
            seen.add(key)
            invoices.append(values)
        return invoices

    @staticmethod
    def shop_name(pdf_path: Path) -> str:
        invoices = IncomePdfService.load_invoices(pdf_path)
        return invoices[0].company_name if invoices else ""

    @staticmethod
    def _page_texts(pdf_path: Path) -> list[str]:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        texts = [_best_page_text(page) for page in reader.pages]
        if any(extract_income_invoice(text) for text in texts):
            return texts
        return _ocr_pages(pdf_path)


def _best_page_text(page) -> str:
    raw = _pypdf_page(page)
    if extract_income_invoice(raw):
        return raw
    decoded = IncomeSapTextService.read_page(page)
    if extract_income_invoice(decoded):
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


def _ocr_pages(pdf_path: Path) -> list[str]:
    with TemporaryDirectory(prefix="income-pdf-") as raw_dir:
        images = IncomePdfRenderService.render_pages(pdf_path, Path(raw_dir))
        return [IncomeOcrService.read_image(path) for path in images]

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from models.income_form_values import IncomeFormValues
from models.income_pdf_record import IncomePdfRecord
from services.income_extract_service import extract_income_invoice, is_rv_tax_invoice
from services.income_ocr_service import IncomeOcrService
from services.income_pdf_render_service import IncomePdfRenderService


class IncomePdfService:
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
    def load_record(pdf_path: Path) -> IncomePdfRecord:
        return IncomePdfRecord(pdf_path=pdf_path, invoices=IncomePdfService.load_invoices(pdf_path))

    @staticmethod
    def load_invoices(pdf_path: Path) -> list[IncomeFormValues]:
        invoices: list[IncomeFormValues] = []
        seen: set[tuple[str, str]] = set()
        for text in IncomePdfService._page_texts(pdf_path):
            if not is_rv_tax_invoice(text):
                continue
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
    def _page_texts(pdf_path: Path) -> list[str]:
        raw = IncomePdfService.read_text(pdf_path)
        if is_rv_tax_invoice(raw):
            return [raw]
        return _ocr_pages(pdf_path)


def _ocr_pages(pdf_path: Path) -> list[str]:
    with TemporaryDirectory(prefix="income-pdf-") as raw_dir:
        images = IncomePdfRenderService.render_pages(pdf_path, Path(raw_dir))
        return [IncomeOcrService.read_image(path) for path in images]

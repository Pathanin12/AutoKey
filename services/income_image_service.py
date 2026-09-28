from __future__ import annotations

from pathlib import Path

from models.income_pdf_record import IncomePdfRecord
from services.income_ocr_service import IncomeOcrService
from services.income_pdf_service import invoices_from_texts


class IncomeImageService:
    @staticmethod
    def load_record(image_path: Path) -> IncomePdfRecord:
        text = IncomeOcrService.read_image(image_path)
        return IncomePdfRecord(
            pdf_path=image_path,
            invoices=invoices_from_texts([text]),
            has_text=bool(text.strip()),
        )

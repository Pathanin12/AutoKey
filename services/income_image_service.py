from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from constants.routes import PDF_OPEN_EXTENSIONS
from models.income_pdf_record import IncomePdfRecord
from services.income_ocr_service import IncomeOcrService
from services.income_pdf_render_service import IncomePdfRenderService
from services.income_pdf_service import invoices_from_texts


class IncomeImageService:
    @staticmethod
    def load_record(image_path: Path) -> IncomePdfRecord:
        texts = _image_texts(image_path)
        return IncomePdfRecord(
            pdf_path=image_path,
            invoices=invoices_from_texts(texts),
            has_text=any(text.strip() for text in texts),
        )


def _image_texts(path: Path) -> list[str]:
    if path.suffix.lower().lstrip(".") not in PDF_OPEN_EXTENSIONS:
        return [IncomeOcrService.read_image(path)]
    with TemporaryDirectory(prefix="income-pages-") as work_dir:
        pages = IncomePdfRenderService.render_pages(path, Path(work_dir))
        return [IncomeOcrService.read_image(page) for page in pages]

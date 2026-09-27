from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from models.income_form_values import IncomeFormValues
from models.income_pdf_record import IncomePdfRecord
from services.income_extract_service import extract_income_invoice, is_rv_tax_invoice
from services.income_ocr_service import IncomeOcrService


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
    try:
        import Quartz
        from AppKit import NSBitmapImageRep, NSColor, NSGraphicsContext, NSImage, NSPNGFileType
    except ImportError:
        return []
    url = Quartz.NSURL.fileURLWithPath_(str(pdf_path))
    document = Quartz.PDFDocument.alloc().initWithURL_(url)
    if document is None:
        return []
    texts: list[str] = []
    scale = 1.5
    with TemporaryDirectory(prefix="income-pdf-") as raw_dir:
        folder = Path(raw_dir)
        for index in range(document.pageCount()):
            page = document.pageAtIndex_(index)
            box = page.boundsForBox_(Quartz.kPDFDisplayBoxMediaBox)
            width, height = int(box.size.width * scale), int(box.size.height * scale)
            image = NSImage.alloc().initWithSize_((width, height))
            image.lockFocus()
            NSColor.whiteColor().set()
            Quartz.NSRectFill(((0, 0), (width, height)))
            ctx = NSGraphicsContext.currentContext().graphicsPort()
            Quartz.CGContextSaveGState(ctx)
            Quartz.CGContextScaleCTM(ctx, scale, scale)
            page.drawWithBox_(Quartz.kPDFDisplayBoxMediaBox)
            Quartz.CGContextRestoreGState(ctx)
            image.unlockFocus()
            tiff = image.TIFFRepresentation()
            rep = NSBitmapImageRep.imageRepWithData_(tiff)
            png = rep.representationUsingType_properties_(NSPNGFileType, None)
            dest = folder / f"page-{index + 1:03d}.png"
            dest.write_bytes(png)
            texts.append(IncomeOcrService.read_image(dest))
    return texts

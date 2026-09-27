from __future__ import annotations

from pathlib import Path


class IncomePdfRenderService:
    @staticmethod
    def render_pages(pdf_path: Path, folder: Path) -> list[Path]:
        pages = _render_quartz(pdf_path, folder)
        if pages:
            return pages
        return _render_pdfium(pdf_path, folder)


def _render_quartz(pdf_path: Path, folder: Path) -> list[Path]:
    try:
        import Quartz
        from AppKit import NSBitmapImageRep, NSColor, NSGraphicsContext, NSImage, NSPNGFileType
    except ImportError:
        return []
    url = Quartz.NSURL.fileURLWithPath_(str(pdf_path))
    document = Quartz.PDFDocument.alloc().initWithURL_(url)
    if document is None:
        return []
    scale = 2.0
    paths: list[Path] = []
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
        paths.append(dest)
    return paths


def _render_pdfium(pdf_path: Path, folder: Path) -> list[Path]:
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return []
    document = pdfium.PdfDocument(str(pdf_path))
    paths: list[Path] = []
    try:
        for index, page in enumerate(document):
            bitmap = page.render(scale=2)
            image = bitmap.to_pil()
            dest = folder / f"page-{index + 1:03d}.png"
            image.save(dest)
            paths.append(dest)
            page.close()
    finally:
        document.close()
    return paths

from __future__ import annotations

from pathlib import Path

_RENDER_SCALE = 2


class IncomePdfRenderService:
    @staticmethod
    def render_pages(pdf_path: Path, folder: Path) -> list[Path]:
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(str(pdf_path))
        paths: list[Path] = []
        try:
            for index, page in enumerate(document):
                try:
                    image = page.render(scale=_RENDER_SCALE).to_pil()
                    dest = folder / f"page-{index + 1:03d}.png"
                    image.save(dest)
                    paths.append(dest)
                finally:
                    page.close()
        finally:
            document.close()
        return paths

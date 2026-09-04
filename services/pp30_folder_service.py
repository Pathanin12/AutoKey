from __future__ import annotations

from pathlib import Path

from constants.routes import PDF_OPEN_EXTENSIONS


class Pp30FolderService:
    @staticmethod
    def list_pdfs(folder: Path) -> list[Path]:
        path = folder.expanduser()
        if not path.exists() or not path.is_dir():
            return []
        files: list[Path] = []
        for child in path.iterdir():
            if not child.is_file() or child.name.startswith("."):
                continue
            if child.suffix.lower().lstrip(".") in PDF_OPEN_EXTENSIONS:
                files.append(child)
        return sorted(files)

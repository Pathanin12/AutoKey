from __future__ import annotations

from pathlib import Path

from constants.routes import IMAGE_OPEN_EXTENSIONS, PDF_OPEN_EXTENSIONS
from models.income_source_mode import IncomeSourceMode


class IncomeFolderService:
    @staticmethod
    def list_files(folder: Path, source: IncomeSourceMode) -> list[Path]:
        path = folder.expanduser()
        if not str(path).strip() or not path.exists() or not path.is_dir():
            return []
        extensions = IMAGE_OPEN_EXTENSIONS if source.is_image else PDF_OPEN_EXTENSIONS
        return [
            child
            for child in sorted(path.iterdir())
            if child.is_file() and child.suffix.lower().lstrip(".") in extensions
        ]

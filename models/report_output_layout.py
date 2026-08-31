from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants.routes import REPORT_SCREENSHOT_FILENAME

_INVALID_FOLDER_CHARS = '<>:"/\\|?*'


def safe_folder_name(value: str) -> str:
    text = value.strip()
    for char in _INVALID_FOLDER_CHARS:
        text = text.replace(char, "")
    text = text.strip(" .")
    return text or "unknown"


@dataclass(frozen=True)
class ReportOutputLayout:
    base_dir: Path
    legal_name: str
    month_folder: str

    def screenshot_path(self, account_code: str) -> Path:
        return (
            self.base_dir
            / safe_folder_name(self.legal_name)
            / self.month_folder
            / account_code
            / REPORT_SCREENSHOT_FILENAME
        )

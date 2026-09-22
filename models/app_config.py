from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants.routes import UI_TEXT


@dataclass
class AppConfig:
    express_data_dir: Path

    def validate(self) -> list[str]:
        folder = self.express_data_dir.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            return [UI_TEXT["express_data_dir_invalid"]]
        return []

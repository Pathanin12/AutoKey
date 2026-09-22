from __future__ import annotations

from pathlib import Path

import yaml

from constants.routes import CONFIG_PATH
from models.app_config import AppConfig


class AppConfigService:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CONFIG_PATH

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig(express_data_dir=Path(""))
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return AppConfig(
            express_data_dir=Path(str(raw.get("express_data_dir", "") or "").strip()),
        )

    def save(self, config: AppConfig) -> None:
        payload = {"express_data_dir": str(config.express_data_dir).strip()}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

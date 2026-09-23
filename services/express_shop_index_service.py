from __future__ import annotations

from pathlib import Path

import yaml

from constants.routes import SHOP_INDEX_FILE_KEY, SHOP_INDEX_SHOP_KEY, SHOPS_PATH
from models.express_company import ExpressCompany
from models.express_shop_index import ExpressShopIndex
from services.express_data_folder_service import ExpressDataFolderService


class ExpressShopIndexService:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or SHOPS_PATH

    def write_from_dir(self, express_data_dir: Path) -> list[ExpressCompany]:
        companies = ExpressDataFolderService.list_companies(express_data_dir)
        self.save([ExpressShopIndex(file_name=company.folder.name, shop_name=company.shop_name) for company in companies])
        return companies

    def save(self, rows: list[ExpressShopIndex]) -> None:
        payload = [
            {SHOP_INDEX_FILE_KEY: row.file_name, SHOP_INDEX_SHOP_KEY: row.shop_name}
            for row in rows
        ]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def load(self, express_data_dir: Path) -> list[ExpressCompany]:
        if not self.path.exists():
            return []
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or []
        companies: list[ExpressCompany] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            file_name = str(item.get(SHOP_INDEX_FILE_KEY) or "").strip()
            shop_name = str(item.get(SHOP_INDEX_SHOP_KEY) or "").strip()
            if not file_name or not shop_name:
                continue
            companies.append(
                ExpressCompany(folder=express_data_dir / file_name, shop_name=shop_name)
            )
        return companies

    def count(self) -> int:
        if not self.path.exists():
            return 0
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or []
        if not isinstance(raw, list):
            return 0
        return sum(
            1
            for item in raw
            if isinstance(item, dict)
            and str(item.get(SHOP_INDEX_FILE_KEY) or "").strip()
            and str(item.get(SHOP_INDEX_SHOP_KEY) or "").strip()
        )

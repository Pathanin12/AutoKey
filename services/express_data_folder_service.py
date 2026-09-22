from __future__ import annotations

from pathlib import Path

from constants.routes import ISINFO_FILE_NAMES, ISINFO_SHOP_NAME_FIELD
from models.express_company import ExpressCompany
from services.dbf_read_service import DbfReadService


class ExpressDataFolderService:
    @staticmethod
    def list_company_dirs(root: Path) -> list[Path]:
        folder = root.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            return []
        found: list[Path] = []
        for child in sorted(folder.iterdir()):
            if not child.is_dir():
                continue
            if any((child / name).exists() for name in ISINFO_FILE_NAMES):
                found.append(child)
        return found

    @staticmethod
    def list_companies(root: Path) -> list[ExpressCompany]:
        companies: list[ExpressCompany] = []
        for folder in ExpressDataFolderService.list_company_dirs(root):
            shop_name = ExpressDataFolderService.read_shop_name(folder)
            if shop_name:
                companies.append(ExpressCompany(folder=folder, shop_name=shop_name))
        return companies

    @staticmethod
    def read_shop_name(folder: Path) -> str:
        for name in ISINFO_FILE_NAMES:
            path = folder / name
            if not path.exists():
                continue
            records = DbfReadService.read_records(path)
            if not records:
                continue
            shop_name = str(records[0].get(ISINFO_SHOP_NAME_FIELD) or "").strip()
            if shop_name:
                return shop_name
        return ""

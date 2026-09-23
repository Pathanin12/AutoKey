from __future__ import annotations

from models.express_company import ExpressCompany
from services.name_match_service import compact_name, core_company_name, tidy_name


class Pp30MatchService:
    @staticmethod
    def lookup(companies: list[ExpressCompany]) -> dict[str, ExpressCompany]:
        table: dict[str, ExpressCompany] = {}
        for company in companies:
            for key in _name_keys(company.shop_name):
                table.setdefault(key, company)
        return table

    @staticmethod
    def match_lookup(pdf_name: str, table: dict[str, ExpressCompany]) -> ExpressCompany | None:
        if not (pdf_name or "").strip():
            return None
        for key in _name_keys(pdf_name):
            found = table.get(key)
            if found:
                return found
        return None

    @staticmethod
    def match_name(pdf_name: str, companies: list[ExpressCompany]) -> ExpressCompany | None:
        return Pp30MatchService.match_lookup(pdf_name, Pp30MatchService.lookup(companies))


def _name_keys(value: str) -> list[str]:
    tidy = tidy_name(value)
    keys: list[str] = []
    for key in (compact_name(tidy), compact_name(core_company_name(tidy))):
        if key and key not in keys:
            keys.append(key)
    return keys

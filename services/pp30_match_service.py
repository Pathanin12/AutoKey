from __future__ import annotations

import re

from models.express_company import ExpressCompany
from services.name_match_service import compact_name, core_company_name, fold_thai_marks, tidy_name

_YEAR_SUFFIX = re.compile(r"(?:ปี\s*)?(\d{2})$")


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
    def match_name(
        pdf_name: str,
        companies: list[ExpressCompany],
        year: int | None = None,
    ) -> ExpressCompany | None:
        return _pick_shop(Pp30MatchService.match_all(pdf_name, companies), year)

    @staticmethod
    def match_names(
        names: list[str],
        companies: list[ExpressCompany],
        year: int | None = None,
    ) -> ExpressCompany | None:
        found: list[ExpressCompany] = []
        seen: set[str] = set()
        for name in names:
            for company in Pp30MatchService.match_all(name, companies):
                folder = str(company.folder.resolve())
                if folder in seen:
                    continue
                seen.add(folder)
                found.append(company)
        return _pick_shop(found, year)

    @staticmethod
    def match_all(pdf_name: str, companies: list[ExpressCompany]) -> list[ExpressCompany]:
        if not (pdf_name or "").strip():
            return []
        keys = set(_name_keys(pdf_name))
        found: list[ExpressCompany] = []
        seen: set[str] = set()
        for company in companies:
            if not keys.intersection(_name_keys(company.shop_name)):
                continue
            folder = str(company.folder.resolve())
            if folder in seen:
                continue
            seen.add(folder)
            found.append(company)
        return found


def _express_label(company: ExpressCompany) -> str:
    return tidy_name(company.folder.name)


def _label_year(label: str) -> int | None:
    match = _YEAR_SUFFIX.search(label.replace(" ", ""))
    if not match:
        return None
    year = int(match.group(1))
    if 50 <= year <= 99:
        return year
    return None


def _pick_shop(found: list[ExpressCompany], year: int | None) -> ExpressCompany | None:
    if not found:
        return None
    if len(found) == 1:
        return found[0]
    kept: list[ExpressCompany] = []
    for company in found:
        label_year = _label_year(_express_label(company))
        if label_year is None:
            kept.append(company)
            continue
        if year is None or label_year == year:
            kept.append(company)
    if not kept:
        return None
    plain = [company for company in kept if _label_year(_express_label(company)) is None]
    if plain:
        return plain[0]
    return kept[0]


def _name_keys(value: str) -> list[str]:
    tidy = tidy_name(value)
    keys: list[str] = []
    for raw in (tidy, core_company_name(tidy)):
        for key in (compact_name(raw), fold_thai_marks(raw)):
            if key and key not in keys:
                keys.append(key)
    return keys

from __future__ import annotations

from models.express_company import ExpressCompany
from services.name_match_service import names_match


class Pp30MatchService:
    @staticmethod
    def match_name(pdf_name: str, companies: list[ExpressCompany]) -> ExpressCompany | None:
        if not (pdf_name or "").strip():
            return None
        for company in companies:
            if names_match(pdf_name, company.shop_name):
                return company
        return None

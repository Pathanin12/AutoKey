from __future__ import annotations

from http.cookiejar import CookieJar

from api.income_eko_api import IncomeEkoApi
from api.income_sbp_api import IncomeSbpApi
from models.income_portal_account import IncomePortalAccount
from models.income_portal_session import IncomePortalSession


class IncomePortalLoginService:
    @staticmethod
    def login(account: IncomePortalAccount) -> IncomePortalSession:
        cookies = CookieJar()
        IncomeEkoApi.login(account, cookies)
        IncomeSbpApi.login(cookies)
        return IncomePortalSession(cookies=cookies)

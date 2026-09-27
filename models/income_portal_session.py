from __future__ import annotations

from dataclasses import dataclass
from http.cookiejar import CookieJar


@dataclass
class IncomePortalSession:
    cookies: CookieJar

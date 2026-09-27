from __future__ import annotations

import json
import time
import uuid
from http.cookiejar import CookieJar

from api.income_http import copy_cookie, request
from constants.routes import EKO_HTTP_URL, EKO_LOGIN_PATH, EKO_ORIGIN_URL, UI_TEXT
from models.income_portal_account import IncomePortalAccount


class IncomeEkoApi:
    @staticmethod
    def login(account: IncomePortalAccount, cookies: CookieJar) -> None:
        payload = {
            "username": account.username,
            "password": account.password,
            "refCode": str(uuid.uuid4()),
            "domain": "",
            "deviceId": f"webapp2x0{uuid.uuid4().hex}{int(time.time() * 1000)}",
            "deviceVersion": "9.3.0",
            "deviceType": "web",
            "deviceModel": "browser",
            "appId": "com.ekoapp.eko",
            "apiVersion": 0,
            "deviceName": "Mozilla/5.0 AutoKey",
        }
        status, _headers, body, _url = request(
            cookies,
            "POST",
            EKO_HTTP_URL + EKO_LOGIN_PATH,
            payload=payload,
            origin=EKO_ORIGIN_URL,
        )
        data = _json(body)
        if status != 200 or not data.get("success"):
            raise ValueError(UI_TEXT["income_login_failed"].format(name=account.legal_name))
        copy_cookie(cookies, "eko.session", (".ekoapp.com", "cpall.ekoapp.com"))


def _json(body: bytes) -> dict:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}

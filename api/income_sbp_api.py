from __future__ import annotations

import json
from http.cookiejar import CookieJar
from pathlib import Path

from api.income_http import join, query, request
from constants.routes import (
    INCOME_PRINT_ALL_NAME,
    INCOME_WANTED_REPORT_CODES,
    INCOME_WANTED_REPORT_NAMES,
    SBP_AUTH_LOGIN_PATH,
    SBP_BFF_URL,
    SBP_FILE_TYPE_NORMAL,
    SBP_MERGE_FILE_PATH,
    SBP_ORIGIN_URL,
    SBP_REPORT_TYPES_PATH,
    SBP_SEARCH_REPORT_PATH,
    SBP_STATEMENT_PATH,
    SBP_STATEMENT_TYPE,
    SBP_STORES_PATH,
)
from models.income_portal_store import IncomePortalStore
from models.income_report_type import IncomeReportType
from models.income_statement_file import IncomeStatementFile


class IncomeSbpApi:
    @staticmethod
    def login(cookies: CookieJar) -> None:
        url = query(
            SBP_BFF_URL + SBP_AUTH_LOGIN_PATH,
            {"redirectUrl": SBP_ORIGIN_URL + SBP_STATEMENT_PATH},
        )
        for _ in range(8):
            status, headers, _body, location = request(
                cookies, "GET", url, origin=SBP_ORIGIN_URL, follow=False
            )
            nxt = headers.get("Location") or location
            if not nxt or status < 300 or status >= 400:
                break
            url = join(url, nxt)
        names = {item.name for item in cookies}
        if not {"sbp_token_1", "sbp_token_2", "sbp_token_3"} <= names:
            raise ValueError("เข้า SBP Mall ไม่ได้")

    @staticmethod
    def stores(cookies: CookieJar, start_date: str) -> list[IncomePortalStore]:
        url = query(
            SBP_BFF_URL + SBP_STORES_PATH,
            {"type": SBP_STATEMENT_TYPE, "start_date": start_date, "subtype_ptt": "0"},
        )
        status, _headers, body, _url = request(cookies, "GET", url, origin=SBP_ORIGIN_URL)
        rows = _data(body) if status < 400 else []
        stores: list[IncomePortalStore] = []
        for row in rows:
            store_id = str(row.get("store_id") or "").strip()
            if store_id:
                stores.append(
                    IncomePortalStore(
                        store_id=store_id,
                        store_name=str(row.get("store_name") or store_id),
                    )
                )
        return stores

    @staticmethod
    def report_types(cookies: CookieJar, start_date: str, end_date: str) -> list[IncomeReportType]:
        url = query(
            SBP_BFF_URL + SBP_REPORT_TYPES_PATH,
            {"type": SBP_STATEMENT_TYPE, "start_date": start_date, "end_date": end_date},
        )
        status, _headers, body, _url = request(cookies, "GET", url, origin=SBP_ORIGIN_URL)
        rows = _data(body) if status < 400 else []
        types: list[IncomeReportType] = []
        for row in rows:
            code = str(row.get("code_value") or "").strip()
            if code:
                types.append(
                    IncomeReportType(
                        code=code,
                        name=str(row.get("code_name") or ""),
                    )
                )
        return types

    @staticmethod
    def search(
        cookies: CookieJar,
        start_date: str,
        end_date: str,
        store_ids: list[str],
        report_types: list[str],
    ) -> list[IncomeStatementFile]:
        payload = {
            "type": SBP_STATEMENT_TYPE,
            "startDate": start_date,
            "endDate": end_date,
            "storeIdList": store_ids,
            "reportType": report_types,
            "subTypePTT": "0",
            "firstRow": "1",
            "lastRow": "200",
        }
        status, _headers, body, _url = request(
            cookies,
            "POST",
            SBP_BFF_URL + SBP_SEARCH_REPORT_PATH,
            payload=payload,
            origin=SBP_ORIGIN_URL,
        )
        data = _object(body)
        rows = ((data.get("data") or {}).get("resultStmtList") if data else None) or []
        files: list[IncomeStatementFile] = []
        if status >= 400:
            return files
        for row in rows:
            file_id = str(row.get("file_id") or "").strip()
            if file_id:
                files.append(
                    IncomeStatementFile(
                        file_id=file_id,
                        report_type=str(row.get("report_type") or ""),
                        store_id=str(row.get("store_id") or ""),
                    )
                )
        return files

    @staticmethod
    def merge(cookies: CookieJar, files: list[IncomeStatementFile], dest: Path) -> Path:
        payload = {"ids": [{"id": item.file_id, "type": SBP_FILE_TYPE_NORMAL} for item in files]}
        status, _headers, body, _url = request(
            cookies,
            "POST",
            SBP_BFF_URL + SBP_MERGE_FILE_PATH,
            payload=payload,
            origin=SBP_ORIGIN_URL,
        )
        if status >= 400 or body[:4] != b"%PDF":
            raise ValueError("รวมไฟล์ไม่ได้")
        dest.write_bytes(body)
        return dest


def fold_report_name(value: str) -> str:
    return "".join((value or "").lower().split())


def pick_report_types(available: list[IncomeReportType]) -> list[str]:
    wanted_codes = set(INCOME_WANTED_REPORT_CODES)
    wanted_names = {fold_report_name(name) for name in INCOME_WANTED_REPORT_NAMES}
    picked: list[str] = []
    seen: set[str] = set()
    for item in available:
        if item.code in seen:
            continue
        if item.code in wanted_codes or fold_report_name(item.name) in wanted_names:
            seen.add(item.code)
            picked.append(item.code)
    return picked


def print_all_path(folder: Path, shop_name: str) -> Path:
    shop = "".join(" " if ch in '\\/:*?"<>|' else ch for ch in shop_name)
    shop = " ".join(shop.split()).rstrip(" .")
    return folder / INCOME_PRINT_ALL_NAME.format(shop=shop)


def _object(body: bytes) -> dict:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _data(body: bytes) -> list:
    parsed = _object(body).get("data")
    return parsed if isinstance(parsed, list) else []

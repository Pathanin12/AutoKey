from __future__ import annotations

import re

from constants.date_utils import format_express_pv_date, is_complete_express_date
from models.income_form_values import IncomeFormValues
from services.name_match_service import tidy_name
from services.pp30_amount_service import money_amounts

_TAX_INVOICE_MARK = "ใบกำกับภาษี"
_RECEIPT_MARK = "ใบเสร็จรับเงิน"
_TAX_ID_RE = re.compile(r"เลขประจำตัวผู้เสียภาษี\s*(\d{13})")
_TAX_ID_LOOSE_RE = re.compile(r"(?<!\d)(\d{13})(?!\d)")
_INVOICE_RE = re.compile(r"(?<!\d)(29\d{8,10})(?!\d)")
_BILL_RE = re.compile(r"(?<!\d)(60\d{8,12})(?!\d)")
_BRANCH_CODE_RE = re.compile(r"รหัสสาขา\s*(\d{5,8})")
_BRANCH_NO_RE = re.compile(r"สาขาที่\s*(\d{5,8})")
_HEAD_OFFICE_RE = re.compile(r"สำนักงานใหญ่\s*(\d{6,8})")
_DATE_RE = re.compile(r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{2,4})(?!\d)")
_COMPANY_PREFIXES = (
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญนิติบุคคล",
    "ห้างหุ้นส่วนสามัญ",
    "บริษัทจำกัดมหาชน",
    "บริษัท ",
    "บจก.",
    "หจก.",
    "บมจ.",
)


def is_rv_tax_invoice(text: str) -> bool:
    compact = (text or "").replace(" ", "")
    return _TAX_INVOICE_MARK in compact and _RECEIPT_MARK in compact


def extract_income_invoice(text: str) -> IncomeFormValues | None:
    if not is_rv_tax_invoice(text):
        return None
    totals = _totals(text)
    invoice_date = _invoice_date(text)
    invoice_number = _invoice_number(text)
    tax_id = _tax_id(text)
    branch = _branch_last5(text)
    company = _company_name(text)
    if totals is None or not invoice_date or not invoice_number or not tax_id or not branch or not company:
        return None
    total_amount, wht_amount, vat_amount = totals
    return IncomeFormValues(
        company_name=company,
        branch_last5=branch,
        invoice_date=invoice_date,
        invoice_number=invoice_number,
        tax_id=tax_id,
        total_amount=total_amount,
        wht_amount=wht_amount,
        vat_amount=vat_amount,
        bill_count=_bill_count(text),
    )


def _totals(text: str) -> tuple[float, float, float] | None:
    amounts = money_amounts(text)
    if len(amounts) >= 5:
        block = amounts[-5:]
        base, vat, with_vat, wht, total = block
        if abs(base + vat - with_vat) < 0.02 and abs(with_vat - wht - total) < 0.02:
            return total, wht, vat
    if len(amounts) >= 3:
        total = amounts[-1]
        wht = amounts[-2]
        vat = amounts[-4] if len(amounts) >= 4 else amounts[-3]
        if total > 0:
            return total, wht, vat
    return None


def _invoice_date(text: str) -> str:
    for match in _DATE_RE.finditer(text or ""):
        day, month, year = match.groups()
        raw = f"{int(day):02d}/{int(month):02d}/{year}"
        formatted = format_express_pv_date(raw)
        if is_complete_express_date(formatted):
            return formatted
    return ""


def _invoice_number(text: str) -> str:
    match = _INVOICE_RE.search(text or "")
    return match.group(1) if match else ""


def _tax_id(text: str) -> str:
    labeled = _TAX_ID_RE.findall(text or "")
    if labeled:
        return labeled[-1]
    loose = _TAX_ID_LOOSE_RE.findall(text or "")
    return loose[-1] if loose else ""


def _branch_last5(text: str) -> str:
    for pattern in (_BRANCH_CODE_RE, _BRANCH_NO_RE, _HEAD_OFFICE_RE):
        match = pattern.search(text or "")
        if match:
            digits = match.group(1)
            return digits[-5:] if len(digits) >= 5 else digits.zfill(5)
    return ""


def _bill_count(text: str) -> int:
    bills = _BILL_RE.findall(text or "")
    return max(1, len(bills))


def _company_name(text: str) -> str:
    for raw in (text or "").splitlines():
        line = tidy_name(raw).rstrip(" .")
        if any(line.startswith(prefix) for prefix in _COMPANY_PREFIXES):
            if "ซีพี ออลล์" in line or "ซีพีออลล์" in line:
                continue
            return line
    return ""

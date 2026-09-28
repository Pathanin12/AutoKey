from __future__ import annotations

import re

from constants.date_utils import format_express_pv_date, is_complete_express_date
from constants.routes import (
    INCOME_PAY_ADVANCE,
    INCOME_PAY_ADVANCE_ALT,
    INCOME_PAY_GOODS,
    INCOME_PAY_RENT,
    INCOME_RV_ADVANCE,
    INCOME_RV_GOODS,
    INCOME_RV_RENT,
    INCOME_RV_TAX,
)
from models.income_form_values import IncomeFormValues
from services.name_match_service import tidy_name
from services.pp30_amount_service import money_amounts

_TAX_INVOICE_MARK = "ใบกำกับภาษี"
_RECEIPT_MARK = "ใบเสร็จรับเงิน"
_PAY_FOR_RE = re.compile(r"ชำระค่า\s*[:：]?\s*(.+)")
_TAX_ID_RE = re.compile(r"เลขประจำตัวผู้เสียภาษี\s*(\d{13})")
_TAX_ID_LOOSE_RE = re.compile(r"(?<!\d)(\d{13})(?!\d)")
_INVOICE_RE = re.compile(r"(29\d{8})(?=\d{2}[./-]\d{2}[./-]\d{2,4}|\D|$)")
_RECEIPT_NUM_RE = re.compile(r"(28\d{8})(?=\d{2}[./-]\d{2}[./-]\d{2,4}|\D|$)")
_BILL_RE = re.compile(r"(?<!\d)(60\d{8,12})(?!\d)")
_BRANCH_CODE_RE = re.compile(r"รหัสสาขา\s*(\d{5,8})")
_BRANCH_NO_RE = re.compile(r"สาขาที่\s*(\d{5,8})")
_HEAD_OFFICE_RE = re.compile(r"สำนักงานใหญ่[^\d]{0,40}(\d{6,8})")
_BRANCH_ALONE_RE = re.compile(r"(?<!\d)(\d{7})(?!\d)")
_TAX_THEN_BRANCH_RE = re.compile(r"(\d{13})(\d{7})(?!\d)")
_DATE_RE = re.compile(r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{2,4})(?!\d)")
_INVOICE_THEN_DATE_RE = re.compile(
    r"29\d{8}\s*(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{2,4})"
)
_RECEIPT_THEN_DATE_RE = re.compile(
    r"28\d{8}\s*(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{2,4})"
)
_INVOICE_DATE_RE = re.compile(r"29\d{8}(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})")
_PERIOD_RE = re.compile(r"(?:ประจำเดือน|เดือน)\s*(\d{1,2})\s*[./:-]\s*(\d{2,4})")
_COMPANY_PREFIXES = (
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญนิติบุคคล",
    "ห้างหุ้นส่วนสามัญ",
    "บริษัทจำกัดมหาชน",
    "บริษัท ",
    "บจก.",
    "บจก",
    "หจก.",
    "หจก",
    "บมจ.",
    "บมจ",
)


def is_rv_tax_invoice(text: str) -> bool:
    compact = re.sub(r"\s+", "", _norm_thai(text))
    if _TAX_INVOICE_MARK in compact and _RECEIPT_MARK in compact:
        return True
    if "กำกับภาษี" in compact and "เสร็จรับเงิน" in compact:
        return True
    glued = _glue_digits(_norm_thai(text))
    if not (_invoice_number(glued) or _invoice_number(text)):
        return False
    tax_ids = _TAX_ID_LOOSE_RE.findall(glued) or _TAX_ID_LOOSE_RE.findall(text or "")
    return len(tax_ids) >= 1 and _totals(text) is not None


def _norm_thai(text: str) -> str:
    return (text or "").replace("\u0e4d\u0e32", "\u0e33")


def _glue_digits(text: str) -> str:
    return re.sub(r"(?<=\d)[ \t\u00a0]+(?=\d)", "", text or "")


def extract_income_values(text: str) -> IncomeFormValues | None:
    from services.income_pv_extract_service import extract_income_pv_receipt, extract_income_pv_tax

    found = extract_income_pv_tax(text) or extract_income_pv_receipt(text)
    if found:
        return found
    if _receipt_kind(text):
        return extract_income_receipt(text)
    return extract_income_invoice(text)


def extract_income_invoice(text: str) -> IncomeFormValues | None:
    text = _norm_thai(text)
    if not is_rv_tax_invoice(text):
        return None
    totals = _totals(text)
    glued = _glue_digits(text)
    invoice_date = _invoice_date(glued) or _invoice_date(text)
    invoice_number = _invoice_number(glued) or _invoice_number(text)
    tax_id = _tax_id(glued) or _tax_id(text)
    branch = _branch_last5(glued) or _branch_last5(text)
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
        bill_count=_bill_count(glued or text),
        kind=INCOME_RV_TAX,
        period_date=_period_date(text),
    )


def extract_income_receipt(text: str) -> IncomeFormValues | None:
    text = _norm_thai(text)
    kind = _receipt_kind(text)
    if kind is None:
        return None
    totals = _receipt_totals(text)
    glued = _glue_digits(text)
    invoice_date = _invoice_date(glued) or _invoice_date(text)
    invoice_number = (
        _invoice_number(glued)
        or _invoice_number(text)
        or _receipt_number(glued)
        or _receipt_number(text)
    )
    tax_id = _tax_id(glued) or _tax_id(text)
    branch = _branch_last5(glued) or _branch_last5(text)
    company = _company_name(text)
    if totals is None or not invoice_number or not tax_id or not branch or not company:
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
        bill_count=_bill_count(glued or text),
        kind=kind,
        period_date=_period_date(text),
    )


def is_rv_receipt_copy(text: str) -> bool:
    return _receipt_kind(text) is not None


def _receipt_kind(text: str) -> str | None:
    text = _norm_thai(text)
    compact = re.sub(r"\s+", "", text)
    if _RECEIPT_MARK not in compact and "เสร็จรับเงิน" not in compact:
        return None
    pay = _pay_for(text)
    blob = f"{pay} {text} {compact}"
    if INCOME_PAY_GOODS in blob:
        return INCOME_RV_GOODS
    if INCOME_PAY_ADVANCE in blob or INCOME_PAY_ADVANCE_ALT in blob:
        return INCOME_RV_ADVANCE
    if INCOME_PAY_RENT in blob:
        return INCOME_RV_RENT
    return None


def _pay_for(text: str) -> str:
    match = _PAY_FOR_RE.search(text or "")
    return tidy_name(match.group(1)) if match else ""


def _receipt_totals(text: str) -> tuple[float, float, float] | None:
    total = _amount_near(text, "รวมเงินทั้งสิ้น")
    wht = _amount_near(text, "หัก ณ ที่จ่าย") or _amount_near(text, "หัก ภาษีหัก ณ ที่จ่าย")
    vat = _amount_near(text, "ภาษีมูลค่าเพิ่ม")
    if total > 0:
        return total, wht, vat
    return _totals(text)


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


def _period_date(text: str) -> str:
    match = _PERIOD_RE.search(text or "")
    if not match:
        return ""
    month, year = match.groups()
    formatted = format_express_pv_date(f"01/{int(month):02d}/{year}")
    return formatted if is_complete_express_date(formatted) else ""


def _invoice_date(text: str) -> str:
    for pattern in (_RECEIPT_THEN_DATE_RE, _INVOICE_THEN_DATE_RE, _INVOICE_DATE_RE, _DATE_RE):
        for match in pattern.finditer(text or ""):
            day, month, year = match.groups()
            raw = f"{int(day):02d}/{int(month):02d}/{year}"
            formatted = format_express_pv_date(raw)
            if is_complete_express_date(formatted):
                return formatted
    return ""


def _invoice_number(text: str) -> str:
    match = _INVOICE_RE.search(text or "")
    return match.group(1) if match else ""


def _receipt_number(text: str) -> str:
    match = _RECEIPT_NUM_RE.search(text or "")
    return match.group(1) if match else ""


def _tax_id(text: str) -> str:
    labeled = _TAX_ID_RE.findall(text or "")
    if labeled:
        return labeled[-1]
    loose = _TAX_ID_LOOSE_RE.findall(text or "")
    return loose[-1] if loose else ""


def _branch_last5(text: str) -> str:
    for pattern in (_BRANCH_CODE_RE, _BRANCH_NO_RE):
        match = pattern.search(text or "")
        if match:
            digits = match.group(1)
            return digits[-5:] if len(digits) >= 5 else digits.zfill(5)
    pair = [item for item in _TAX_THEN_BRANCH_RE.findall(text or "") if item[0].startswith("0")]
    if pair:
        return pair[-1][1][-5:]
    tax_ids = set(_TAX_ID_LOOSE_RE.findall(text or ""))
    codes = [
        code
        for code in _BRANCH_ALONE_RE.findall(text or "")
        if not any(code in tax_id for tax_id in tax_ids)
    ]
    if codes:
        return codes[-1][-5:]
    match = _HEAD_OFFICE_RE.search(text or "")
    if match and len(match.group(1)) <= 7:
        return match.group(1)[-5:]
    return ""


def _bill_count(text: str) -> int:
    bills = _BILL_RE.findall(text or "")
    return max(1, len(bills))


def _company_name(text: str) -> str:
    for raw in (text or "").splitlines():
        found = _company_from_line(tidy_name(raw).rstrip(" ."))
        if found:
            return found
    return _company_from_line(tidy_name(text))


def _amount_near(text: str, label: str) -> float:
    index = (text or "").find(label)
    if index < 0:
        return 0.0
    amounts = money_amounts(text[index : index + 80])
    return amounts[0] if amounts else 0.0


def _company_from_line(line: str) -> str:
    for prefix in _COMPANY_PREFIXES:
        index = line.find(prefix)
        if index < 0:
            continue
        snippet = line[index:]
        for stop in ("สำนักงานใหญ่", "เลขประจำตัว", "ใบเสร็จรับเงิน"):
            cut = snippet.find(stop, len(prefix))
            if cut > 0:
                snippet = snippet[:cut]
        name = tidy_name(snippet).rstrip(" .")
        if not name or "ซีพี ออลล์" in name or "ซีพีออลล์" in name:
            continue
        return name
    return ""

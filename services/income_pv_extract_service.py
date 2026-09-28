from __future__ import annotations

import re

from constants.date_utils import format_express_pv_date, is_complete_express_date
from constants.routes import (
    INCOME_PV_DEPOSIT_MARK,
    INCOME_PV_RECEIPT,
    INCOME_PV_TAX,
    INCOME_PV_TAX_TITLE,
    INCOME_PV_TAX_TITLE_GLUED,
)
from models.income_form_values import IncomeFormValues
from services.income_extract_service import (
    _branch_last5,
    _company_name,
    _glue_digits,
    _invoice_date,
    _norm_thai,
    _period_date,
    _tax_id,
    shop_tax_id,
)
from services.name_match_service import tidy_name
from services.pp30_amount_service import eq_amount, money_amounts


_RECEIPT_MARK = "ใบเสร็จรับเงิน"
_CUSTOMER_RE = re.compile(r"รหัสลูกค้า[^\d]{0,80}(\d{7,8})")
_DOC_NUM_RE = re.compile(r"เลขที่\s*[:：]?\s*(\d{8,12})")
_PV_NUM_RE = re.compile(r"((?:26|27)\d{8})(?=\d{2}[./-]\d{2}[./-]\d{2,4}|\D|$)")
_TAX_ID_RE = re.compile(r"เลขประจำตัวผู้เสียภาษี\s*(\d{13})")
_PV_THEN_DATE_RE = re.compile(
    r"(?:26|27)\d{8}[^\d]{0,40}(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{2,4})"
)


def extract_income_pv_tax(text: str) -> IncomeFormValues | None:
    text = _norm_thai(text)
    if not is_cpall_pv_tax(text):
        return None
    glued = _glue_digits(text)
    invoice_number = _doc_number(glued) or _doc_number(text)
    invoice_date = _pv_doc_date(glued) or _pv_doc_date(text) or _invoice_date(glued) or _invoice_date(text)
    tax_id = _issuer_tax_id(text) or _tax_id(glued) or _tax_id(text)
    branch = _customer_branch(text) or _branch_last5(glued) or _branch_last5(text)
    company = _company_name(text)
    base_amount, vat_amount, wht_amount, pay_amount = _pv_amounts(text)
    if not invoice_date or not invoice_number or not tax_id or not branch or not company:
        return None
    if pay_amount <= 0 and base_amount <= 0:
        return None
    if pay_amount <= 0:
        pay_amount = round(base_amount + vat_amount - wht_amount, 2)
    return IncomeFormValues(
        company_name=company,
        branch_last5=branch,
        invoice_date=invoice_date,
        invoice_number=invoice_number,
        tax_id=tax_id,
        total_amount=pay_amount,
        wht_amount=wht_amount,
        vat_amount=vat_amount,
        bill_count=1,
        kind=INCOME_PV_TAX,
        period_date=_period_date(text),
        base_amount=base_amount,
        shop_tax_id=shop_tax_id(text),
    )


def is_cpall_pv_tax(text: str) -> bool:
    compact = re.sub(r"\s+", "", _norm_thai(text))
    if not _is_cpall_doc(compact):
        return False
    return _has_pv_tax_title(compact)


def is_cpall_pv_receipt(text: str) -> bool:
    compact = re.sub(r"\s+", "", _norm_thai(text))
    if not _is_cpall_doc(compact):
        return False
    if _has_pv_tax_title(compact):
        return False
    return _RECEIPT_MARK in compact or "เสร็จรับเงิน" in compact


def _has_pv_tax_title(compact: str) -> bool:
    if INCOME_PV_TAX_TITLE in compact or INCOME_PV_TAX_TITLE_GLUED in compact:
        return True
    upper = compact.upper()
    if "RECEIPT/TAXINVOICE" in upper or "RECEIPTTAXINVOICE" in upper or "TAXINVOICE" in upper:
        return True
    rest = compact.replace("สาขาที่ออกใบกำกับภาษี", "")
    return "ใบเสร็จรับเงิน" in compact and "ใบกำกับภาษี" in rest


def _is_cpall_doc(compact: str) -> bool:
    if "รหัสลูกค้า" not in compact:
        return False
    return "ซีพีออลล์" in compact or "CPALLPUBLIC" in compact.upper().replace(" ", "")


def _customer_branch(text: str) -> str:
    match = _CUSTOMER_RE.search(text or "")
    if not match:
        return ""
    digits = match.group(1)
    return digits[-5:] if len(digits) >= 5 else digits.zfill(5)


def _doc_number(text: str) -> str:
    match = _PV_NUM_RE.search(text or "")
    if match:
        return match.group(1)
    labeled = _DOC_NUM_RE.findall(text or "")
    return labeled[0] if labeled else ""


def _issuer_tax_id(text: str) -> str:
    labeled = _TAX_ID_RE.findall(text or "")
    return labeled[0] if labeled else ""


def _pv_doc_date(text: str) -> str:
    match = _PV_THEN_DATE_RE.search(text or "")
    if not match:
        return ""
    day, month, year = match.groups()
    formatted = format_express_pv_date(f"{int(day):02d}/{int(month):02d}/{year}")
    return formatted if is_complete_express_date(formatted) else ""


def _pv_amounts(text: str) -> tuple[float, float, float, float]:
    base = _amount_near(text, "ค่ารวม")
    vat = _amount_near(text, "บวก ภาษีมูลค่าเพิ่ม") or _amount_near(text, "บาก ภาษีมูลค่าเพิ่ม")
    wht = _amount_near(text, "หัก ณ ที่จ่าย") or _amount_near(text, "หัก ภาษีหัก ณ ที่จ่าย")
    pay = _amount_near(text, "จำนวนเงินที่ต้องชำระ") or _amount_near(text, "จำนวนเงินที่ชำระ")
    if base > 0 and pay > 0:
        if vat <= 0:
            vat = _amount_near(text, "ภาษีมูลค่าเพิ่ม")
        return base, vat, wht, pay
    stacked = _stacked_tax_totals(text)
    if stacked:
        return stacked
    if vat <= 0:
        vat = _amount_near(text, "ภาษีมูลค่าเพิ่ม")
    if base <= 0:
        base = _amount_near(text, "รวม (บาท)")
    return base, vat, wht, pay


def _stacked_tax_totals(text: str) -> tuple[float, float, float, float] | None:
    index = (text or "").find("รวม (บาท)")
    if index < 0:
        index = (text or "").find("รวม(บาท)")
    if index < 0:
        return None
    amounts = money_amounts(text[index:])
    for i in range(len(amounts) - 4):
        base, vat, included, wht, pay = amounts[i : i + 5]
        if eq_amount(base + vat, included) and eq_amount(included - wht, pay):
            return base, vat, wht, pay
    return None


def _amount_near(text: str, label: str) -> float:
    index = (text or "").find(label)
    if index < 0:
        return 0.0
    amounts = money_amounts(text[index : index + 80])
    return amounts[0] if amounts else 0.0


def extract_income_pv_receipt(text: str) -> IncomeFormValues | None:
    text = _norm_thai(text)
    if not is_cpall_pv_receipt(text):
        return None
    glued = _glue_digits(text)
    invoice_number = _doc_number(glued) or _doc_number(text)
    invoice_date = _pv_doc_date(glued) or _pv_doc_date(text) or _invoice_date(glued) or _invoice_date(text)
    tax_id = _issuer_tax_id(text) or _tax_id(glued) or _tax_id(text)
    branch = _customer_branch(text) or _branch_last5(glued) or _branch_last5(text)
    company = _company_name(text)
    deposit_amount, install_amount = _receipt_splits(text)
    pay_amount = _amount_near(text, "จำนวนเงินที่ชำระ") or _amount_near(text, "จำนวนเงินที่ต้องชำระ")
    if pay_amount <= 0:
        pay_amount = round(deposit_amount + install_amount, 2)
    if not invoice_date or not invoice_number or not tax_id or not branch or not company:
        return None
    if pay_amount <= 0 and deposit_amount <= 0 and install_amount <= 0:
        return None
    return IncomeFormValues(
        company_name=company,
        branch_last5=branch,
        invoice_date=invoice_date,
        invoice_number=invoice_number,
        tax_id=tax_id,
        total_amount=pay_amount,
        wht_amount=0.0,
        vat_amount=0.0,
        bill_count=1,
        kind=INCOME_PV_RECEIPT,
        period_date=_period_date(text),
        base_amount=install_amount,
        deposit_amount=deposit_amount,
    )


def _receipt_splits(text: str) -> tuple[float, float]:
    deposit = 0.0
    install = 0.0
    for desc, amount in _receipt_items(text):
        if INCOME_PV_DEPOSIT_MARK in desc:
            deposit = round(deposit + amount, 2)
        else:
            install = round(install + amount, 2)
    return deposit, install


def _receipt_items(text: str) -> list[tuple[str, float]]:
    started = False
    pending: list[str] = []
    items: list[tuple[str, float]] = []
    for raw in (text or "").splitlines():
        line = tidy_name(raw)
        compact = re.sub(r"\s+", "", line)
        if "ชำระค่า" in compact:
            started = True
            rest = re.split(r"ชำระค่า\s*[:：]?", line, maxsplit=1)
            extra = tidy_name(rest[1]) if len(rest) > 1 else ""
            if extra and extra.lower() not in ("amount", "จำนวนเงิน"):
                pending.append(extra)
            continue
        if not started:
            continue
        if any(mark in compact for mark in ("รวม(บาท)", "รวมบาท", "หักณที่จ่าย", "จำนวนเงินที่ชำระ")):
            break
        if not compact or compact.lower() in ("amount", "description", "จำนวนเงิน"):
            continue
        if re.fullmatch(r"\d{1,3}", compact) or re.fullmatch(r"\d{8,12}", compact):
            continue
        if _is_date_line(line) and not re.search(r"[ก-๙A-Za-z]", line):
            continue
        amounts = money_amounts(line)
        has_text = bool(re.search(r"[ก-๙A-Za-z]", line))
        if amounts and has_text:
            items.append((line, amounts[-1]))
            pending = []
        elif amounts:
            for amount in amounts:
                if pending:
                    items.append((pending.pop(0), amount))
        elif has_text:
            pending.append(line)
    return items


def _is_date_line(line: str) -> bool:
    formatted = format_express_pv_date(line)
    return is_complete_express_date(formatted)

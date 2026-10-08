from __future__ import annotations

import re

from constants.date_utils import format_express_pv_date
from services.pnd30_extract_service import extract_pv_date
from services.pp30_amount_service import line_money

_EMPLOYER_LABEL = "เงินสมทบนายจ้าง"
_EMPLOYEE_LABEL = "เงินสมทบผู้ประกันตน"
_PENALTY_LABELS = ("เงินเพิ่มตามกฏหมาย", "เงินเพิ่มตามกฎหมาย")
_PAID_LABEL = "จำนวนเงินที่ชำระ"
_RECEIPT_RE = re.compile(r"เลขที่ใบเสร็จรับเงิน[.\s]*([A-Za-z0-9]+)")
_SSO_DATE_RE = re.compile(
    r"วันที่(?:ชำระเงิน|ออกใบเสร็จรับเงิน)[.\s]*(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{2,4})"
)


def extract_sso_values(text: str) -> tuple[float, float, float] | None:
    employer = _labeled_amount(text, (_EMPLOYER_LABEL,))
    employee = _labeled_amount(text, (_EMPLOYEE_LABEL,))
    contrib = round((employer or 0.0) + (employee or 0.0), 2)
    penalty = _labeled_amount(text, _PENALTY_LABELS, allow_zero=True)
    paid = _labeled_amount(text, (_PAID_LABEL,))
    if contrib <= 0 and (penalty is None or penalty <= 0) and (paid is None or paid <= 0):
        return None
    return contrib, 0.0 if penalty is None else penalty, 0.0 if paid is None else paid


def extract_sso_date(text: str) -> str:
    match = _SSO_DATE_RE.search(text or "")
    if match:
        day, month, year = match.groups()
        return format_express_pv_date(f"{int(day):02d}/{int(month):02d}/{year}")
    return extract_pv_date(text)


def extract_sso_receipt_no(text: str) -> str:
    match = _RECEIPT_RE.search(text or "")
    return (match.group(1) if match else "").strip().upper()


def _labeled_amount(text: str, labels: tuple[str, ...], *, allow_zero: bool = False) -> float | None:
    lines = (text or "").splitlines()
    for index, raw in enumerate(lines):
        if not any(label in raw for label in labels):
            continue
        amount = line_money(raw, allow_zero=allow_zero)
        if amount is not None:
            return amount
        for nxt in lines[index + 1 : index + 4]:
            amount = line_money(nxt, allow_zero=allow_zero)
            if amount is not None:
                return amount
    return None

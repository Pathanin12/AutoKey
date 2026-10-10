from __future__ import annotations

from constants.routes import (
    ACCOUNT_BT40_LOAN,
    ACCOUNT_BT40_TAX,
    ACCOUNT_CASH,
    ACCOUNT_PP30_DECIMAL,
    ACCOUNT_PP30_PENALTY,
    JNLTYP_PV,
    JNLTYP_RV,
    VOUCHER_PV_PREFIX,
    VOUCHER_RV_PREFIX,
)
from models.bt40_form_values import Bt40FormValues
from models.journal_voucher import JournalLine, JournalVoucher
from services.pp30_amount_service import has_amount


def _debit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=False)


def _credit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=True)


def rv_bt40(values: Bt40FormValues, date: str, description: str) -> JournalVoucher:
    lines: list[JournalLine] = []
    if has_amount(values.line7_receipt):
        lines.append(_debit(ACCOUNT_CASH, values.line7_receipt))
        lines.append(_credit(ACCOUNT_BT40_LOAN, values.line7_receipt))
    return JournalVoucher(
        jnltyp=JNLTYP_RV,
        prefix=VOUCHER_RV_PREFIX,
        voudat_express=date,
        description=description,
        lines=[line for line in lines if has_amount(line.amount)],
    )


def pv_bt40(values: Bt40FormValues, date: str, description: str) -> JournalVoucher:
    lines: list[JournalLine] = []
    if has_amount(values.tax_amount):
        lines.append(_debit(ACCOUNT_BT40_TAX, values.tax_amount))
    if has_amount(values.penalty_amount):
        lines.append(_debit(ACCOUNT_PP30_PENALTY, values.penalty_amount))
    if has_amount(values.line17_integer):
        lines.append(_credit(ACCOUNT_CASH, values.line17_integer))
    if has_amount(values.line17_decimal):
        lines.append(_credit(ACCOUNT_PP30_DECIMAL, values.line17_decimal))
    return JournalVoucher(
        jnltyp=JNLTYP_PV,
        prefix=VOUCHER_PV_PREFIX,
        voudat_express=date,
        description=description,
        lines=[line for line in lines if has_amount(line.amount)],
    )

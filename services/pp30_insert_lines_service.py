from __future__ import annotations

from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_PP30_DECIMAL,
    ACCOUNT_PP30_NEW_SHOP,
    ACCOUNT_PP30_PENALTY,
    ACCOUNT_PP30_VAT_PAYABLE,
    ACCOUNT_PP30_VAT_PURCHASE,
    ACCOUNT_PP30_VAT_SALE,
    JNLTYP_JV,
    JNLTYP_PV,
    VOUCHER_JV_PREFIX,
    VOUCHER_PV_PREFIX,
)
from models.journal_voucher import JournalLine, JournalVoucher
from models.pp30_form_values import Pp30FormValues
from services.pp30_amount_service import eq_amount, has_amount


def _debit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=False)


def _credit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=True)


def _remainder(debits: list[JournalLine], credits: list[JournalLine]) -> float:
    return round(sum(line.amount for line in debits) - sum(line.amount for line in credits), 2)


def _voucher(jnltyp: str, prefix: str, date: str, description: str, lines: list[JournalLine]) -> JournalVoucher:
    return JournalVoucher(
        jnltyp=jnltyp,
        prefix=prefix,
        voudat_express=date,
        description=description,
        lines=[line for line in lines if has_amount(line.amount)],
    )


def jv_normal(values: Pp30FormValues, date: str, description: str) -> JournalVoucher:
    debits: list[JournalLine] = []
    credits: list[JournalLine] = []
    if values.has_line_5:
        debits.append(_debit(ACCOUNT_PP30_VAT_SALE, values.line_5))
    if values.has_line_7:
        credits.append(_credit(ACCOUNT_PP30_VAT_PURCHASE, values.line_7))
    rest = _remainder(debits, credits)
    if has_amount(rest):
        credits.append(_credit(ACCOUNT_PP30_VAT_PAYABLE, rest))
    return _voucher(JNLTYP_JV, VOUCHER_JV_PREFIX, date, description, debits + credits)


def jv_pay(values: Pp30FormValues, date: str, description: str) -> JournalVoucher:
    debits: list[JournalLine] = []
    credits: list[JournalLine] = []
    if values.has_line_5:
        debits.append(_debit(ACCOUNT_PP30_VAT_SALE, values.line_5))
    if values.has_line_7:
        credits.append(_credit(ACCOUNT_PP30_VAT_PURCHASE, values.line_7))
    if values.has_line_10:
        credits.append(_credit(ACCOUNT_PP30_NEW_SHOP, values.line_10))
    rest = _remainder(debits, credits)
    if has_amount(rest):
        credits.append(_credit(ACCOUNT_PP30_VAT_PAYABLE, rest))
    return _voucher(JNLTYP_JV, VOUCHER_JV_PREFIX, date, description, debits + credits)


def jv_no_pay_normal(values: Pp30FormValues, date: str, description: str) -> JournalVoucher:
    debits: list[JournalLine] = []
    credits: list[JournalLine] = []
    if values.has_line_5:
        debits.append(_debit(ACCOUNT_PP30_VAT_SALE, values.line_5))
    if values.has_line_7:
        credits.append(_credit(ACCOUNT_PP30_VAT_PURCHASE, values.line_7))
    rest = _remainder(debits, credits)
    if has_amount(rest):
        credits.append(_credit(ACCOUNT_PP30_NEW_SHOP, rest))
    return _voucher(JNLTYP_JV, VOUCHER_JV_PREFIX, date, description, debits + credits)


def jv_new_shop(values: Pp30FormValues, date: str, description: str) -> JournalVoucher:
    purchase = values.line_7
    return _voucher(
        JNLTYP_JV,
        VOUCHER_JV_PREFIX,
        date,
        description,
        [_debit(ACCOUNT_PP30_NEW_SHOP, purchase), _credit(ACCOUNT_PP30_VAT_PURCHASE, purchase)],
    )


def pv_pay_or_normal(values: Pp30FormValues, date: str, description: str) -> JournalVoucher:
    due = values.line_11
    decimal_amount = values.amount_due_decimal if values.has_amount_due_decimal else 0.0
    cash = round(due - decimal_amount, 2)
    lines = [_debit(ACCOUNT_PP30_VAT_PAYABLE, due)]
    if has_amount(decimal_amount):
        lines.append(_credit(ACCOUNT_PP30_DECIMAL, decimal_amount))
    if has_amount(cash):
        lines.append(_credit(ACCOUNT_CASH, cash))
    return _voucher(JNLTYP_PV, VOUCHER_PV_PREFIX, date, description, lines)


def pv_penalty(values: Pp30FormValues, date: str, description: str) -> JournalVoucher:
    due = _penalty_line_11(values)
    penalty = values.penalty_amount
    decimal_amount = values.line_15_decimal if values.has_line_15_decimal else 0.0
    cash = round(due + penalty - decimal_amount, 2)
    lines = [_debit(ACCOUNT_PP30_VAT_PAYABLE, due)]
    if has_amount(penalty):
        lines.append(_debit(ACCOUNT_PP30_PENALTY, penalty))
    if has_amount(decimal_amount):
        lines.append(_credit(ACCOUNT_PP30_DECIMAL, decimal_amount))
    if has_amount(cash):
        lines.append(_credit(ACCOUNT_CASH, cash))
    return _voucher(JNLTYP_PV, VOUCHER_PV_PREFIX, date, description, lines)


def _penalty_line_11(values: Pp30FormValues) -> float:
    if eq_amount(values.line_11, values.line_15) and has_amount(values.penalty_amount):
        return round(values.line_15 - values.penalty_amount, 2)
    return values.line_11

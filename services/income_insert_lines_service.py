from __future__ import annotations

from constants.routes import (
    ACCOUNT_INCOME,
    ACCOUNT_INCOME_ADVANCE,
    ACCOUNT_INCOME_GOODS,
    ACCOUNT_INCOME_RECEIVABLE,
    ACCOUNT_INCOME_RENT,
    ACCOUNT_INCOME_WHT,
    ACCOUNT_PP30_VAT_SALE,
    INCOME_RV_ADVANCE,
    INCOME_RV_GOODS,
    INCOME_RV_RENT,
    JNLTYP_RV,
    VOUCHER_RV_PREFIX,
)
from models.income_form_values import IncomeFormValues
from models.journal_voucher import JournalLine, JournalVoucher
from services.pp30_amount_service import has_amount


def _debit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=False)


def _credit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=True)


def rv_income(values: IncomeFormValues, date: str, description: str) -> JournalVoucher:
    if values.kind == INCOME_RV_GOODS:
        lines = _receipt_lines(values, ACCOUNT_INCOME_GOODS)
    elif values.kind == INCOME_RV_RENT:
        lines = _receipt_lines(values, ACCOUNT_INCOME_RENT)
    elif values.kind == INCOME_RV_ADVANCE:
        lines = _advance_lines(values)
    else:
        lines = _tax_lines(values)
    return JournalVoucher(
        jnltyp=JNLTYP_RV,
        prefix=VOUCHER_RV_PREFIX,
        voudat_express=date,
        description=description,
        lines=lines,
    )


def _tax_lines(values: IncomeFormValues) -> list[JournalLine]:
    debits: list[JournalLine] = []
    credits: list[JournalLine] = []
    if has_amount(values.total_amount):
        debits.append(_debit(ACCOUNT_INCOME_RECEIVABLE, values.total_amount))
    if has_amount(values.wht_amount):
        debits.append(_debit(ACCOUNT_INCOME_WHT, values.wht_amount))
    if has_amount(values.vat_amount):
        credits.append(_credit(ACCOUNT_PP30_VAT_SALE, values.vat_amount))
    rest = round(sum(line.amount for line in debits) - sum(line.amount for line in credits), 2)
    if has_amount(rest):
        credits.append(_credit(ACCOUNT_INCOME, rest))
    return [line for line in debits + credits if has_amount(line.amount)]


def _receipt_lines(values: IncomeFormValues, credit_account: str) -> list[JournalLine]:
    lines: list[JournalLine] = []
    if has_amount(values.total_amount):
        lines.append(_debit(ACCOUNT_INCOME_RECEIVABLE, values.total_amount))
    if has_amount(values.wht_amount):
        lines.append(_debit(ACCOUNT_INCOME_WHT, values.wht_amount))
    rest = round(sum(line.amount for line in lines), 2)
    if has_amount(rest):
        lines.append(_credit(credit_account, rest))
    return lines


def _advance_lines(values: IncomeFormValues) -> list[JournalLine]:
    lines: list[JournalLine] = []
    if has_amount(values.total_amount):
        lines.append(_debit(ACCOUNT_INCOME_RECEIVABLE, values.total_amount))
        lines.append(_credit(ACCOUNT_INCOME_ADVANCE, values.total_amount))
    return lines

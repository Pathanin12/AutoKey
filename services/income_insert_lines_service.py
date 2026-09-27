from __future__ import annotations

from constants.routes import (
    ACCOUNT_INCOME,
    ACCOUNT_INCOME_RECEIVABLE,
    ACCOUNT_INCOME_WHT,
    ACCOUNT_PP30_VAT_SALE,
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
    return JournalVoucher(
        jnltyp=JNLTYP_RV,
        prefix=VOUCHER_RV_PREFIX,
        voudat_express=date,
        description=description,
        lines=[line for line in debits + credits if has_amount(line.amount)],
    )

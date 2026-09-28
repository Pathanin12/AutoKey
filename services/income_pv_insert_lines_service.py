from __future__ import annotations

from constants.routes import (
    ACCOUNT_INCOME_ADVANCE,
    ACCOUNT_INCOME_DEPOSIT,
    ACCOUNT_INCOME_RECEIVABLE,
    ACCOUNT_VAT,
    ACCOUNT_WT,
    JNLTYP_PV,
    VOUCHER_PV_PREFIX,
)
from models.income_form_values import IncomeFormValues
from models.journal_voucher import JournalLine, JournalVoucher
from services.pp30_amount_service import has_amount


def _debit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=False)


def _credit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=True)


def pv_income_tax(values: IncomeFormValues, date: str, description: str) -> JournalVoucher:
    lines: list[JournalLine] = []
    if has_amount(values.base_amount):
        lines.append(_debit(ACCOUNT_INCOME_ADVANCE, values.base_amount))
    if has_amount(values.vat_amount):
        lines.append(_debit(ACCOUNT_VAT, values.vat_amount))
    if has_amount(values.wht_amount):
        lines.append(_credit(ACCOUNT_WT, values.wht_amount))
    if has_amount(values.total_amount):
        lines.append(_credit(ACCOUNT_INCOME_RECEIVABLE, values.total_amount))
    return JournalVoucher(
        jnltyp=JNLTYP_PV,
        prefix=VOUCHER_PV_PREFIX,
        voudat_express=date,
        description=description,
        lines=lines,
    )


def pv_income_receipt(values: IncomeFormValues, date: str, description: str) -> JournalVoucher:
    lines: list[JournalLine] = []
    if has_amount(values.deposit_amount):
        lines.append(_debit(ACCOUNT_INCOME_DEPOSIT, values.deposit_amount))
    if has_amount(values.base_amount):
        lines.append(_debit(ACCOUNT_INCOME_ADVANCE, values.base_amount))
    if has_amount(values.total_amount):
        lines.append(_credit(ACCOUNT_INCOME_RECEIVABLE, values.total_amount))
    return JournalVoucher(
        jnltyp=JNLTYP_PV,
        prefix=VOUCHER_PV_PREFIX,
        voudat_express=date,
        description=description,
        lines=lines,
    )

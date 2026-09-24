from __future__ import annotations

from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_SERVICE,
    ACCOUNT_VAT,
    ACCOUNT_WT,
    JNLTYP_PV,
    VOUCHER_PV_PREFIX,
)
from models.journal_voucher import JournalLine, JournalVoucher
from models.ka_tam_row import KaTamRow
from services.pp30_amount_service import has_amount


def _debit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=False)


def _credit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=True)


def pv_ka_tam(row: KaTamRow, date: str, description: str) -> JournalVoucher:
    debits: list[JournalLine] = []
    credits: list[JournalLine] = []
    if has_amount(row.service_amount):
        debits.append(_debit(ACCOUNT_SERVICE, row.service_amount))
    if has_amount(row.vat_amount):
        debits.append(_debit(ACCOUNT_VAT, row.vat_amount))
    if has_amount(row.wt_amount):
        credits.append(_credit(ACCOUNT_WT, row.wt_amount))
    rest = round(sum(line.amount for line in debits) - sum(line.amount for line in credits), 2)
    if has_amount(rest):
        credits.append(_credit(ACCOUNT_CASH, rest))
    lines = [line for line in debits + credits if has_amount(line.amount)]
    return JournalVoucher(
        jnltyp=JNLTYP_PV,
        prefix=VOUCHER_PV_PREFIX,
        voudat_express=date,
        description=description,
        lines=lines,
    )

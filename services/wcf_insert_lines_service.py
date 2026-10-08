from __future__ import annotations

from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_WCF_CONTRIB,
    ACCOUNT_WCF_PENALTY,
    JNLTYP_PV,
    VOUCHER_PV_PREFIX,
)
from models.journal_voucher import JournalLine, JournalVoucher
from models.wcf_row import WcfRow
from services.pp30_amount_service import has_amount


def _debit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=False)


def _credit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=True)


def pv_wcf(row: WcfRow, date: str, description: str) -> JournalVoucher:
    lines: list[JournalLine] = []
    if has_amount(row.contrib_amount):
        lines.append(_debit(ACCOUNT_WCF_CONTRIB, row.contrib_amount))
    if has_amount(row.surcharge):
        lines.append(_debit(ACCOUNT_WCF_PENALTY, row.surcharge))
    cash = row.paid_amount if has_amount(row.paid_amount) else round(
        sum(line.amount for line in lines), 2
    )
    if has_amount(cash):
        lines.append(_credit(ACCOUNT_CASH, cash))
    return JournalVoucher(
        jnltyp=JNLTYP_PV,
        prefix=VOUCHER_PV_PREFIX,
        voudat_express=date,
        description=description,
        lines=[line for line in lines if has_amount(line.amount)],
    )

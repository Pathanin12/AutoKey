from __future__ import annotations

from constants.routes import ACCOUNT_CASH, ACCOUNT_PP30_PENALTY, ACCOUNT_WT_PND3, JNLTYP_PV, VOUCHER_PV_PREFIX
from models.journal_voucher import JournalLine, JournalVoucher
from models.pnd3_form_values import Pnd3FormValues
from services.pp30_amount_service import has_amount


def _debit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=False)


def _credit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=True)


def pv_pnd3(values: Pnd3FormValues, date: str, description: str) -> JournalVoucher:
    debits: list[JournalLine] = []
    if has_amount(values.tax_withheld):
        debits.append(_debit(ACCOUNT_WT_PND3, values.tax_withheld))
    if has_amount(values.surcharge):
        debits.append(_debit(ACCOUNT_PP30_PENALTY, values.surcharge))
    rest = round(sum(line.amount for line in debits), 2)
    lines = list(debits)
    if has_amount(rest):
        lines.append(_credit(ACCOUNT_CASH, rest))
    return JournalVoucher(
        jnltyp=JNLTYP_PV,
        prefix=VOUCHER_PV_PREFIX,
        voudat_express=date,
        description=description,
        lines=[line for line in lines if has_amount(line.amount)],
    )

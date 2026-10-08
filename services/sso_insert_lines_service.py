from __future__ import annotations

from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_SSO_CONTRIB,
    ACCOUNT_SSO_PENALTY,
    JNLTYP_PV,
    VOUCHER_PV_PREFIX,
)
from models.journal_voucher import JournalLine, JournalVoucher
from models.sso_form_values import SsoFormValues
from services.pp30_amount_service import has_amount


def _debit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=False)


def _credit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=True)


def pv_sso(values: SsoFormValues, date: str, description: str) -> JournalVoucher:
    lines: list[JournalLine] = []
    if has_amount(values.contrib_amount):
        lines.append(_debit(ACCOUNT_SSO_CONTRIB, values.contrib_amount))
    if has_amount(values.surcharge):
        lines.append(_debit(ACCOUNT_SSO_PENALTY, values.surcharge))
    cash = values.paid_amount if has_amount(values.paid_amount) else round(
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

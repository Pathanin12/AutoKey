from __future__ import annotations

from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_PP30_PENALTY,
    ACCOUNT_WT_PND2,
    JNLTYP_PV,
    VOUCHER_PV_PREFIX,
)
from models.journal_voucher import JournalLine, JournalVoucher
from models.pnd2_form_values import Pnd2FormValues
from services.pp30_amount_service import has_amount

_LINE_ORDER = (
    ACCOUNT_WT_PND2,
    ACCOUNT_PP30_PENALTY,
    ACCOUNT_CASH,
)


def _debit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=False)


def _credit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=True)


def _sorted(lines: list[JournalLine]) -> list[JournalLine]:
    rank = {account: index for index, account in enumerate(_LINE_ORDER)}
    return sorted(lines, key=lambda line: rank.get(line.account, len(rank)))


def pv_pnd2(values: Pnd2FormValues, date: str, description: str) -> JournalVoucher:
    lines: list[JournalLine] = []
    if has_amount(values.tax_withheld):
        lines.append(_debit(ACCOUNT_WT_PND2, values.tax_withheld))
    if has_amount(values.surcharge):
        lines.append(_debit(ACCOUNT_PP30_PENALTY, values.surcharge))
    rest = round(sum(line.amount for line in lines), 2)
    if has_amount(rest):
        lines.append(_credit(ACCOUNT_CASH, rest))
    return JournalVoucher(
        jnltyp=JNLTYP_PV,
        prefix=VOUCHER_PV_PREFIX,
        voudat_express=date,
        description=description,
        lines=_sorted([line for line in lines if has_amount(line.amount)]),
    )

from __future__ import annotations

from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_PAYROLL_SALARY,
    ACCOUNT_PAYROLL_SSO10,
    ACCOUNT_PAYROLL_SSO5,
    ACCOUNT_PAYROLL_WELFARE,
    ACCOUNT_PAYROLL_WELFARE025,
    ACCOUNT_WT_PND1,
    JNLTYP_PV,
    VOUCHER_PV_PREFIX,
)
from models.journal_voucher import JournalLine, JournalVoucher
from models.payroll_row import PayrollRow
from services.pp30_amount_service import has_amount


def _debit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=False)


def _credit(account: str, amount: float) -> JournalLine:
    return JournalLine(account=account, amount=round(amount, 2), is_credit=True)


def pv_payroll(row: PayrollRow, date: str, description: str) -> JournalVoucher:
    lines: list[JournalLine] = []
    if has_amount(row.salary):
        lines.append(_debit(ACCOUNT_PAYROLL_SALARY, row.salary))
    if has_amount(row.sso5):
        lines.append(_debit(ACCOUNT_PAYROLL_SSO5, row.sso5))
    if has_amount(row.welfare025):
        lines.append(_debit(ACCOUNT_PAYROLL_WELFARE025, row.welfare025))
    if has_amount(row.sso10):
        lines.append(_credit(ACCOUNT_PAYROLL_SSO10, row.sso10))
    if has_amount(row.welfare):
        lines.append(_credit(ACCOUNT_PAYROLL_WELFARE, row.welfare))
    if has_amount(row.tax):
        lines.append(_credit(ACCOUNT_WT_PND1, row.tax))
    if has_amount(row.net):
        lines.append(_credit(ACCOUNT_CASH, row.net))
    return JournalVoucher(
        jnltyp=JNLTYP_PV,
        prefix=VOUCHER_PV_PREFIX,
        voudat_express=date,
        description=description,
        lines=lines,
    )

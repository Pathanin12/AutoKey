from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class JournalLine:
    account: str
    amount: float
    is_credit: bool


@dataclass
class JournalVoucher:
    jnltyp: str
    prefix: str
    voudat_express: str
    description: str
    lines: list[JournalLine] = field(default_factory=list)
    voucher: str = ""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressVatRecord:
    vatrec: str
    vatprd: str
    vatdat: str
    docdat: str
    docnum: str
    refnum: str
    descrp: str
    amt01: float
    vat01: float
    taxid: str
    docstat: str

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IncomePortalAccount:
    legal_name: str
    username: str
    password: str

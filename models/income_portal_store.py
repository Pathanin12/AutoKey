from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IncomePortalStore:
    store_id: str
    store_name: str

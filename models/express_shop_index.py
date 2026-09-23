from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressShopIndex:
    file_name: str
    shop_name: str

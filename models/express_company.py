from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExpressCompany:
    folder: Path
    shop_name: str

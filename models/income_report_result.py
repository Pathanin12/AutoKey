from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class IncomeReportResult:
    path: Path
    skipped_shops: list[str] = field(default_factory=list)

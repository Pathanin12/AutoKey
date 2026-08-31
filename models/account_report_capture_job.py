from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AccountReportCaptureJob:
    account_code: str
    start_date: str
    end_date: str
    output_file: Path

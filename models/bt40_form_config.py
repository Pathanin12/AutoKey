from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constants.date_utils import is_complete_express_date
from constants.routes import BT40_PV_DESCRIPTION, BT40_RV_DESCRIPTION, UI_TEXT
from models.bt40_form_values import Bt40FormValues
from models.bt40_voucher_mode import Bt40VoucherMode
from models.month_year_period import MonthYearPeriod


def _with_amendment(text: str, values: Bt40FormValues | None) -> str:
    if values is not None and values.is_amendment:
        return f"{text} เพิ่มเติม"
    return text


@dataclass
class Bt40FormConfig:
    pdf_folder: Path
    rv_date: str
    period: MonthYearPeriod
    pdf_files: list[Path] = field(default_factory=list)
    voucher_mode: Bt40VoucherMode = field(default_factory=Bt40VoucherMode.all)

    def rv_description(self, values: Bt40FormValues | None = None) -> str:
        return _with_amendment(BT40_RV_DESCRIPTION, values)

    def pv_description(self, values: Bt40FormValues | None = None) -> str:
        return _with_amendment(BT40_PV_DESCRIPTION.format(period=self.period.text), values)

    def validate(self) -> list[str]:
        errors: list[str] = []
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append(UI_TEXT["bt40_pdf_invalid"])
        elif not self.pdf_files:
            errors.append(UI_TEXT["bt40_pdf_none"])
        if not self.voucher_mode.is_valid:
            errors.append(UI_TEXT["bt40_mode_invalid"])
        if self.voucher_mode.include_rv and not is_complete_express_date(self.rv_date):
            errors.append(UI_TEXT["bt40_rv_date_invalid"])
        if not self.period.is_valid:
            errors.append(UI_TEXT["bt40_period_invalid"])
        return errors

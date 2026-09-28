from __future__ import annotations

from dataclasses import dataclass

from constants.routes import INCOME_SOURCE_IMAGE, INCOME_SOURCE_PDF, INCOME_SOURCES, UI_TEXT


@dataclass(frozen=True)
class IncomeSourceMode:
    key: str

    @staticmethod
    def parse(value: str) -> IncomeSourceMode:
        key = (value or "").strip()
        if key not in INCOME_SOURCES:
            return IncomeSourceMode(key=INCOME_SOURCE_PDF)
        return IncomeSourceMode(key=key)

    @property
    def is_image(self) -> bool:
        return self.key == INCOME_SOURCE_IMAGE

    @property
    def none_text(self) -> str:
        return UI_TEXT["income_image_none"] if self.is_image else UI_TEXT["income_pdf_none"]

    def total_text(self, count: int) -> str:
        key = "income_image_total" if self.is_image else "pp30_pdf_total"
        return UI_TEXT[key].format(count=count)

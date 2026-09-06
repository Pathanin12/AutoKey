from __future__ import annotations

from dataclasses import dataclass

from constants.routes import (
    PP30_MODE_NORMAL,
    PP30_MODE_SPECIAL,
    PP30_RUN_MODES,
    UI_TEXT,
)


@dataclass(frozen=True)
class Pp30RunMode:
    key: str

    @staticmethod
    def normal() -> Pp30RunMode:
        return Pp30RunMode(key=PP30_MODE_NORMAL)

    @staticmethod
    def special() -> Pp30RunMode:
        return Pp30RunMode(key=PP30_MODE_SPECIAL)

    @staticmethod
    def parse(value: str) -> Pp30RunMode:
        key = (value or "").strip() or PP30_MODE_NORMAL
        if key not in PP30_RUN_MODES:
            return Pp30RunMode.normal()
        return Pp30RunMode(key=key)

    @property
    def label(self) -> str:
        if self.key == PP30_MODE_SPECIAL:
            return UI_TEXT["pp30_mode_special"]
        return UI_TEXT["pp30_mode_normal"]

    @property
    def is_special(self) -> bool:
        return self.key == PP30_MODE_SPECIAL

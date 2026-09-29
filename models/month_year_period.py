from __future__ import annotations

import re
from dataclasses import dataclass

_SEPARATORS = re.compile(r"[/\-.\s]+")


@dataclass(frozen=True)
class MonthYearPeriod:
    month: int
    year: int

    @property
    def is_valid(self) -> bool:
        return 1 <= self.month <= 12 and 0 <= self.year <= 99

    @property
    def label(self) -> str:
        return f"{self.month:02d}/{self.year:02d}"

    @property
    def text(self) -> str:
        return f"{self.month}/{self.year:02d}"

    @staticmethod
    def mask(value: str) -> str:
        text = value or ""
        head, separator, tail = text.partition("/")
        head_digits = "".join(ch for ch in head if ch.isdigit())
        if separator and len(head_digits) == 1:
            head_digits = "0" + head_digits
        digits = head_digits + "".join(ch for ch in tail if ch.isdigit())
        if digits and digits[0] > "1":
            digits = "0" + digits
        if len(digits) >= 2 and not 1 <= int(digits[:2]) <= 12:
            digits = digits[:1]
        digits = digits[:4]
        if len(digits) > 2:
            return f"{digits[:2]}/{digits[2:]}"
        return digits

    @staticmethod
    def parse(value: str) -> MonthYearPeriod:
        text = (value or "").strip()
        chunks = [part for part in _SEPARATORS.split(text) if part]
        if len(chunks) == 2 and all(part.isdigit() for part in chunks):
            return MonthYearPeriod(month=int(chunks[0]), year=int(chunks[1]) % 100)
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) == 4:
            return MonthYearPeriod(month=int(digits[:2]), year=int(digits[2:]))
        return MonthYearPeriod(month=0, year=0)

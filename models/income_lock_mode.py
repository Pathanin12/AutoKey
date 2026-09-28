from __future__ import annotations

from dataclasses import dataclass

from constants.routes import INCOME_LOCK_MODES, INCOME_LOCK_NONE, INCOME_LOCK_PASSWORD


@dataclass(frozen=True)
class IncomeLockMode:
    key: str

    @staticmethod
    def parse(value: str) -> IncomeLockMode:
        key = (value or "").strip()
        if key not in INCOME_LOCK_MODES:
            return IncomeLockMode(key=INCOME_LOCK_NONE)
        return IncomeLockMode(key=key)

    @property
    def is_locked(self) -> bool:
        return self.key == INCOME_LOCK_PASSWORD

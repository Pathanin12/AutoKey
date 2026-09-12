from __future__ import annotations

from dataclasses import dataclass

from constants.routes import RUN_SPEED_100, RUN_SPEED_SCALES, RUN_SPEEDS


@dataclass(frozen=True)
class RunSpeed:
    key: str

    @staticmethod
    def default() -> RunSpeed:
        return RunSpeed(key=RUN_SPEED_100)

    @staticmethod
    def parse(value: str) -> RunSpeed:
        key = (value or "").strip() or RUN_SPEED_100
        if key not in RUN_SPEEDS:
            return RunSpeed.default()
        return RunSpeed(key=key)

    @property
    def label(self) -> str:
        return f"x{self.key}"

    @property
    def wait_scale(self) -> float:
        return RUN_SPEED_SCALES[self.key]

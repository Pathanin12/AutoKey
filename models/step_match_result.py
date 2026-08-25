from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StepMatchResult:
    found: bool
    score: float
    x: int
    y: int
    width: int
    height: int

    @property
    def rect(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height

    def contains(self, point_x: int, point_y: int) -> bool:
        return self.x <= point_x < self.x + self.width and self.y <= point_y < self.y + self.height

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2

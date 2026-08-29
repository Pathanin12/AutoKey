from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressEditTarget:
    hwnd: int
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def center_y(self) -> float:
        return (self.top + self.bottom) / 2

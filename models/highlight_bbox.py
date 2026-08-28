from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HighlightBBox:
    x: int
    y: int
    width: int
    height: int
    confidence: float = 0.0

    @property
    def x1(self) -> int:
        return self.x + self.width

    @property
    def y1(self) -> int:
        return self.y + self.height

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.width / 2.0, self.y + self.height / 2.0

    def contains_point(self, x: float, y: float, *, padding: int = 0) -> bool:
        return (
            self.x - padding <= x <= self.x1 + padding
            and self.y - padding <= y <= self.y1 + padding
        )

    def expand(self, *, pad_x: int = 0, pad_y: int = 0, max_w: int | None = None, max_h: int | None = None) -> HighlightBBox:
        x0 = max(0, self.x - pad_x)
        y0 = max(0, self.y - pad_y)
        x1 = self.x1 + pad_x
        y1 = self.y1 + pad_y
        if max_w is not None:
            x1 = min(x1, max_w)
        if max_h is not None:
            y1 = min(y1, max_h)
        return HighlightBBox(x0, y0, max(1, x1 - x0), max(1, y1 - y0), self.confidence)

    def as_tuple(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScreenRegion:
    x: int
    y: int
    width: int
    height: int
    label: str = ""

    def scaled(self, screen_width: int, screen_height: int, base_width: int = 1920, base_height: int = 1080) -> ScreenRegion:
        return ScreenRegion(
            x=int(self.x * screen_width / base_width),
            y=int(self.y * screen_height / base_height),
            width=max(int(self.width * screen_width / base_width), 40),
            height=max(int(self.height * screen_height / base_height), 24),
            label=self.label,
        )

    def padded(self, padding: int = 8) -> ScreenRegion:
        return ScreenRegion(
            x=max(self.x - padding, 0),
            y=max(self.y - padding, 0),
            width=self.width + padding * 2,
            height=self.height + padding * 2,
            label=self.label,
        )

    @classmethod
    def from_match(cls, x: int, y: int, width: int, height: int, label: str = "") -> ScreenRegion:
        return cls(x=x, y=y, width=width, height=height, label=label).padded()

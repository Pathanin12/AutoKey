from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants.routes import TEMPLATES_DIR


@dataclass(frozen=True)
class TemplateTarget:
    step_id: str
    label: str
    template_file: str
    match_threshold: float = 0.82
    crop_x: int = 0
    crop_y: int = 0
    crop_width: int | None = None
    crop_height: int | None = None

    @property
    def template_path(self) -> Path:
        return TEMPLATES_DIR / self.template_file

    def crop_box(self) -> tuple[int, int, int, int] | None:
        if self.crop_width is None or self.crop_height is None:
            return None
        return (
            self.crop_x,
            self.crop_y,
            self.crop_x + self.crop_width,
            self.crop_y + self.crop_height,
        )

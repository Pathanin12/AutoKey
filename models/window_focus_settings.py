from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowFocusSettings:
    enabled: bool = True
    title_contains: str = "Express"
    prepare_seconds: float = 0.3
    wait_after_focus_seconds: float = 0.5
    required: bool = True

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LookupOcrCheck:
    expected: str
    actual: str
    similarity: float

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TopicMenuItem:
    id: str
    title: str
    hint: str
    page_route: str
    enabled: bool = True

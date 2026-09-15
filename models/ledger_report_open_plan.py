from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LedgerReportOpenPlan:
    expand_tree: bool

    @property
    def after_f12_keys(self) -> tuple[str, ...]:
        if self.expand_tree:
            return ("5", "4", "1")
        return ("1",)

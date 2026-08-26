from __future__ import annotations

from dataclasses import dataclass

from models.template_target import TemplateTarget


@dataclass(frozen=True)
class TemplateClickAction:
    action_id: str
    target: TemplateTarget
    search_region: tuple[int, int, int, int] | None = None


@dataclass(frozen=True)
class TemplateClickSettings:
    enabled: bool = True
    fallback_to_keyboard: bool = True
    actions: tuple[TemplateClickAction, ...] = ()

    def get_action(self, action_id: str) -> TemplateClickAction:
        for action in self.actions:
            if action.action_id == action_id:
                return action
        raise KeyError(f"ไม่พบ template action: {action_id}")

"""ปุ่มที่ AutoKey จับภาพแล้วคลิกบน Express จริง"""

from __future__ import annotations

from models.template_click_settings import TemplateClickAction
from models.template_target import TemplateTarget

LOOKUP_SEARCH_TARGET = TemplateTarget(
    step_id="lookup_search",
    label="ปุ่ม ค้นหา",
    template_file="btn_search.png",
    match_threshold=0.88,
)

LOOKUP_OK_TARGET = TemplateTarget(
    step_id="lookup_ok",
    label="ปุ่ม ตกลง",
    template_file="btn_ok.png",
    match_threshold=0.88,
)

COMPANY_DIALOG_REGION = (580, 520, 990, 670)

DEFAULT_TEMPLATE_CLICK_ACTIONS: tuple[TemplateClickAction, ...] = (
    TemplateClickAction(
        action_id="lookup_search",
        target=LOOKUP_SEARCH_TARGET,
        search_region=COMPANY_DIALOG_REGION,
    ),
    TemplateClickAction(
        action_id="lookup_ok",
        target=LOOKUP_OK_TARGET,
        search_region=COMPANY_DIALOG_REGION,
    ),
)

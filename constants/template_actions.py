"""ปุ่มที่ AutoKey จับภาพแล้วคลิกบน Express จริง"""

from __future__ import annotations

from constants.routes import (
    MENU_ACCOUNT_REPORT_LABEL,
    MENU_GENERAL_LEDGER_LABEL,
    MENU_REPORT_NORMAL_LABEL,
)
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

MENU_BAR_REGION = (80, 0, 980, 90)
MENU_DROPDOWN_REGION = (80, 40, 720, 480)
MENU_SUBMENU_REGION = (280, 40, 980, 560)

MENU_ACCOUNT_TARGET = TemplateTarget(
    step_id="menu_account",
    label="5.บัญชี",
    template_file="menu_account.png",
    match_threshold=0.88,
)

MENU_DAILY_ENTRY_TARGET = TemplateTarget(
    step_id="menu_daily_entry",
    label="1.ลงประจำวัน",
    template_file="menu_daily_entry.png",
    match_threshold=0.88,
)

MENU_PAYMENT_JOURNAL_TARGET = TemplateTarget(
    step_id="menu_payment_journal",
    label="2.สมุดรายวันจ่าย",
    template_file="menu_payment_journal.png",
    match_threshold=0.80,
)

F12_MENU_REGION = (20, 20, 1400, 900)

MENU_ACCOUNT_REPORT_TARGET = TemplateTarget(
    step_id="menu_account_report",
    label=MENU_ACCOUNT_REPORT_LABEL,
    template_file="menu_account_report.png",
    match_threshold=0.88,
)

MENU_GENERAL_LEDGER_TARGET = TemplateTarget(
    step_id="menu_general_ledger",
    label=MENU_GENERAL_LEDGER_LABEL,
    template_file="menu_general_ledger.png",
    match_threshold=0.88,
)

MENU_REPORT_NORMAL_TARGET = TemplateTarget(
    step_id="menu_report_normal",
    label=MENU_REPORT_NORMAL_LABEL,
    template_file="menu_report_normal.png",
    match_threshold=0.88,
)

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
    TemplateClickAction(
        action_id="menu_account",
        target=MENU_ACCOUNT_TARGET,
        search_region=MENU_BAR_REGION,
    ),
    TemplateClickAction(
        action_id="menu_daily_entry",
        target=MENU_DAILY_ENTRY_TARGET,
        search_region=MENU_DROPDOWN_REGION,
    ),
    TemplateClickAction(
        action_id="menu_payment_journal",
        target=MENU_PAYMENT_JOURNAL_TARGET,
        search_region=MENU_SUBMENU_REGION,
    ),
    TemplateClickAction(
        action_id="menu_account_report",
        target=MENU_ACCOUNT_REPORT_TARGET,
        search_region=F12_MENU_REGION,
    ),
    TemplateClickAction(
        action_id="menu_general_ledger",
        target=MENU_GENERAL_LEDGER_TARGET,
        search_region=F12_MENU_REGION,
    ),
    TemplateClickAction(
        action_id="menu_report_normal",
        target=MENU_REPORT_NORMAL_TARGET,
        search_region=F12_MENU_REGION,
    ),
)

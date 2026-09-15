"""ปุ่มที่ AutoKey จับภาพแล้วคลิกบน Express จริง"""

from __future__ import annotations

from constants.routes import (
    MENU_ACCOUNT_REPORT_LABEL,
    MENU_GENERAL_JOURNAL_LABEL,
    MENU_GENERAL_LEDGER_LABEL,
    MENU_REPORT_NORMAL_LABEL,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
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

MENU_GENERAL_JOURNAL_TARGET = TemplateTarget(
    step_id="menu_general_journal",
    label=MENU_GENERAL_JOURNAL_LABEL,
    template_file="menu_general_journal.png",
    match_threshold=0.80,
)

# ต้นไม้รายงาน F12 อยู่ซ้ายจอ — อย่าสแกนเกือบทั้งจอ
F12_MENU_REGION = (20, 20, 880, 700)
REPORT_NORMAL_ACTION_IDS = ("menu_report_normal_selected", "menu_report_normal")
REPORT_PREVIEW_ACTION_IDS = ("report_preview_tmp6", "report_preview_title")

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

MENU_REPORT_NORMAL_SELECTED_TARGET = TemplateTarget(
    step_id="menu_report_normal_selected",
    label=f"{MENU_REPORT_NORMAL_LABEL} (เลือกอยู่)",
    template_file="menu_report_normal_selected.png",
    match_threshold=0.88,
)

REPORT_PREVIEW_REGION = (0, 0, SCREEN_WIDTH, 280)
REPORT_PREVIEW_TITLE_REGION = (0, 0, SCREEN_WIDTH, 800)
REPORT_EXPORT_REGION = (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

REPORT_PREVIEW_TMP6_TARGET = TemplateTarget(
    step_id="report_preview_tmp6",
    label="แถบพรีวิว TMP6",
    template_file="report_preview_tmp6.png",
    match_threshold=0.88,
)

REPORT_PREVIEW_TITLE_TARGET = TemplateTarget(
    step_id="report_preview_title",
    label="หัวรายงานแยกประเภททั่วไป",
    template_file="report_preview_title.png",
    match_threshold=0.88,
)

REPORT_EXPORT_JPEG_TARGET = TemplateTarget(
    step_id="report_export_jpeg",
    label="ช่อง JPEG",
    template_file="report_export_jpeg.png",
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
        action_id="menu_general_journal",
        target=MENU_GENERAL_JOURNAL_TARGET,
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
    TemplateClickAction(
        action_id="menu_report_normal_selected",
        target=MENU_REPORT_NORMAL_SELECTED_TARGET,
        search_region=F12_MENU_REGION,
    ),
    TemplateClickAction(
        action_id="report_preview_tmp6",
        target=REPORT_PREVIEW_TMP6_TARGET,
        search_region=REPORT_PREVIEW_REGION,
    ),
    TemplateClickAction(
        action_id="report_preview_title",
        target=REPORT_PREVIEW_TITLE_TARGET,
        search_region=REPORT_PREVIEW_TITLE_REGION,
    ),
    TemplateClickAction(
        action_id="report_export_jpeg",
        target=REPORT_EXPORT_JPEG_TARGET,
        search_region=REPORT_EXPORT_REGION,
    ),
)

from __future__ import annotations

from constants.routes import (
    PAGE_INCOME,
    PAGE_KA_TAM,
    PAGE_PND1,
    PAGE_PND2,
    PAGE_PND3,
    PAGE_PND30,
    PAGE_SSO,
    PAGE_WCF,
    PAGE_PAYROLL,
    PAGE_PP30,
    UI_TEXT,
)
from models.topic_menu_item import TopicMenuItem

TOPIC_KA_TAM_ID = "ka_tam"
TOPIC_PP30_ID = "pp30"
TOPIC_PND30_ID = "pnd30"
TOPIC_PND3_ID = "pnd3"
TOPIC_PND1_ID = "pnd1"
TOPIC_PND2_ID = "pnd2"
TOPIC_SSO_ID = "sso"
TOPIC_WCF_ID = "wcf"
TOPIC_PAYROLL_ID = "payroll"
TOPIC_INCOME_ID = "income"

TOPIC_MENU_ITEMS = (
    TopicMenuItem(
        id=TOPIC_KA_TAM_ID,
        title=UI_TEXT["menu_ka_tam"],
        hint=UI_TEXT["menu_ka_tam_hint"],
        page_route=PAGE_KA_TAM,
        enabled=True,
    ),
    TopicMenuItem(
        id=TOPIC_PP30_ID,
        title=UI_TEXT["menu_pp30"],
        hint=UI_TEXT["menu_pp30_hint"],
        page_route=PAGE_PP30,
        enabled=True,
    ),
    TopicMenuItem(
        id=TOPIC_PND30_ID,
        title=UI_TEXT["menu_pnd30"],
        hint=UI_TEXT["menu_pnd30_hint"],
        page_route=PAGE_PND30,
        enabled=True,
    ),
    TopicMenuItem(
        id=TOPIC_PND1_ID,
        title=UI_TEXT["menu_pnd1"],
        hint=UI_TEXT["menu_pnd1_hint"],
        page_route=PAGE_PND1,
        enabled=True,
    ),
    TopicMenuItem(
        id=TOPIC_PND2_ID,
        title=UI_TEXT["menu_pnd2"],
        hint=UI_TEXT["menu_pnd2_hint"],
        page_route=PAGE_PND2,
        enabled=True,
    ),
    TopicMenuItem(
        id=TOPIC_PND3_ID,
        title=UI_TEXT["menu_pnd3"],
        hint=UI_TEXT["menu_pnd3_hint"],
        page_route=PAGE_PND3,
        enabled=True,
    ),
    TopicMenuItem(
        id=TOPIC_INCOME_ID,
        title=UI_TEXT["menu_income"],
        hint=UI_TEXT["menu_income_hint"],
        page_route=PAGE_INCOME,
        enabled=True,
    ),
    TopicMenuItem(
        id=TOPIC_SSO_ID,
        title=UI_TEXT["menu_sso"],
        hint=UI_TEXT["menu_sso_hint"],
        page_route=PAGE_SSO,
        enabled=True,
    ),
    TopicMenuItem(
        id=TOPIC_WCF_ID,
        title=UI_TEXT["menu_wcf"],
        hint=UI_TEXT["menu_wcf_hint"],
        page_route=PAGE_WCF,
        enabled=True,
    ),
    TopicMenuItem(
        id=TOPIC_PAYROLL_ID,
        title=UI_TEXT["menu_payroll"],
        hint=UI_TEXT["menu_payroll_hint"],
        page_route=PAGE_PAYROLL,
        enabled=True,
    ),
)

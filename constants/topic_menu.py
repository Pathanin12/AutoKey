from __future__ import annotations

from constants.routes import PAGE_KA_TAM, PAGE_PND30, PAGE_PP30, UI_TEXT
from models.topic_menu_item import TopicMenuItem

TOPIC_KA_TAM_ID = "ka_tam"
TOPIC_PP30_ID = "pp30"
TOPIC_PND30_ID = "pnd30"

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
)

from __future__ import annotations

from constants.routes import PAGE_KA_TAM, UI_TEXT
from models.topic_menu_item import TopicMenuItem

TOPIC_KA_TAM_ID = "ka_tam"

TOPIC_MENU_ITEMS = (
    TopicMenuItem(
        id=TOPIC_KA_TAM_ID,
        title=UI_TEXT["menu_ka_tam"],
        hint=UI_TEXT["menu_ka_tam_hint"],
        page_route=PAGE_KA_TAM,
        enabled=True,
    ),
)

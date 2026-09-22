import unittest

from constants.routes import PAGE_CONFIG, PAGE_KA_TAM, PAGE_PND30, PAGE_PP30, UI_TEXT
from constants.topic_menu import (
    TOPIC_KA_TAM_ID,
    TOPIC_MENU_ITEMS,
    TOPIC_PND30_ID,
    TOPIC_PP30_ID,
)


class TopicMenuTests(unittest.TestCase):
    def test_first_menu_has_three_topics(self) -> None:
        ids = [item.id for item in TOPIC_MENU_ITEMS]
        self.assertEqual(ids, [TOPIC_KA_TAM_ID, TOPIC_PP30_ID, TOPIC_PND30_ID])
        self.assertEqual(TOPIC_MENU_ITEMS[0].title, UI_TEXT["menu_ka_tam"])
        self.assertEqual(TOPIC_MENU_ITEMS[0].page_route, PAGE_KA_TAM)
        self.assertEqual(TOPIC_MENU_ITEMS[1].title, UI_TEXT["menu_pp30"])
        self.assertEqual(TOPIC_MENU_ITEMS[1].page_route, PAGE_PP30)
        self.assertEqual(TOPIC_MENU_ITEMS[2].title, UI_TEXT["menu_pnd30"])
        self.assertEqual(TOPIC_MENU_ITEMS[2].page_route, PAGE_PND30)

    def test_config_route_is_separate_from_topics(self) -> None:
        self.assertEqual(UI_TEXT["menu_config"], "Config")
        self.assertEqual(PAGE_CONFIG, "config")
        self.assertNotIn(PAGE_CONFIG, [item.page_route for item in TOPIC_MENU_ITEMS])


if __name__ == "__main__":
    unittest.main()

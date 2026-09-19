import unittest
from pathlib import Path

from constants.routes import PAGE_PND30, UI_TEXT
from constants.topic_menu import TOPIC_MENU_ITEMS, TOPIC_PND30_ID
from models.pnd30_form_config import Pnd30FormConfig
from models.pp30_run_mode import Pp30RunMode


class Pnd30MenuTests(unittest.TestCase):
    def test_menu_opens_pnd30_page(self) -> None:
        item = next(entry for entry in TOPIC_MENU_ITEMS if entry.id == TOPIC_PND30_ID)
        self.assertEqual(item.page_route, PAGE_PND30)
        self.assertEqual(item.title, UI_TEXT["menu_pnd30"])
        self.assertTrue(item.enabled)


class Pnd30FormConfigTests(unittest.TestCase):
    def test_validate_requires_folder_excel_and_output(self) -> None:
        config = Pnd30FormConfig(
            pdf_folder=Path("/tmp/missing-pnd30"),
            excel_path=Path("/tmp/missing.xlsx"),
            pv_description="",
            report_output_dir=Path(""),
        )
        errors = config.validate()
        self.assertTrue(any("โฟลเดอร์ PDF" in item for item in errors))
        self.assertTrue(any("Excel" in item for item in errors))
        self.assertFalse(any("วันที่" in item for item in errors))
        self.assertFalse(any("JV" in item for item in errors))
        self.assertTrue(any("โฟลเดอร์เก็บไฟล์" in item for item in errors))

    def test_default_run_mode_is_normal(self) -> None:
        config = Pnd30FormConfig(
            pdf_folder=Path("/tmp/missing-pnd30"),
            excel_path=Path("/tmp/missing.xlsx"),
            pv_description="",
            report_output_dir=Path(""),
        )
        self.assertEqual(config.run_mode.key, Pp30RunMode.normal().key)


if __name__ == "__main__":
    unittest.main()

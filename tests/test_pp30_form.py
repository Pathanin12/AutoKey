import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from constants.routes import PP30_MODE_NORMAL, PP30_MODE_SPECIAL, UI_TEXT
from models.pp30_form_config import Pp30FormConfig
from models.pp30_run_mode import Pp30RunMode
from services.pp30_folder_service import Pp30FolderService


class Pp30FormTests(unittest.TestCase):
    def test_validate_requires_pdf_folder(self) -> None:
        config = Pp30FormConfig(
            pdf_folder=Path("/tmp/missing-pp30"),
            jv_description="",
            pv_description="",
        )
        errors = config.validate()
        self.assertTrue(any("โฟลเดอร์ PDF" in item for item in errors))
        self.assertFalse(any("Excel" in item for item in errors))
        self.assertIn(UI_TEXT["pp30_jv_date_invalid"], errors)

    def test_default_mode_is_normal(self) -> None:
        config = Pp30FormConfig(pdf_folder=Path("/tmp"), jv_description="", pv_description="")
        self.assertEqual(config.run_mode.key, PP30_MODE_NORMAL)
        self.assertEqual(Pp30RunMode.special().key, PP30_MODE_SPECIAL)
        self.assertEqual(Pp30RunMode.special().label, UI_TEXT["pp30_mode_special"])

    def test_validate_requires_complete_jv_date(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "a.pdf").write_bytes(b"%PDF")
            config = Pp30FormConfig(
                pdf_folder=folder,
                jv_description="",
                pv_description="",
                jv_date="31/08",
                pdf_files=Pp30FolderService.list_pdfs(folder),
            )
            self.assertEqual(config.validate(), [UI_TEXT["pp30_jv_date_invalid"]])
            config.jv_date = "31/08/69"
            self.assertEqual(config.validate(), [])

    def test_lists_pdf_files(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "a.pdf").write_bytes(b"%PDF")
            (folder / "b.PDF").write_bytes(b"%PDF")
            (folder / "skip.txt").write_text("x", encoding="utf-8")
            files = Pp30FolderService.list_pdfs(folder)
            self.assertEqual([path.name for path in files], ["a.pdf", "b.PDF"])


if __name__ == "__main__":
    unittest.main()

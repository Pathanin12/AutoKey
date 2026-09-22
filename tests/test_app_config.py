import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from models.app_config import AppConfig
from services.app_config_service import AppConfigService
from services.express_data_folder_service import ExpressDataFolderService


class AppConfigTests(unittest.TestCase):
    def test_validate_requires_existing_folder(self) -> None:
        config = AppConfig(express_data_dir=Path("/tmp/missing-express-data"))
        self.assertTrue(config.validate())

    def test_save_and_load_express_data_dir(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.yaml"
            folder = Path(tmp) / "companies"
            folder.mkdir()
            service = AppConfigService(path)
            service.save(AppConfig(express_data_dir=folder))
            loaded = service.load()
            self.assertEqual(loaded.express_data_dir, folder)
            self.assertEqual(loaded.validate(), [])

    def test_lists_company_dirs_with_isinfo(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            shop = root / "kachapor"
            shop.mkdir()
            (shop / "ISINFO.DBF").write_bytes(b"x")
            (root / "notes").mkdir()
            found = ExpressDataFolderService.list_company_dirs(root)
            self.assertEqual(found, [shop])


if __name__ == "__main__":
    unittest.main()

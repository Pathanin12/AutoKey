from __future__ import annotations

from pathlib import Path
from struct import pack
from tempfile import TemporaryDirectory
import unittest

from constants.routes import ISINFO_SHOP_NAME_FIELD, UI_TEXT
from models.express_company import ExpressCompany
from services.express_data_folder_service import ExpressDataFolderService
from services.express_shop_index_service import ExpressShopIndexService
from services.name_match_service import names_match, tidy_name
from services.pp30_match_service import Pp30MatchService
from services.pp30_pdf_service import Pp30PdfService, company_hint_from_filename


def _write_isinfo(path: Path, shop_name: str) -> None:
    encoded = shop_name.encode("cp874")
    field_len = 60
    padded = encoded[:field_len].ljust(field_len, b" ")
    rec = b" " + padded
    field = bytearray(32)
    field[0:6] = b"THINAM"
    field[11:12] = b"C"
    field[16] = field_len
    header = bytearray(32)
    header[0] = 0x03
    header[4:8] = pack("<I", 1)
    header_len = 32 + 32 + 1
    header[8:10] = pack("<H", header_len)
    header[10:12] = pack("<H", len(rec))
    path.write_bytes(bytes(header) + bytes(field) + b"\x0d" + rec + b"\x1a")


class Pp30MatchTests(unittest.TestCase):
    def test_matches_nbsp_and_extra_spaces(self) -> None:
        pdf_name = "ห้างหุ้นส่วนจำกัด กชพรรุ่งเรือง"
        shop_name = "ห้างหุ้นส่วนจำกัด\xa0กชพรรุ่งเรือง"
        self.assertEqual(tidy_name(shop_name), pdf_name)
        self.assertTrue(names_match(pdf_name, shop_name))
        self.assertTrue(names_match(pdf_name, "ห้างหุ้นส่วนจำกัด  กชพรรุ่งเรือง"))
        self.assertTrue(names_match("หจก.กชพรรุ่งเรือง", shop_name))

    def test_match_name_finds_shop_ignoring_spaces(self) -> None:
        companies = [
            ExpressCompany(folder=Path("/tmp/kachapor"), shop_name="ห้างหุ้นส่วนจำกัด\xa0กชพรรุ่งเรือง"),
            ExpressCompany(folder=Path("/tmp/other"), shop_name="บริษัท อื่น จำกัด"),
        ]
        found = Pp30MatchService.match_name("ห้างหุ้นส่วนจำกัด กชพรรุ่งเรือง", companies)
        self.assertIsNotNone(found)
        self.assertEqual(found.folder.name, "kachapor")

    def test_reads_thinam_from_isinfo(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            shop = root / "kachapor"
            shop.mkdir()
            _write_isinfo(shop / "ISINFO.DBF", "ห้างหุ้นส่วนจำกัด\xa0กชพรรุ่งเรือง")
            companies = ExpressDataFolderService.list_companies(root)
            self.assertEqual(len(companies), 1)
            self.assertEqual(companies[0].shop_name, "ห้างหุ้นส่วนจำกัด\xa0กชพรรุ่งเรือง")
            self.assertEqual(companies[0].folder, shop)
            index = ExpressShopIndexService(root / "shops.yaml")
            written = index.write_from_dir(root)
            self.assertEqual(written[0].folder, shop)
            loaded = index.load(root)
            found = Pp30MatchService.match_lookup(
                "หจก.กชพรรุ่งเรือง",
                Pp30MatchService.lookup(loaded),
            )
            self.assertIsNotNone(found)
            self.assertEqual(found.folder, shop)

    def test_extracts_company_name_after_label(self) -> None:
        text = "ชื่อผู้ประกอบการ\nห้างหุ้นส่วนจำกัด กชพรรุ่งเรือง\n5. ภาษีขายเดือนนี้"
        self.assertEqual(Pp30PdfService.extract_company_name(text), "ห้างหุ้นส่วนจำกัด กชพรรุ่งเรือง")

    def test_filename_hint_strips_p30_suffix(self) -> None:
        path = Path("กชพรรุ่งเรือง 2569 07 P30 Form 01.pdf")
        self.assertEqual(company_hint_from_filename(path), "กชพรรุ่งเรือง")

    def test_log_strings_exist(self) -> None:
        self.assertIn("{pdf_name}", UI_TEXT["pp30_match_log"])
        self.assertIn("{shop_name}", UI_TEXT["pp30_match_log"])
        self.assertEqual(ISINFO_SHOP_NAME_FIELD, "THINAM")


if __name__ == "__main__":
    unittest.main()

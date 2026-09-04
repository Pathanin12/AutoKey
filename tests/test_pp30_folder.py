import tempfile
import unittest
from pathlib import Path

from models.pp30_form_config import Pp30FormConfig
from models.pp30_matched_job import Pp30PdfRecord
from services.pp30_folder_service import Pp30FolderService
from services.pp30_match_service import Pp30MatchService
from services.pp30_pdf_service import Pp30PdfService


class Pp30FolderServiceTests(unittest.TestCase):
    def test_lists_pdf_files_and_skips_other_types(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            (folder / "a.pdf").write_bytes(b"%PDF")
            (folder / "b.PDF").write_bytes(b"%PDF")
            (folder / "notes.txt").write_text("x")
            (folder / ".hidden.pdf").write_bytes(b"%PDF")
            files = Pp30FolderService.list_pdfs(folder)
            names = [path.name for path in files]
            self.assertEqual(names, ["a.pdf", "b.PDF"])

    def test_missing_folder_returns_empty(self) -> None:
        self.assertEqual(Pp30FolderService.list_pdfs(Path("/tmp/does-not-exist-pp30")), [])


class Pp30FormConfigTests(unittest.TestCase):
    def test_validate_requires_folder_and_excel(self) -> None:
        config = Pp30FormConfig(
            pdf_folder=Path("/tmp/missing-pp30"),
            excel_path=Path("/tmp/missing.xlsx"),
            jv_date="",
            jv_description="",
            pv_description="",
        )
        errors = config.validate()
        self.assertTrue(any("โฟลเดอร์ PDF" in item for item in errors))
        self.assertTrue(any("Excel" in item for item in errors))
        self.assertTrue(any("วันที่ JV" in item for item in errors))


_SAMPLE_PP30_TEXT = """
ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88
มาหักในการคำนวณภาษีเดือนนี้
แบบแสดงรายการภาษีมูลค่าเพิ่ม
ชื่อผู้ประกอบการ
สาขาที่
ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88
"""


class Pp30PdfServiceTests(unittest.TestCase):
    def test_extracts_company_name_from_form_text(self) -> None:
        name = Pp30PdfService.extract_company_name(_SAMPLE_PP30_TEXT)
        self.assertEqual(name, "ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88")

    def test_extracts_company_name_from_rd_form_layout(self) -> None:
        name = Pp30PdfService.extract_company_name(
            """
ห้างหุ้นส่วนจำกัด เจนสิริการค้า
มาหักในการคำนวณภาษีเดือนนี้
แบบแสดงรายการภาษีมูลค่าเพิ่ม
ชื่อผู้ประกอบการ
สาขาที่
ห้างหุ้นส่วนจำกัด เจนสิริการค้า
ชื่อสถานประกอบการ
"""
        )
        self.assertEqual(name, "ห้างหุ้นส่วนจำกัด เจนสิริการค้า")


class Pp30MatchServiceTests(unittest.TestCase):
    def test_matches_pdf_name_to_excel_name(self) -> None:
        excel_names = [
            "บริษัท อื่น จำกัด",
            "ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88",
            "บริษัท ทดสอบ จำกัด",
        ]
        matched = Pp30MatchService.match_name("ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88", excel_names)
        self.assertEqual(matched, "ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88")

    def test_matches_full_legal_name_to_excel_abbreviation(self) -> None:
        excel_names = [
            "หจก.ฉัตราภัทร์",
            "หจก.ทัศนาออมทรัพย์กิจรุ่งเรือง",
            "หจก.ที.เอ็น.เอส.บิสซิเนส พาร์ทเนอร์",
            "หจก.ธนทรัพย์เจริญ 265",
            "หจก.ธนทรัพย์เจริญ 99",
            "หจก.วงเดือน คลองใหญ่",
            "หจก.เจนสิริการค้า",
        ]
        cases = [
            ("ห้างหุ้นส่วนจำกัด ฉัตราภัทร์", "หจก.ฉัตราภัทร์"),
            ("ห้างหุ้นส่วนจำกัด ทัศนาออมทรัพย์กิจรุ่งเรือง", "หจก.ทัศนาออมทรัพย์กิจรุ่งเรือง"),
            ("ห้างหุ้นส่วนจำกัด ที.เอ็น.เอส.บิสซิเนส พาร์ทเนอร์", "หจก.ที.เอ็น.เอส.บิสซิเนส พาร์ทเนอร์"),
            ("ห้างหุ้นส่วนจำกัด ธนทรัพย์เจริญ 265", "หจก.ธนทรัพย์เจริญ 265"),
            ("ห้างหุ้นส่วนจำกัด ธนทรัพย์เจริญ 99", "หจก.ธนทรัพย์เจริญ 99"),
            ("ห้างหุ้นส่วนจำกัด วงเดือน คลองใหญ่", "หจก.วงเดือน คลองใหญ่"),
            ("ห้างหุ้นส่วนจำกัด เจนสิริการค้า", "หจก.เจนสิริการค้า"),
        ]
        for pdf_name, excel_name in cases:
            with self.subTest(pdf_name=pdf_name):
                self.assertEqual(Pp30MatchService.match_name(pdf_name, excel_names), excel_name)

    def test_matches_company_to_spaced_abbreviation(self) -> None:
        matched = Pp30MatchService.match_name(
            "ห้างหุ้นส่วนจำกัด ฉัตราภัทร์",
            ["หจก. ฉัตราภัทร์", "บจก. ทดสอบ"],
        )
        self.assertEqual(matched, "หจก. ฉัตราภัทร์")

    def test_matches_company_to_borkor_abbreviation(self) -> None:
        matched = Pp30MatchService.match_name("บริษัท ทดสอบ จำกัด", ["บจก.ทดสอบ", "หจก.ทดสอบ"])
        self.assertEqual(matched, "บจก.ทดสอบ")

    def test_match_jobs_uses_excel_name(self) -> None:
        records = [
            Pp30PdfRecord(pdf_path=Path("a.pdf"), company_name="ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88"),
        ]
        jobs = Pp30MatchService.match_jobs(records, ["ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88"])
        self.assertEqual(jobs[0].excel_name, "ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88")

    def test_match_jobs_uses_filename_when_pdf_prefix_differs(self) -> None:
        records = [
            Pp30PdfRecord(
                pdf_path=Path("ฉัตราภัทร์ 2569 07 P30 Form 01.pdf"),
                company_name="ห้างหุ้นส่วนจำกัด ฉัตราภัทร์",
            ),
        ]
        jobs = Pp30MatchService.match_jobs(records, ["หจก.ฉัตราภัทร์"])
        self.assertEqual(jobs[0].excel_name, "หจก.ฉัตราภัทร์")

    def test_unmatched_name_raises(self) -> None:
        records = [Pp30PdfRecord(pdf_path=Path("a.pdf"), company_name="บริษัท ไม่มีในลิสต์ จำกัด")]
        with self.assertRaises(ValueError):
            Pp30MatchService.match_jobs(records, ["ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88"])

    def test_filename_hint_strips_p30_suffix(self) -> None:
        from services.pp30_pdf_service import company_hint_from_filename

        self.assertEqual(
            company_hint_from_filename(Path("เจนสิริการค้า 2569 07 P30 Form 01.pdf")),
            "เจนสิริการค้า",
        )


if __name__ == "__main__":
    unittest.main()

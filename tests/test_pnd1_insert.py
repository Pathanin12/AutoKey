import unittest
from pathlib import Path

from constants.routes import ACCOUNT_CASH, ACCOUNT_PP30_PENALTY, ACCOUNT_WT_PND1, UI_TEXT
from models.month_year_period import MonthYearPeriod
from models.pnd1_form_config import Pnd1FormConfig
from models.pnd1_form_values import Pnd1FormValues
from services.pnd1_extract_service import extract_line_6_and_7
from services.pnd1_insert_lines_service import pv_pnd1
from services.pnd1_pdf_service import Pnd1PdfService
from services.pnd30_extract_service import extract_pv_date

_SAMPLE = """
สรุปรายการภาษีที่นำส่ง จำนวนราย เงินได้ทั้งสิ้น ภาษีที่นำส่งทั้งสิ้น
1. เงินได้ตาม มาตรา 40 (1) เงินเดือน ค่าจ้าง ฯลฯ กรณีทั่วไป 1 36,250.00 500.00
6. รวม 1 36,250.00 500.00
7. เงินเพิ่ม (ถ้ามี)
8. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (6.+7.) 500.00
ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน) : สาขาที่ 00000
ห้างหุ้นส่วนจำกัด 3325 เอ็น เอ็น พี
วันที่: 12/08/2569
ยื่นวันที่ 12 เดือน สิงหาคม พ.ศ. 2569
ภ.ง.ด.1
"""

_SAMPLE_SURCHARGE = """
6. รวม 1 36,250.00 500.00
7. เงินเพิ่ม (ถ้ามี) 15.00
8. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (6.+7.) 515.00
วันที่: 12/08/2569
"""

SAMPLE_PDF = Path(
    "/Users/pathanin/.cursor/projects/Users-pathanin-job-AutoKey/attachments/"
    "95442e36-2dbc-40d8-8635-d8ec30cd3af5/TAX_FORM_P010014548191.pdf"
)


class Pnd1ExtractTests(unittest.TestCase):
    def test_reads_line_6_tax_and_empty_line_7(self) -> None:
        self.assertEqual(extract_line_6_and_7(_SAMPLE), (500.00, 0.0))
        self.assertEqual(extract_pv_date(_SAMPLE), "12/08/69")

    def test_reads_surcharge_on_line_7(self) -> None:
        self.assertEqual(extract_line_6_and_7(_SAMPLE_SURCHARGE), (500.00, 15.00))

    def test_reads_company_and_values(self) -> None:
        name = Pnd1PdfService.extract_company_name(_SAMPLE)
        values = Pnd1PdfService.extract_form_values(_SAMPLE)
        self.assertEqual(name, "ห้างหุ้นส่วนจำกัด 3325 เอ็น เอ็น พี")
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.tax_withheld, 500.00)
        self.assertFalse(values.has_surcharge)
        self.assertEqual(values.pv_date, "12/08/69")

    @unittest.skipUnless(SAMPLE_PDF.exists(), "sample ภ.ง.ด.1 pdf")
    def test_reads_uploaded_pdf(self) -> None:
        record = Pnd1PdfService.load_record(SAMPLE_PDF)
        self.assertEqual(record.company_name, "ห้างหุ้นส่วนจำกัด 3325 เอ็น เอ็น พี")
        self.assertIsNotNone(record.form_values)
        assert record.form_values is not None
        self.assertEqual(record.form_values.tax_withheld, 500.00)
        self.assertFalse(record.form_values.has_surcharge)
        self.assertEqual(record.form_values.pv_date, "12/08/69")


class Pnd1InsertLinesTests(unittest.TestCase):
    def test_line_6_then_cash(self) -> None:
        voucher = pv_pnd1(Pnd1FormValues(500.00, 0.0, "12/08/69"), "12/08/69", "ภ.ง.ด.1")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_WT_PND1, 500.00, False),
                (ACCOUNT_CASH, 500.00, True),
            ],
        )
        self.assertEqual(ACCOUNT_WT_PND1, "2132-01")
        self.assertEqual(ACCOUNT_CASH, "1111-00")

    def test_surcharge_before_cash(self) -> None:
        voucher = pv_pnd1(Pnd1FormValues(500.00, 15.0, "12/08/69"), "12/08/69", "ภ.ง.ด.1")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_WT_PND1, 500.00, False),
                (ACCOUNT_PP30_PENALTY, 15.0, False),
                (ACCOUNT_CASH, 515.00, True),
            ],
        )
        self.assertEqual(ACCOUNT_PP30_PENALTY, "5390-01")

    def test_form_needs_pdf_folder(self) -> None:
        errors = Pnd1FormConfig(pdf_folder=Path("/no-folder"), period=MonthYearPeriod.parse("08/69")).validate()
        self.assertTrue(any("โฟลเดอร์" in item for item in errors))
        self.assertNotIn(UI_TEXT["pnd1_period_invalid"], errors)

    def test_form_needs_period(self) -> None:
        errors = Pnd1FormConfig(pdf_folder=Path("/no-folder"), period=MonthYearPeriod.parse("")).validate()
        self.assertIn(UI_TEXT["pnd1_period_invalid"], errors)

    def test_description_from_month_and_year(self) -> None:
        form = Pnd1FormConfig(pdf_folder=Path("."), period=MonthYearPeriod.parse("08/69"))
        self.assertEqual(form.description, "กรมสรรพากร-ภ.ง.ด.1 เดือน 8/69")


if __name__ == "__main__":
    unittest.main()

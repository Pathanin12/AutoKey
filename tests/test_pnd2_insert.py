import unittest
from pathlib import Path

from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_PND2_PARTNER,
    ACCOUNT_PP30_PENALTY,
    ACCOUNT_WT_PND2,
    UI_TEXT,
)
from models.month_year_period import MonthYearPeriod
from models.pnd2_form_config import Pnd2FormConfig
from models.pnd2_form_values import Pnd2FormValues
from services.pnd2_extract_service import extract_income_period, extract_line_6_and_7
from services.pnd2_insert_lines_service import pv_pnd2, pv_pnd2_tax
from services.pnd2_insert_service import Pnd2InsertService
from services.pnd2_pdf_service import Pnd2PdfService

_SAMPLE = """
สรุปรายการภาษีที่นำส่ง
6. รวม จำนวนราย เงินได้ทั้งสิ้น ภาษีที่นำส่งทั้งสิ้น
6. รวม              2     50,000.00      5,000.00
7. เงินเพิ่ม (ถ้ามี)
8. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (6. + 7.) . . . . . . . 5,000.00
ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน) : สาขาที่ 0
ห้างหุ้นส่วนจำกัด ฐิติภัทรกิจรุ่งเรือง
เดือนที่จ่ายเงินได้พึงประเมิน
พ.ศ.     2569
(2) กุมภาพันธ์ü(5) พฤษภาคม(8) สิงหาคม(11) พฤศจิกายน
วันที่: 12/06/2569
ยื่นวันที่่ 12  เดือน มิถุนายน พ.ศ. 2569
ภ.ง.ด.2
"""

_SAMPLE_SURCHARGE = """
6. รวม              2     50,000.00      5,000.00
7. เงินเพิ่ม (ถ้ามี). . . . . . . . . . . . . . . 15.00
8. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (6. + 7.) . . . . . . . 5,015.00
"""

SAMPLE_PDF = Path(
    "/Users/pathanin/.cursor/projects/Users-pathanin-job-AutoKey/attachments/"
    "95442e36-2dbc-40d8-8635-d8ec30cd3af5/______.pdf"
)

_VALUES = Pnd2FormValues(
    people_count=2,
    income_amount=50000.00,
    tax_withheld=5000.00,
    pv_date="12/06/69",
    period=MonthYearPeriod(month=5, year=69),
)


class Pnd2ExtractTests(unittest.TestCase):
    def test_reads_line_6_three_columns_and_empty_line_7(self) -> None:
        self.assertEqual(extract_line_6_and_7(_SAMPLE), (2, 50000.00, 5000.00, 0.0))

    def test_reads_surcharge_on_line_7(self) -> None:
        self.assertEqual(extract_line_6_and_7(_SAMPLE_SURCHARGE), (2, 50000.00, 5000.00, 15.00))

    def test_reads_period_from_checked_month(self) -> None:
        period = extract_income_period(_SAMPLE)
        self.assertIsNotNone(period)
        assert period is not None
        self.assertEqual(period.text, "5/69")

    def test_reads_company_and_values(self) -> None:
        name = Pnd2PdfService.extract_company_name(_SAMPLE)
        values = Pnd2PdfService.extract_form_values(_SAMPLE)
        self.assertEqual(name, "ห้างหุ้นส่วนจำกัด ฐิติภัทรกิจรุ่งเรือง")
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.people_count, 2)
        self.assertEqual(values.income_amount, 50000.00)
        self.assertEqual(values.tax_withheld, 5000.00)
        self.assertFalse(values.has_surcharge)
        self.assertEqual(values.description, "จ่ายเงินปันผลหุ้นส่วน 2 คน")
        self.assertEqual(values.pv_date, "12/06/69")
        self.assertIsNotNone(values.period)
        assert values.period is not None
        self.assertEqual(values.period.text, "5/69")
        self.assertEqual(values.tax_description, "กรมสรรพากร ภ.ง.ด.2 เดือน 5/69")

    @unittest.skipUnless(SAMPLE_PDF.exists(), "sample ภ.ง.ด.2 pdf")
    def test_reads_uploaded_pdf(self) -> None:
        record = Pnd2PdfService.load_record(SAMPLE_PDF)
        self.assertEqual(record.company_name, "ห้างหุ้นส่วนจำกัด ฐิติภัทรกิจรุ่งเรือง")
        self.assertIsNotNone(record.form_values)
        assert record.form_values is not None
        self.assertEqual(record.form_values.people_count, 2)
        self.assertEqual(record.form_values.income_amount, 50000.00)
        self.assertEqual(record.form_values.tax_withheld, 5000.00)
        self.assertFalse(record.form_values.has_surcharge)
        self.assertEqual(record.form_values.pv_date, "12/06/69")
        self.assertIsNotNone(record.form_values.period)
        assert record.form_values.period is not None
        self.assertEqual(record.form_values.period.text, "5/69")


class Pnd2InsertLinesTests(unittest.TestCase):
    def test_income_tax_then_cash(self) -> None:
        voucher = pv_pnd2(_VALUES, "25/07/69", _VALUES.description)
        self.assertEqual(voucher.voudat_express, "25/07/69")
        self.assertEqual(voucher.description, "จ่ายเงินปันผลหุ้นส่วน 2 คน")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_PND2_PARTNER, 50000.00, False),
                (ACCOUNT_WT_PND2, 5000.00, True),
                (ACCOUNT_CASH, 45000.00, True),
            ],
        )

    def test_surcharge_before_cash(self) -> None:
        values = Pnd2FormValues(
            people_count=2, income_amount=50000.00, tax_withheld=5000.00, surcharge=15.0
        )
        voucher = pv_pnd2(values, "25/07/69", values.description)
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_PND2_PARTNER, 50000.00, False),
                (ACCOUNT_WT_PND2, 5000.00, True),
                (ACCOUNT_PP30_PENALTY, 15.0, False),
                (ACCOUNT_CASH, 45015.00, True),
            ],
        )

    def test_tax_pv_from_pdf_date(self) -> None:
        voucher = pv_pnd2_tax(_VALUES, _VALUES.pv_date, _VALUES.tax_description)
        self.assertEqual(voucher.voudat_express, "12/06/69")
        self.assertEqual(voucher.description, "กรมสรรพากร ภ.ง.ด.2 เดือน 5/69")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_WT_PND2, 5000.00, False),
                (ACCOUNT_CASH, 5000.00, True),
            ],
        )

    def test_tax_pv_includes_surcharge(self) -> None:
        values = Pnd2FormValues(
            people_count=2,
            income_amount=50000.00,
            tax_withheld=5000.00,
            surcharge=15.0,
            pv_date="12/06/69",
            period=MonthYearPeriod(month=5, year=69),
        )
        voucher = pv_pnd2_tax(values, values.pv_date, values.tax_description)
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_WT_PND2, 5000.00, False),
                (ACCOUNT_PP30_PENALTY, 15.0, False),
                (ACCOUNT_CASH, 5015.00, True),
            ],
        )

    def test_insert_builds_both_pvs(self) -> None:
        form = Pnd2FormConfig(pdf_folder=Path("."), pv_date="25/07/69")
        vouchers = Pnd2InsertService.vouchers(_VALUES, form)
        self.assertEqual(
            [(item.voudat_express, item.description, item.lines[0].account) for item in vouchers],
            [
                ("25/07/69", "จ่ายเงินปันผลหุ้นส่วน 2 คน", ACCOUNT_PND2_PARTNER),
                ("12/06/69", "กรมสรรพากร ภ.ง.ด.2 เดือน 5/69", ACCOUNT_WT_PND2),
            ],
        )

    def test_tax_isvat_uses_pdf_month(self) -> None:
        form = Pnd2FormConfig(pdf_folder=Path("."), pv_date="25/07/69")
        dividend, tax = Pnd2InsertService.vouchers(_VALUES, form)
        record = Pnd2InsertService.tax_vat_record(_VALUES, tax, "PV6906-0001")
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record.vatprd, "20260501")
        self.assertEqual(record.vatdat, "20260612")
        self.assertEqual(record.amt01, 50000.00)
        self.assertEqual(record.vat01, 5000.00)
        self.assertIsNone(Pnd2InsertService.tax_vat_record(_VALUES, dividend, "PV6907-0001"))

    def test_form_needs_pdf_folder(self) -> None:
        errors = Pnd2FormConfig(pdf_folder=Path("/no-folder"), pv_date="25/07/69").validate()
        self.assertTrue(any("โฟลเดอร์" in item for item in errors))
        self.assertNotIn(UI_TEXT["pnd2_pv_date_invalid"], errors)

    def test_form_needs_pv_date(self) -> None:
        errors = Pnd2FormConfig(pdf_folder=Path("/no-folder"), pv_date="").validate()
        self.assertIn(UI_TEXT["pnd2_pv_date_invalid"], errors)


if __name__ == "__main__":
    unittest.main()

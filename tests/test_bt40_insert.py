import unittest
from pathlib import Path

from constants.routes import (
    ACCOUNT_BT40_LOAN,
    ACCOUNT_BT40_TAX,
    ACCOUNT_CASH,
    ACCOUNT_PP30_DECIMAL,
    ACCOUNT_PP30_PENALTY,
    UI_TEXT,
)
from models.bt40_form_config import Bt40FormConfig
from models.bt40_form_values import Bt40FormValues
from models.month_year_period import MonthYearPeriod
from services.bt40_extract_service import extract_bt40_amounts, extract_bt40_pv_date
from services.bt40_insert_lines_service import pv_bt40, rv_bt40
from services.bt40_insert_service import Bt40InsertService
from services.bt40_pdf_service import Bt40PdfService

_SAMPLE = """
แบบแสดงรายการภาษีธุรกิจเฉพาะ
ภ.ธ.40
ชื่อผู้ประกอบกิจการ              ห้างหุ้นส่วนจำกัด ทัศนาออมทรัพย์กิจรุ่งเรือง
พิมพ์ ณ วันที่ 11 กันยายน 2569 เวลา 13:58 น.
7. การประกอบกิจการโดย                                 • ดอกเบี้ย ส่วนลด ค่าธรรมเนียม ค่าบริการฯ
   ปกติเยี่ยงธนาคารพาณิชย์                          43,200.00           3.0                           1,296.00
8. การขายอสังหาริมทรัพย์
12. รวมยอดภาษีธุรกิจเฉพาะ                                          1,296.00
13. เงินเพิ่ม (ถ้ามี)                                                  19.44
14. เบี้ยปรับ (ถ้ามี)                                                  64.80
15. รวม   (12. + 13. +14.)                                         1,380.24
16. รายได้ส่วนท้องถิ่น                                               138.02
17. รวมภาษีทั้งสิ้น  (15. + 16.)                                   1,518.26
"""

_SAMPLE_NO_PENALTY = """
7. การประกอบกิจการโดย
   ปกติเยี่ยงธนาคารพาณิชย์                          10,000.00           3.0                             300.00
8. การขายอสังหาริมทรัพย์
13. เงินเพิ่ม (ถ้ามี)
14. เบี้ยปรับ (ถ้ามี)
17. รวมภาษีทั้งสิ้น  (15. + 16.)                                     330.00
พิมพ์ ณ วันที่ 11 กันยายน 2569
"""

SAMPLE_PDF = Path(
    "/Users/pathanin/.cursor/projects/Users-pathanin-job-AutoKey/attachments/"
    "95442e36-2dbc-40d8-8635-d8ec30cd3af5/__.40_7.69__________.pdf"
)

_VALUES = Bt40FormValues(
    line7_receipt=43200.00,
    line13=19.44,
    line14=64.80,
    line17=1518.26,
    pv_date="11/09/69",
)


class Bt40ExtractTests(unittest.TestCase):
    def test_reads_line_7_col_1_and_13_14_17(self) -> None:
        self.assertEqual(extract_bt40_amounts(_SAMPLE), (43200.00, 19.44, 64.80, 1518.26))

    def test_reads_print_date(self) -> None:
        self.assertEqual(extract_bt40_pv_date(_SAMPLE), "11/09/69")

    def test_reads_company_and_values(self) -> None:
        name = Bt40PdfService.extract_company_name(_SAMPLE)
        values = Bt40PdfService.extract_form_values(_SAMPLE)
        self.assertEqual(name, "ห้างหุ้นส่วนจำกัด ทัศนาออมทรัพย์กิจรุ่งเรือง")
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.line7_receipt, 43200.00)
        self.assertEqual(values.line13, 19.44)
        self.assertEqual(values.line14, 64.80)
        self.assertEqual(values.line17, 1518.26)
        self.assertEqual(values.pv_date, "11/09/69")

    @unittest.skipUnless(SAMPLE_PDF.exists(), "sample ภ.ธ.40 pdf")
    def test_reads_uploaded_pdf(self) -> None:
        record = Bt40PdfService.load_record(SAMPLE_PDF)
        self.assertEqual(record.company_name, "ห้างหุ้นส่วนจำกัด ทัศนาออมทรัพย์กิจรุ่งเรือง")
        self.assertIsNotNone(record.form_values)
        assert record.form_values is not None
        self.assertEqual(record.form_values.line7_receipt, 43200.00)
        self.assertEqual(record.form_values.line13, 19.44)
        self.assertEqual(record.form_values.line14, 64.80)
        self.assertEqual(record.form_values.line17, 1518.26)
        self.assertEqual(record.form_values.pv_date, "11/09/69")


class Bt40InsertLinesTests(unittest.TestCase):
    def test_rv_cash_then_loan(self) -> None:
        voucher = rv_bt40(_VALUES, "25/07/69", "รับดอกเบี้ย-เงินกู้ยืมกรรมการ")
        self.assertEqual(voucher.prefix, "RV")
        self.assertEqual(voucher.voudat_express, "25/07/69")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_CASH, 43200.00, False),
                (ACCOUNT_BT40_LOAN, 43200.00, True),
            ],
        )

    def test_pv_splits_penalty_and_decimal(self) -> None:
        voucher = pv_bt40(_VALUES, "11/09/69", "กรมสรรพากร-ภ.ธ.40 เดือน 7/69")
        self.assertEqual(voucher.prefix, "PV")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_BT40_TAX, 1434.02, False),
                (ACCOUNT_PP30_PENALTY, 84.24, False),
                (ACCOUNT_CASH, 1518.00, True),
                (ACCOUNT_PP30_DECIMAL, 0.26, True),
            ],
        )
        self.assertEqual(ACCOUNT_BT40_TAX, "5360-08")
        self.assertEqual(ACCOUNT_BT40_LOAN, "1210-01")

    def test_pv_skips_penalty_and_zero_decimal(self) -> None:
        values = Bt40FormValues(line7_receipt=10000.00, line17=330.00, pv_date="11/09/69")
        voucher = pv_bt40(values, "11/09/69", "กรมสรรพากร-ภ.ธ.40 เดือน 7/69")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_BT40_TAX, 330.00, False),
                (ACCOUNT_CASH, 330.00, True),
            ],
        )
        self.assertEqual(extract_bt40_amounts(_SAMPLE_NO_PENALTY), (10000.00, 0.0, 0.0, 330.00))

    def test_insert_builds_rv_then_pv(self) -> None:
        form = Bt40FormConfig(
            pdf_folder=Path("/no-folder"),
            rv_date="25/07/69",
            period=MonthYearPeriod.parse("07/69"),
        )
        vouchers = Bt40InsertService.vouchers(_VALUES, form)
        self.assertEqual(len(vouchers), 2)
        self.assertEqual(vouchers[0].prefix, "RV")
        self.assertEqual(vouchers[0].description, "รับดอกเบี้ย-เงินกู้ยืมกรรมการ")
        self.assertEqual(vouchers[0].voudat_express, "25/07/69")
        self.assertEqual(vouchers[1].prefix, "PV")
        self.assertEqual(vouchers[1].description, "กรมสรรพากร-ภ.ธ.40 เดือน 7/69")
        self.assertEqual(vouchers[1].voudat_express, "11/09/69")
        self.assertEqual(form.validate(), [UI_TEXT["bt40_pdf_invalid"]])


if __name__ == "__main__":
    unittest.main()

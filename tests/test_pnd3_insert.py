import unittest
from pathlib import Path

from constants.routes import ACCOUNT_CASH, ACCOUNT_PP30_PENALTY, ACCOUNT_WT_PND3
from models.pnd3_form_config import Pnd3FormConfig
from models.pnd3_form_values import Pnd3FormValues
from services.pnd3_extract_service import extract_line_1_and_3
from services.pnd3_insert_lines_service import pv_pnd3
from services.pnd3_pdf_service import Pnd3PdfService
from services.pnd30_extract_service import extract_pv_date

_SAMPLE = """
4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (2. + 3.) . . . . . . . 456.69
3. เงินเพิ่ม (ถ้ามี). . . . . . . . . . . . . . .
456.69	2. . . . . . . . . . . . .	รวมยอดภาษีที่นำส่งทั้งสิ้น
1. . . . . . . . . . . . . . 15,223.00	รวมยอดเงินได้ทั้งสิ้น
ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน) : สาขาที่ 0	0	0	0	0
ห้างหุ้นส่วนจำกัด พิชยมงคล	................................................................
วันที่: 14/09/2569
ยื่นวันที่ 08 เดือน กันยายน พ.ศ. 2569
ภ.ง.ด.3
"""

_SAMPLE_SURCHARGE = """
4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (2. + 3.) . . . . . . . 471.00
3. เงินเพิ่ม (ถ้ามี). . . . . . . . . . . . . . . 15.00
456.00	2. . . . . . . . . . . . .	รวมยอดภาษีที่นำส่งทั้งสิ้น
1. . . . . . . . . . . . . . 15,223.00	รวมยอดเงินได้ทั้งสิ้น
วันที่: 14/09/2569
"""

SAMPLE_PDF = Path(
    "/Users/pathanin/.cursor/projects/Users-pathanin-job-AutoKey/attachments/"
    "95442e36-2dbc-40d8-8635-d8ec30cd3af5/________.pdf"
)


class Pnd3ExtractTests(unittest.TestCase):
    def test_reads_line_1_and_empty_line_3(self) -> None:
        self.assertEqual(extract_line_1_and_3(_SAMPLE), (15223.00, 0.0))
        self.assertEqual(extract_pv_date(_SAMPLE), "14/09/69")

    def test_reads_surcharge_on_line_3(self) -> None:
        self.assertEqual(extract_line_1_and_3(_SAMPLE_SURCHARGE), (15223.00, 15.00))

    def test_reads_company_and_values(self) -> None:
        name = Pnd3PdfService.extract_company_name(_SAMPLE)
        values = Pnd3PdfService.extract_form_values(_SAMPLE)
        self.assertEqual(name, "ห้างหุ้นส่วนจำกัด พิชยมงคล")
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.tax_withheld, 15223.00)
        self.assertFalse(values.has_surcharge)
        self.assertEqual(values.pv_date, "14/09/69")

    @unittest.skipUnless(SAMPLE_PDF.exists(), "sample ภ.ง.ด.3 pdf")
    def test_reads_uploaded_pdf(self) -> None:
        record = Pnd3PdfService.load_record(SAMPLE_PDF)
        self.assertEqual(record.company_name, "ห้างหุ้นส่วนจำกัด พิชยมงคล")
        self.assertIsNotNone(record.form_values)
        assert record.form_values is not None
        self.assertEqual(record.form_values.tax_withheld, 15223.00)
        self.assertFalse(record.form_values.has_surcharge)
        self.assertEqual(record.form_values.pv_date, "14/09/69")


class Pnd3InsertLinesTests(unittest.TestCase):
    def test_line_1_then_cash(self) -> None:
        voucher = pv_pnd3(Pnd3FormValues(15223.0, 0.0, "14/09/69"), "14/09/69", "ภ.ง.ด.3")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_WT_PND3, 15223.0, False),
                (ACCOUNT_CASH, 15223.0, True),
            ],
        )

    def test_surcharge_before_cash(self) -> None:
        voucher = pv_pnd3(Pnd3FormValues(15223.0, 15.0, "14/09/69"), "14/09/69", "ภ.ง.ด.3")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_WT_PND3, 15223.0, False),
                (ACCOUNT_PP30_PENALTY, 15.0, False),
                (ACCOUNT_CASH, 15238.0, True),
            ],
        )

    def test_form_needs_pdf_folder(self) -> None:
        errors = Pnd3FormConfig(pdf_folder=Path("/no-folder"), description="x").validate()
        self.assertTrue(any("โฟลเดอร์" in item for item in errors))


if __name__ == "__main__":
    unittest.main()

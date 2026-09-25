import unittest
from pathlib import Path

from constants.routes import ACCOUNT_CASH, ACCOUNT_PP30_PENALTY, ACCOUNT_WT
from models.pnd30_form_config import Pnd30FormConfig
from models.pnd30_form_values import Pnd30FormValues
from services.pnd30_extract_service import extract_line_2_and_3, extract_pv_date
from services.pnd30_insert_lines_service import pv_pnd30
from services.pnd30_pdf_service import Pnd30PdfService

_SAMPLE_SURCHARGE = """
4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (2. + 3.) . . . . . . . 1,036.25
3. เงินเพิ่ม (ถ้ามี). . . . . . . . . . . . . . . 15.31
1,020.94	2. . . . . . . . . . . . .	รวมยอดภาษีที่นำส่งทั้งสิ้
1. . . . . . . . . . . . . . 34,031.25	รวมยอดเงินได้ทั้งสิ้น
ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน) : สาขาที่ 0	0	0	0	0
ห้างหุ้นส่วนจำกัด ธนทรัพย์เจริญ 99	................................................................
ยื่นวันที่ 16 เดือน มิถุนายน พ.ศ. 2569
วันที่: 16/06/2569
"""

_SAMPLE_NO_SURCHARGE = """
4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (2. + 3.) . . . . . . . 36.00
3. เงินเพิ่ม (ถ้ามี). . . . . . . . . . . . . . .
36.00	2. . . . . . . . . . . .	รวมยอดภาษีที่นำส่งทั้งสิ้
1. . . . . . . . . . . . . . 1,200.00	รวมยอดเงินได้ทั้งสิ้น
ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน) : สาขาที่ 0	0	0	0	0
ห้างหุ้นส่วนจำกัด 2411	................................................................
วันที่: 13/07/2569
ยื่นวันที่ 08 เดือน กรกฎาคม พ.ศ. 2569
"""


class Pnd30ExtractTests(unittest.TestCase):
    def test_reads_line_2_and_surcharge_line_3(self) -> None:
        self.assertEqual(extract_line_2_and_3(_SAMPLE_SURCHARGE), (1020.94, 15.31))
        self.assertEqual(extract_pv_date(_SAMPLE_SURCHARGE), "16/06/69")

    def test_empty_line_3_is_zero(self) -> None:
        self.assertEqual(extract_line_2_and_3(_SAMPLE_NO_SURCHARGE), (36.00, 0.0))
        self.assertEqual(extract_pv_date(_SAMPLE_NO_SURCHARGE), "13/07/69")

    def test_reads_company_and_values(self) -> None:
        name = Pnd30PdfService.extract_company_name(_SAMPLE_SURCHARGE)
        values = Pnd30PdfService.extract_form_values(_SAMPLE_SURCHARGE)
        self.assertEqual(name, "ห้างหุ้นส่วนจำกัด ธนทรัพย์เจริญ 99")
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.tax_withheld, 1020.94)
        self.assertEqual(values.surcharge, 15.31)
        self.assertEqual(values.pv_date, "16/06/69")


class Pnd30InsertLinesTests(unittest.TestCase):
    def test_tax_then_cash(self) -> None:
        voucher = pv_pnd30(Pnd30FormValues(36.0, 0.0, "13/07/69"), "13/07/69", "ภ.ง.ด.53")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_WT, 36.0, False),
                (ACCOUNT_CASH, 36.0, True),
            ],
        )

    def test_surcharge_before_cash(self) -> None:
        voucher = pv_pnd30(Pnd30FormValues(1020.94, 15.31, "16/06/69"), "16/06/69", "ภ.ง.ด.53")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_WT, 1020.94, False),
                (ACCOUNT_PP30_PENALTY, 15.31, False),
                (ACCOUNT_CASH, 1036.25, True),
            ],
        )

    def test_form_needs_pdf_folder(self) -> None:
        errors = Pnd30FormConfig(pdf_folder=Path("/no-folder"), description="x").validate()
        self.assertTrue(any("โฟลเดอร์" in item for item in errors))


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from constants.routes import (
    ACCOUNT_INCOME,
    ACCOUNT_INCOME_RECEIVABLE,
    ACCOUNT_INCOME_WHT,
    ACCOUNT_PP30_VAT_SALE,
    VATREC_SALE,
)
from models.income_form_config import IncomeFormConfig
from models.income_form_values import IncomeFormValues
from services.income_extract_service import extract_income_invoice, is_rv_tax_invoice
from services.income_insert_lines_service import rv_income
from services.income_insert_service import IncomeInsertService

_SAMPLE = """
หจก. พี ที รีเทลลิ่ง
สำนักงานใหญ่ เลขที่ 1867/119 ถนน เจริญนคร
เลขประจำตัวผู้เสียภาษี
0103552027652
เลขที่
วันที่
ใบเสร็จรับเงิน/ใบกำกับภาษี (สำเนา)
2900054763
18.09.2026
รายละเอียดบิลที่ชำระ
318,583.39
รับจาก : บริษัท ซีพี ออลล์ จำกัด (มหาชน) สำนักงานใหญ่
3807064
60008864903131.08.2036
เลขประจำตัวผู้เสียภาษี 0107542000011
ชำระค่า : ค่าตอบแทนจากการบริหาร เดือน 08/69
OFFSET
331,326.73
รวมเงิน
บวก ภาษีมูลค่าเพิ่ม
รวมเงิน
หัก ภาษีหัก ณ ที่จ่าย
รวมเงินทั้งสิ้น
318,583.39
22,300.84
340,884.23
9,557.50
331,326.73
"""

_SAMPLE_TWO_BILLS = _SAMPLE.replace(
    "60008864903131.08.2036",
    "6000886490\n6000886501",
)

_RECEIPT_ONLY = """
บริษัท ซีพี ออลล์ จำกัด (มหาชน)
ใบเสร็จรับเงิน
ต้นฉบับ
"""


class IncomeExtractTests(unittest.TestCase):
    def test_reads_tax_invoice_amounts(self) -> None:
        self.assertTrue(is_rv_tax_invoice(_SAMPLE))
        self.assertFalse(is_rv_tax_invoice(_RECEIPT_ONLY))
        values = extract_income_invoice(_SAMPLE)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.company_name, "หจก. พี ที รีเทลลิ่ง")
        self.assertEqual(values.invoice_number, "2900054763")
        self.assertEqual(values.tax_id, "0107542000011")
        self.assertEqual(values.invoice_date, "18/09/69")
        self.assertEqual(values.branch_last5, "07064")
        self.assertEqual(values.total_amount, 331326.73)
        self.assertEqual(values.wht_amount, 9557.50)
        self.assertEqual(values.vat_amount, 22300.84)
        self.assertEqual(values.bill_count, 1)

    def test_reads_invoice_from_numbers_when_thai_marks_missing(self) -> None:
        text = (
            "หจก พี ที รีเทลลิ่ง\n"
            "2900054763 18.09.2026\n"
            "0103552027652\n"
            "เลขประจำตัวผู้เสียภาษี 0107542000011\n"
            "3807064\n"
            "318,583.39 22,300.84 340,884.23 9,557.50 331,326.73\n"
        )
        self.assertTrue(is_rv_tax_invoice(text))
        values = extract_income_invoice(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.invoice_number, "2900054763")
        self.assertEqual(values.tax_id, "0107542000011")
        self.assertEqual(values.branch_last5, "07064")

    def test_uses_date_after_invoice_number(self) -> None:
        text = (
            "หจก. พี ที รีเทลลิ่ง\n"
            "31.08.2026\n"
            "ใบเสร็จรับเงิน/ใบกำกับภาษี\n"
            "2900054763\n"
            "18.09.2026\n"
            "เลขประจำตัวผู้เสียภาษี 0107542000011\n"
            "3807064\n"
            "318,583.39 22,300.84 340,884.23 9,557.50 331,326.73\n"
        )
        values = extract_income_invoice(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.invoice_date, "18/09/69")

    def test_counts_more_than_one_bill(self) -> None:
        values = extract_income_invoice(_SAMPLE_TWO_BILLS)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.bill_count, 2)


class IncomeInsertLinesTests(unittest.TestCase):
    def test_rv_lines_then_income_remainder(self) -> None:
        values = IncomeFormValues(
            company_name="หจก. ทดสอบ",
            branch_last5="70064",
            invoice_date="18/09/69",
            invoice_number="2900054763",
            tax_id="0107542000011",
            total_amount=331326.73,
            wht_amount=9557.50,
            vat_amount=22300.84,
            bill_count=1,
        )
        voucher = rv_income(values, "18/09/69", "บมจ.ซีพีออลล์-ค่าตอบแทนการบริหาร ด.8/69*70064")
        self.assertEqual(voucher.jnltyp, "02")
        self.assertEqual(voucher.prefix, "RV")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_INCOME_RECEIVABLE, 331326.73, False),
                (ACCOUNT_INCOME_WHT, 9557.50, False),
                (ACCOUNT_PP30_VAT_SALE, 22300.84, True),
                (ACCOUNT_INCOME, 318583.39, True),
            ],
        )

    def test_description_appends_branch(self) -> None:
        values = IncomeFormValues(
            company_name="หจก. ทดสอบ",
            branch_last5="70064",
            invoice_date="18/09/69",
            invoice_number="2900054763",
            tax_id="0107542000011",
            total_amount=100.0,
            wht_amount=0.0,
            vat_amount=0.0,
            bill_count=1,
        )
        form = IncomeFormConfig(pdf_folder=Path("."), rv_description="บมจ.ซีพีออลล์-ค่าตอบแทนการบริหาร ด.8/69")
        self.assertEqual(
            IncomeInsertService.description(values, form),
            "บมจ.ซีพีออลล์-ค่าตอบแทนการบริหาร ด.8/69*70064",
        )
        self.assertEqual(VATREC_SALE, "S")

    def test_form_needs_pdf_folder(self) -> None:
        errors = IncomeFormConfig(pdf_folder=Path("/no-folder"), rv_description="x").validate()
        self.assertTrue(any("โฟลเดอร์" in item for item in errors))
        self.assertTrue(any("Excel" in item for item in errors))


if __name__ == "__main__":
    unittest.main()

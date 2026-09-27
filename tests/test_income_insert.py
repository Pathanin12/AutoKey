import unittest
from pathlib import Path

from constants.routes import (
    ACCOUNT_INCOME,
    ACCOUNT_INCOME_ADVANCE,
    ACCOUNT_INCOME_GOODS,
    ACCOUNT_INCOME_RECEIVABLE,
    ACCOUNT_INCOME_WHT,
    ACCOUNT_PP30_VAT_SALE,
    INCOME_RV_ADVANCE,
    INCOME_RV_GOODS,
    INCOME_RV_TAX,
    VATREC_SALE,
)
from models.income_form_config import IncomeFormConfig
from models.income_form_values import IncomeFormValues
from services.income_extract_service import (
    extract_income_invoice,
    extract_income_receipt,
    extract_income_values,
    is_rv_tax_invoice,
)
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

_RECEIPT_GOODS = """
หจก. จิราวรรณ คอนวีเนียนซ์สโตร์
ใบเสร็จรับเงิน (สำเนา)
2900054763
18.09.2026
เลขประจำตัวผู้เสียภาษี 0107542000011
3807064
ชำระค่า : สินค้าและบริการ
รวมเงินทั้งสิ้น 10,000.00
หัก ภาษีหัก ณ ที่จ่าย 300.00
"""

_RECEIPT_ADVANCE = """
หจก. ปรีดีวิทย์
ใบเสร็จรับเงิน (สำเนา)
2800009528
18.09.2026
เลขประจำตัวผู้เสียภาษี 0107542000011
3807064
ชำระค่า : เบิกเงินสำรอง
รวมเงินทั้งสิ้น 5,000.00
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

    def test_reads_receipt_goods(self) -> None:
        values = extract_income_receipt(_RECEIPT_GOODS)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.kind, INCOME_RV_GOODS)
        self.assertEqual(values.company_name, "หจก. จิราวรรณ คอนวีเนียนซ์สโตร์")
        self.assertEqual(values.invoice_number, "2900054763")
        self.assertEqual(values.tax_id, "0107542000011")
        self.assertEqual(values.branch_last5, "07064")
        self.assertEqual(values.total_amount, 10000.0)
        self.assertEqual(values.wht_amount, 300.0)

    def test_reads_goods_when_pay_is_on_next_line(self) -> None:
        text = (
            "ใบเสร็จรับเงิน (สำเนา)\n"
            "หจก. กชพรตรรกพล 2489\n"
            "2800007038\n"
            "20.02.2026\n"
            "เลขประจำตัวผู้เสียภาษี 0107542000011\n"
            "3816329\n"
            "ชำระค่า :\n"
            "สินค้าและบริการ\n"
            "รวมเงินทั้งสิ้น 6,306.37\n"
            "หัก ภาษีหัก ณ ที่จ่าย 63.71\n"
        )
        values = extract_income_receipt(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.kind, INCOME_RV_GOODS)
        self.assertEqual(values.invoice_number, "2800007038")
        self.assertEqual(values.tax_id, "0107542000011")
        self.assertEqual(values.invoice_date, "20/02/69")
        self.assertEqual(values.total_amount, 6306.37)
        self.assertEqual(values.wht_amount, 63.71)

    def test_one_file_keeps_every_kind(self) -> None:
        kinds = [
            values.kind
            for text in (_SAMPLE, _RECEIPT_GOODS, _RECEIPT_ADVANCE)
            if (values := extract_income_values(text)) is not None
        ]
        self.assertEqual(kinds, [INCOME_RV_TAX, INCOME_RV_GOODS, INCOME_RV_ADVANCE])

    def test_reads_receipt_advance(self) -> None:
        values = extract_income_receipt(_RECEIPT_ADVANCE)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.kind, INCOME_RV_ADVANCE)
        self.assertEqual(values.company_name, "หจก. ปรีดีวิทย์")
        self.assertEqual(values.invoice_number, "2800009528")
        self.assertEqual(values.tax_id, "0107542000011")
        self.assertEqual(values.branch_last5, "07064")
        self.assertEqual(values.total_amount, 5000.0)


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

    def test_description_from_start_date(self) -> None:
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
        form = IncomeFormConfig(pdf_folder=Path("."), start_date="01/08/69")
        self.assertEqual(
            IncomeInsertService.description(values, form),
            "บมจ.ซีพีออลล์-ค่าตอบแทนการบริหาร ด.8/69*70064",
        )
        goods = IncomeFormValues(
            company_name="หจก. ทดสอบ",
            branch_last5="04497",
            invoice_date="18/09/69",
            invoice_number="2900054763",
            tax_id="0107542000011",
            total_amount=100.0,
            wht_amount=3.0,
            vat_amount=0.0,
            bill_count=1,
            kind=INCOME_RV_GOODS,
        )
        self.assertEqual(
            IncomeInsertService.description(goods, form),
            "บมจ.ซีพีออลล์-สินค้าและบริการ ด.8/69*04497",
        )
        advance = IncomeFormValues(
            company_name="หจก. ทดสอบ",
            branch_last5="09310",
            invoice_date="18/09/69",
            invoice_number="",
            tax_id="",
            total_amount=100.0,
            wht_amount=0.0,
            vat_amount=0.0,
            bill_count=1,
            kind=INCOME_RV_ADVANCE,
        )
        self.assertEqual(
            IncomeInsertService.description(advance, form),
            "บมจ.ซีพีออลล์-เบิกเงินสำรอง ด.8/69*09310",
        )
        self.assertEqual(VATREC_SALE, "S")

    def test_goods_and_advance_lines(self) -> None:
        goods = IncomeFormValues(
            company_name="หจก. ทดสอบ",
            branch_last5="04497",
            invoice_date="18/09/69",
            invoice_number="2900054763",
            tax_id="0107542000011",
            total_amount=10000.0,
            wht_amount=300.0,
            vat_amount=0.0,
            bill_count=1,
            kind=INCOME_RV_GOODS,
        )
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in rv_income(goods, "18/09/69", "x").lines],
            [
                (ACCOUNT_INCOME_RECEIVABLE, 10000.0, False),
                (ACCOUNT_INCOME_WHT, 300.0, False),
                (ACCOUNT_INCOME_GOODS, 10300.0, True),
            ],
        )
        advance = IncomeFormValues(
            company_name="หจก. ทดสอบ",
            branch_last5="09310",
            invoice_date="18/09/69",
            invoice_number="",
            tax_id="",
            total_amount=5000.0,
            wht_amount=0.0,
            vat_amount=0.0,
            bill_count=1,
            kind=INCOME_RV_ADVANCE,
        )
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in rv_income(advance, "18/09/69", "x").lines],
            [
                (ACCOUNT_INCOME_RECEIVABLE, 5000.0, False),
                (ACCOUNT_INCOME_ADVANCE, 5000.0, True),
            ],
        )

    def test_form_needs_pdf_folder(self) -> None:
        errors = IncomeFormConfig(pdf_folder=Path("/no-folder")).validate()
        self.assertTrue(any("โฟลเดอร์" in item for item in errors))
        self.assertTrue(any("Excel" in item for item in errors))


if __name__ == "__main__":
    unittest.main()

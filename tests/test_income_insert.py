import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from constants.routes import (
    ACCOUNT_INCOME,
    ACCOUNT_INCOME_ADVANCE,
    ACCOUNT_INCOME_DEPOSIT,
    ACCOUNT_INCOME_GOODS,
    ACCOUNT_INCOME_RECEIVABLE,
    ACCOUNT_INCOME_RENT,
    ACCOUNT_INCOME_WHT,
    ACCOUNT_PP30_VAT_SALE,
    ACCOUNT_VAT,
    ACCOUNT_WT,
    INCOME_PV_TAX,
    INCOME_PV_RECEIPT,
    INCOME_RV_ADVANCE,
    INCOME_RV_GOODS,
    INCOME_RV_RENT,
    INCOME_RV_TAX,
    INCOME_LOCK_NONE,
    INCOME_LOCK_PASSWORD,
    VATREC_SALE,
)
from models.income_form_config import IncomeFormConfig
from models.income_form_values import IncomeFormValues
from models.income_lock_mode import IncomeLockMode
from models.income_pdf_name import IncomePdfName
from services.income_pdf_service import IncomePdfService
from services.income_report_service import IncomeReportService
from services.income_extract_service import (
    extract_income_invoice,
    extract_income_receipt,
    extract_income_values,
    is_rv_tax_invoice,
)
from services.income_insert_lines_service import rv_income
from services.income_insert_service import IncomeInsertService
from services.income_pv_extract_service import extract_income_pv_receipt, extract_income_pv_tax
from services.income_pv_insert_lines_service import pv_income_receipt, pv_income_tax

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

_RECEIPT_RENT = """
รวมเงิน
บวก  ภาษีมูลค่าเพิม
รวมเงิน
หัก  ภาษีหัก ณ ทีจ่าย
รวมเงินทังสิน
6007724078
31.07.2026
       8,019.63
ใบเสร็จรับเงิน (สําเนา)
หจก. อรพรรณ เทรดดิง (2002)
0103545013692
2800009248
14.08.2026
บริษัท ซีพี ออลล์ จํากัด (มหาชน)   สํานักงานใหญ่
เลขประจําตัวผู้เสียภาษี  0107542000011
3800245
ค่าเช่ารับ 1% (A-MO) เดือน 07/69 ประจําเดือน 07/69
OFFSET
       7,618.65
       7,618.65
            8,019.63
                0.00
       8,019.63
              400.98
       7,618.65
"""

_RECEIPT_RENT_OCR = """
หจก. อรพรรณ เทรดดิ้ง (2002)
เลขประจำตัวผู้เสียภาษี
0103545013692
ใบเสร็จรับเงิน (สำเนา)
2800009248
14.08.2026
จำนวนเงิน
8,019.63
รับจาก : บริษัท ซีพี ออลล์ จำกัด (มหาชน) สำนักงานใหญ่
3800245
313 อาคาร ซี.พี.ทาวเวอร์ ชั้นที่ 24 ถนน สีลม กรุงเทพมหานคร 10506007724078 31.07.2026
เลขประจำตัวผู้เสียภาษี 0107542000011
ชำระค่า : ค่าเช่ารับ 1% (A-MO) เดือน 07/69 ประจำเดือน 07/69
OFFSET
71518.65
รวม (บาท)
7,618.65
รวมเงิน
บวก ภาษีมูลค่าเพิ่ม
รวมเงิน
หัก ภาษีหัก ณ ที่จ่าย
รวมเงินทั้งสิ้น
8,019.63
0.00
8,019.63
400.98
7,618.65
"""

_CPALL_PV_TAX = """
CP ALL PUBLIC COMPANY LIMITED
บริษัท ซีพี ออลล์ จำกัด (มหาชน)
เลขประจำตัวผู้เสียภาษี 0107542000011
Receipt
ใบเสร็จรับเงิน/ใบกำกับภาษี
ต้นฉบับ
รหัสลูกค้า :
ชื่อลูกค้า :
3808734 สำนักงานใหญ่
หจก. 3325 เอ็น เอ็น พี
เลขที่ :
2600008431
วันที่ :
20.02.2026
เลขประจำตัวผู้เสียภาษี :
0123549005198
ชำระค่า ค่าสิทธิ์ เดือน 08/69
ค่ารวม 1,000.00
บวก ภาษีมูลค่าเพิ่ม 70.00
หัก ณ ที่จ่าย 30.00
จำนวนเงินที่ต้องชำระ 1,040.00
"""

_CPALL_PV_TAX_OCR = """
CP ALL PUBLIC COMPANY LIMITED
บริษัท ซีพี ออลล์ จำกัด (มหาชน)
เลขประจำตัวผู้เสียภาษี 0107542000011
Receipt
ใบเสร็จรับเงิน
ต้นฉบับ
รหัสลูกค้า : 3810981
หจก. อิงฟ้า คอนวีเนียนซ์สโตร์
เลขที่ : 2700015438
วันที่ : 18.09.2026
สาขาที่ออกใบกำกับภาษี : 00000
ใบกำกับภาษี
ชำระค่า
Renewal Expense เดือน 08/69 5,000.00
ค่าใช้จ่ายเพื่อการเปิดร้าน เดือน 08/69 5,000.00
รวม (บาท)
ภาษีถูกหัก ณ ที่จ่าย 300.00
รวม
บาก ภาษีมูลค่าเพิ่ม
หัก ณ ที่จ่าย
จำนวนเงินที่ชำระ
10,000.00
700.00
10,700.00
300.00
10,400.00
"""

_CPALL_PV_RECEIPT = """
CP ALL PUBLIC COMPANY LIMITED
บริษัท ซีพี ออลล์ จำกัด (มหาชน)
เลขประจำตัวผู้เสียภาษี 0107542000011
Receipt
ใบเสร็จรับเงิน
ต้นฉบับ
รหัสลูกค้า :
ชื่อลูกค้า :
3810981 สำนักงานใหญ่
หจก. อิงฟ้า คอนวีเนียนซ์สโตร์
เลขที่ :
2600049608
วันที่ :
18.09.2026
เลขประจำตัวผู้เสียภาษี :
0103562018222
สาขาที่ออกใบกำกับภาษี : 00000
ชำระค่า
ผ่อนเงินสำรอง รถเข็นลัง เดือน 08/69
เงินประกัน เดือน 08/69
297.00
10,132.75
รวม (บาท)
หัก ณ ที่จ่าย 0.00
จำนวนเงินที่ชำระ 10,429.75
"""

_CPALL_PV_RECEIPT_OCR = """
CP ALL PUBLIC COMPANY LIMITED
บริษัท ซีพี ออลล์ จำกัด (มหาชน)
เลขประจำตัวผู้เสียภาษี 0107542000011
Receipt
ใบเสร็จรับเงิน
ต้นฉบับ
รหัสลูกค้า :
ชื่อลูกค้า :
3810981
สำนักงานใหญ่
หจก. อิงฟ้า คอนวีเนียนซ์สโตร์
เลขประจำตัวผู้เสียภาษี :
0103562018222
Invoice Date
วันที่ใบแจ้งหนี้
31.03.2026
31.08.2026
เลขที่ :
วันที่ :
2600049608
18.09.2026
6400509502
Description
ชำระค่า
ผ่อนเงินสำรอง รถเข็นลัง เดือน 08/69
เงินประกัน เดือน 08:69
Amount
จำนวนเงิน
297.00
10,132.75
รวม (บาท)
หัก ณ ที่จ่าย
จำนวนเงินที่ชำระ
10,429.75
0.00
10,429.75
"""

_CPALL_PV_DEPOSIT_ONLY = """
CP ALL PUBLIC COMPANY LIMITED
บริษัท ซีพี ออลล์ จำกัด (มหาชน)
เลขประจำตัวผู้เสียภาษี 0107542000011
Receipt
ใบเสร็จรับเงิน
ต้นฉบับ
รหัสลูกค้า : 3810981
หจก. อิงฟ้า คอนวีเนียนซ์สโตร์
เลขที่ : 2600049608
วันที่ : 18.09.2026
ชำระค่า
เงินประกัน เดือน 08/69 5,000.00
เงินประกัน ค่าเช่า เดือน 08/69 3,000.00
รวม (บาท)
จำนวนเงินที่ชำระ 8,000.00
"""

_CPALL_PV_INSTALL_ONLY = """
CP ALL PUBLIC COMPANY LIMITED
บริษัท ซีพี ออลล์ จำกัด (มหาชน)
เลขประจำตัวผู้เสียภาษี 0107542000011
Receipt
ใบเสร็จรับเงิน
ต้นฉบับ
รหัสลูกค้า : 3810981
หจก. อิงฟ้า คอนวีเนียนซ์สโตร์
เลขที่ : 2600049608
วันที่ : 18.09.2026
ชำระค่า
ผ่อนเงินสำรอง รถเข็นลัง เดือน 08/69 165.00
รวม (บาท)
จำนวนเงินที่ชำระ 165.00
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
        self.assertEqual(values.period_date, "01/08/69")
        september = IncomeFormConfig(pdf_folder=Path("."), start_date="01/09/69")
        self.assertTrue(september.matches_month(values))
        self.assertFalse(IncomeFormConfig(pdf_folder=Path("."), start_date="01/08/69").matches_month(values))

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

    def test_rent_receipt_lines_without_vat(self) -> None:
        values = extract_income_values(_RECEIPT_RENT)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.kind, INCOME_RV_RENT)
        self.assertEqual(values.invoice_number, "2800009248")
        self.assertEqual(values.branch_last5, "00245")
        form = IncomeFormConfig(pdf_folder=Path("."), start_date="01/08/69")
        self.assertEqual(IncomeInsertService.description(values, form), "บมจ.ซีพีออลล์-ค่าเช่ารับ ด.7/69*00245")
        voucher = IncomeInsertService.voucher(values, form)
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_INCOME_RECEIVABLE, 7618.65, False),
                (ACCOUNT_INCOME_WHT, 400.98, False),
                (ACCOUNT_INCOME_RENT, 8019.63, True),
            ],
        )
        with (
            mock.patch("services.income_insert_service.ExpressJournalService.insert", return_value="RV6908-0001"),
            mock.patch("services.income_insert_service.ExpressVatService.insert") as vat_insert,
        ):
            IncomeInsertService.insert(Path("."), values, form)
        vat_insert.assert_not_called()

    def test_rent_receipt_from_ocr_stacked_totals(self) -> None:
        values = extract_income_values(_RECEIPT_RENT_OCR)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.kind, INCOME_RV_RENT)
        self.assertEqual((values.total_amount, values.wht_amount, values.vat_amount), (7618.65, 400.98, 0.0))

    def test_branch_prefers_customer_code_over_glued_date(self) -> None:
        text = _RECEIPT_RENT_OCR.replace(
            "10506007724078 31.07.2026",
            "6007724098} 31.07.2026381,132.22",
        )
        values = extract_income_values(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.branch_last5, "00245")

    def test_pdf_name_takes_password_after_last_underscore(self) -> None:
        self.assertEqual(IncomePdfName.parse(Path("สมยศ_1234.pdf")).password, "1234")
        self.assertEqual(IncomePdfName.parse(Path("หจก_สมยศ_ab12.pdf")).password, "ab12")
        self.assertEqual(IncomePdfName.parse(Path("สมยศ.pdf")).password, "")
        self.assertTrue(IncomeLockMode.parse(INCOME_LOCK_PASSWORD).is_locked)
        self.assertFalse(IncomeLockMode.parse("").is_locked)
        self.assertEqual(IncomeLockMode.parse("").key, INCOME_LOCK_NONE)

    def test_locked_pdf_opens_only_with_password(self) -> None:
        from pypdf import PdfWriter
        from pypdf.generic import ContentStream

        with TemporaryDirectory() as raw:
            pdf_path = Path(raw) / "สมยศ_1234.pdf"
            writer = PdfWriter()
            page = writer.add_blank_page(width=200, height=200)
            page.replace_contents(ContentStream(None, writer))
            writer.encrypt("1234", algorithm="RC4-128")
            with pdf_path.open("wb") as handle:
                writer.write(handle)
            wrong = IncomePdfService.load_record(pdf_path, "9999")
            empty = IncomePdfService.load_record(pdf_path)
            right = IncomePdfService.load_record(pdf_path, IncomePdfName.parse(pdf_path).password)
        self.assertTrue(wrong.locked)
        self.assertTrue(empty.locked)
        self.assertFalse(right.locked)

    def test_report_groups_branches_and_adds_red_total(self) -> None:
        def invoice(name: str, branch: str, kind: str, total: float, wht: float, vat: float, base: float = 0.0):
            return IncomeFormValues(
                company_name=name,
                branch_last5=branch,
                invoice_date="14/08/69",
                invoice_number="2900000000",
                tax_id="0107542000011",
                total_amount=total,
                wht_amount=wht,
                vat_amount=vat,
                bill_count=1,
                kind=kind,
                base_amount=base,
                shop_tax_id="0103545013692",
            )

        invoices = [
            invoice("หจก. อรพรรณ", "00435", INCOME_RV_TAX, 208448.86, 6012.95, 14030.21),
            invoice("หจก. อรพรรณ", "00245", INCOME_RV_TAX, 396377.51, 11433.97, 26679.26),
            invoice("หจก. อรพรรณ", "00245", INCOME_PV_TAX, 1040.0, 30.0, 70.0, base=1000.0),
            invoice("หจก. อรพรรณ", "00245", INCOME_RV_RENT, 7618.65, 400.98, 0.0),
            invoice("หจก. สมยศ", "00111", INCOME_RV_TAX, 1070.0, 30.0, 70.0),
        ]
        rows = IncomeReportService.build_rows(invoices)
        self.assertEqual([(row.branch, row.number, row.is_total) for row in rows], [
            ("00245", None, False),
            ("00435", None, False),
            ("", 1, True),
            ("00111", 2, False),
        ])
        self.assertEqual(rows[0].amounts, (381132.22, 26679.26, 11433.97, 1000.0, 70.0, 30.0))
        self.assertEqual(rows[2].income, round(381132.22 + 200431.6, 2))
        self.assertEqual(rows[3].income, 1030.0)

        with TemporaryDirectory() as raw:
            path = IncomeReportService.write(Path(raw), "15/08/69", rows)
            from openpyxl import load_workbook

            sheet = load_workbook(path).active
            self.assertEqual(path.name, "รายได้ 8.69.xlsx")
            self.assertEqual(sheet.title, "vat 2026 08")
            self.assertEqual(sheet["B2"].value, "นิติบุคคล")
            self.assertEqual(sheet["C3"].value, "0103545013692")
            self.assertEqual(sheet["A5"].value, 1)
            self.assertEqual(sheet["E5"].font.color.rgb, "FFFF0000")
            self.assertNotEqual(getattr(sheet["E3"].font.color, "rgb", None), "FFFF0000")

    def test_shop_tax_id_skips_cpall(self) -> None:
        values = extract_income_pv_tax(_CPALL_PV_TAX)
        assert values is not None
        self.assertEqual(values.shop_tax_id, "0123549005198")

    def test_broken_page_does_not_skip_whole_pdf(self) -> None:
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, NameObject

        with TemporaryDirectory() as raw:
            pdf_path = Path(raw) / "broken.pdf"
            writer = PdfWriter()
            for data in (b"BT [ (cut", b""):
                page = writer.add_blank_page(width=200, height=200)
                stream = DecodedStreamObject()
                stream.set_data(data)
                page[NameObject("/Contents")] = writer._add_object(stream)
            with pdf_path.open("wb") as handle:
                writer.write(handle)
            record = IncomePdfService.load_record(pdf_path)
        self.assertFalse(record.locked)
        self.assertEqual(record.broken_pages, [1])

    def test_reads_cpall_pv_tax_invoice(self) -> None:
        self.assertEqual(extract_income_values(_SAMPLE).kind, INCOME_RV_TAX)
        values = extract_income_pv_tax(_CPALL_PV_TAX)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(extract_income_values(_CPALL_PV_TAX).kind, INCOME_PV_TAX)
        self.assertEqual(values.kind, INCOME_PV_TAX)
        self.assertEqual(values.company_name, "หจก. 3325 เอ็น เอ็น พี")
        self.assertEqual(values.branch_last5, "08734")
        self.assertEqual(values.invoice_date, "20/02/69")
        self.assertEqual(values.invoice_number, "2600008431")
        self.assertEqual(values.tax_id, "0107542000011")
        self.assertEqual(values.base_amount, 1000.0)
        self.assertEqual(values.vat_amount, 70.0)
        self.assertEqual(values.wht_amount, 30.0)
        self.assertEqual(values.total_amount, 1040.0)
        self.assertEqual(values.period_date, "01/08/69")
        tax27 = extract_income_pv_tax(
            _CPALL_PV_TAX.replace("2600008431", "2700015438").replace("20.02.2026", "18.09.2026")
        )
        self.assertIsNotNone(tax27)
        assert tax27 is not None
        self.assertEqual(tax27.invoice_number, "2700015438")
        self.assertEqual(tax27.invoice_date, "18/09/69")
        september = IncomeFormConfig(pdf_folder=Path("."), start_date="01/09/69")
        self.assertTrue(september.matches_month(tax27))
        self.assertFalse(IncomeFormConfig(pdf_folder=Path("."), start_date="01/08/69").matches_month(tax27))
        ocr = extract_income_pv_tax(_CPALL_PV_TAX_OCR)
        self.assertIsNotNone(ocr)
        assert ocr is not None
        self.assertEqual(extract_income_values(_CPALL_PV_TAX_OCR).kind, INCOME_PV_TAX)
        self.assertEqual(ocr.kind, INCOME_PV_TAX)
        self.assertEqual(ocr.invoice_number, "2700015438")
        self.assertEqual(ocr.base_amount, 10000.0)
        self.assertEqual(ocr.vat_amount, 700.0)
        self.assertEqual(ocr.wht_amount, 300.0)
        self.assertEqual(ocr.total_amount, 10400.0)

    def test_reads_cpall_pv_receipt_splits(self) -> None:
        values = extract_income_pv_receipt(_CPALL_PV_RECEIPT)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(extract_income_values(_CPALL_PV_RECEIPT).kind, INCOME_PV_RECEIPT)
        self.assertIsNone(extract_income_pv_tax(_CPALL_PV_RECEIPT))
        self.assertEqual(values.kind, INCOME_PV_RECEIPT)
        self.assertEqual(values.vat_amount, 0.0)
        self.assertEqual(values.company_name, "หจก. อิงฟ้า คอนวีเนียนซ์สโตร์")
        self.assertEqual(values.branch_last5, "10981")
        self.assertEqual(values.invoice_number, "2600049608")
        self.assertEqual(values.tax_id, "0107542000011")
        self.assertEqual(values.base_amount, 297.0)
        self.assertEqual(values.deposit_amount, 10132.75)
        self.assertEqual(values.total_amount, 10429.75)
        self.assertEqual(values.invoice_date, "18/09/69")
        ocr = extract_income_pv_receipt(_CPALL_PV_RECEIPT_OCR)
        self.assertIsNotNone(ocr)
        assert ocr is not None
        self.assertEqual(ocr.invoice_date, "18/09/69")
        self.assertEqual(ocr.invoice_number, "2600049608")
        self.assertEqual(ocr.base_amount, 297.0)
        self.assertEqual(ocr.deposit_amount, 10132.75)
        self.assertEqual(ocr.total_amount, 10429.75)
        deposit = extract_income_pv_receipt(_CPALL_PV_DEPOSIT_ONLY)
        self.assertIsNotNone(deposit)
        assert deposit is not None
        self.assertEqual(deposit.deposit_amount, 8000.0)
        self.assertEqual(deposit.base_amount, 0.0)
        install = extract_income_pv_receipt(_CPALL_PV_INSTALL_ONLY)
        self.assertIsNotNone(install)
        assert install is not None
        self.assertEqual(install.base_amount, 165.0)
        self.assertEqual(install.deposit_amount, 0.0)


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
        august = IncomeFormValues(
            company_name="หจก. ทดสอบ",
            branch_last5="70064",
            invoice_date="18/09/69",
            invoice_number="2900054763",
            tax_id="0107542000011",
            total_amount=100.0,
            wht_amount=0.0,
            vat_amount=0.0,
            bill_count=1,
            period_date="01/08/69",
        )
        july = IncomeFormValues(
            company_name="หจก. ทดสอบ",
            branch_last5="70064",
            invoice_date="18/08/69",
            invoice_number="2900054763",
            tax_id="0107542000011",
            total_amount=100.0,
            wht_amount=0.0,
            vat_amount=0.0,
            bill_count=1,
            period_date="01/07/69",
        )
        september = IncomeFormConfig(pdf_folder=Path("."), start_date="01/09/69")
        self.assertTrue(september.matches_month(august))
        self.assertFalse(form.matches_month(august))
        self.assertTrue(form.matches_month(july))
        self.assertFalse(september.matches_month(july))
        self.assertEqual(
            IncomeInsertService.description(august, september),
            "บมจ.ซีพีออลล์-ค่าตอบแทนการบริหาร ด.8/69*70064",
        )

    def test_pv_tax_lines_and_description(self) -> None:
        values = extract_income_pv_tax(_CPALL_PV_TAX)
        self.assertIsNotNone(values)
        assert values is not None
        form = IncomeFormConfig(pdf_folder=Path("."), start_date="01/08/69")
        self.assertEqual(
            IncomeInsertService.description(values, form),
            "บมจ.ซีพี ออลล์-ค่าสิทธ์ ด.8/69*08734",
        )
        july = IncomeFormConfig(pdf_folder=Path("."), start_date="01/07/69")
        self.assertEqual(
            IncomeInsertService.description(values, july),
            "บมจ.ซีพี ออลล์-ค่าสิทธ์ ด.8/69*08734",
        )
        voucher = IncomeInsertService.voucher(values, form)
        self.assertEqual(voucher.jnltyp, "01")
        self.assertEqual(voucher.prefix, "PV")
        self.assertEqual(voucher.voudat_express, "20/02/69")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_INCOME_ADVANCE, 1000.0, False),
                (ACCOUNT_VAT, 70.0, False),
                (ACCOUNT_WT, 30.0, True),
                (ACCOUNT_INCOME_RECEIVABLE, 1040.0, True),
            ],
        )
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in pv_income_tax(values, "20/02/69", "x").lines],
            [
                (ACCOUNT_INCOME_ADVANCE, 1000.0, False),
                (ACCOUNT_VAT, 70.0, False),
                (ACCOUNT_WT, 30.0, True),
                (ACCOUNT_INCOME_RECEIVABLE, 1040.0, True),
            ],
        )
        self.assertEqual(VATREC_SALE, "S")

    def test_pv_receipt_lines_and_description(self) -> None:
        values = extract_income_pv_receipt(_CPALL_PV_RECEIPT)
        self.assertIsNotNone(values)
        assert values is not None
        form = IncomeFormConfig(pdf_folder=Path("."), start_date="01/07/69")
        self.assertEqual(
            IncomeInsertService.description(values, form),
            "บมจ.ซีพีออลล์-ผ่อนเงินสำรอง,เงินประกัน 8/69*10981",
        )
        voucher = IncomeInsertService.voucher(values, form)
        self.assertEqual(voucher.jnltyp, "01")
        self.assertEqual(voucher.prefix, "PV")
        self.assertEqual(voucher.voudat_express, "18/09/69")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_INCOME_DEPOSIT, 10132.75, False),
                (ACCOUNT_INCOME_ADVANCE, 297.0, False),
                (ACCOUNT_INCOME_RECEIVABLE, 10429.75, True),
            ],
        )
        self.assertNotIn(ACCOUNT_VAT, [line.account for line in voucher.lines])
        with (
            mock.patch("services.income_pv_insert_service.ExpressJournalService.insert", return_value="PV6909-0001"),
            mock.patch("services.income_pv_insert_service.ExpressVatService.insert") as vat_insert,
        ):
            self.assertEqual(IncomeInsertService.insert(Path("."), values, form), "PV6909-0001")
        vat_insert.assert_not_called()
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in pv_income_receipt(values, "18/09/69", "x").lines],
            [
                (ACCOUNT_INCOME_DEPOSIT, 10132.75, False),
                (ACCOUNT_INCOME_ADVANCE, 297.0, False),
                (ACCOUNT_INCOME_RECEIVABLE, 10429.75, True),
            ],
        )
        deposit = extract_income_pv_receipt(_CPALL_PV_DEPOSIT_ONLY)
        self.assertIsNotNone(deposit)
        assert deposit is not None
        self.assertEqual(
            IncomeInsertService.description(deposit, form),
            "บมจ.ซีพีออลล์-เงินประกัน ด.8/69*10981",
        )
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in IncomeInsertService.voucher(deposit, form).lines],
            [
                (ACCOUNT_INCOME_DEPOSIT, 8000.0, False),
                (ACCOUNT_INCOME_RECEIVABLE, 8000.0, True),
            ],
        )
        install = extract_income_pv_receipt(_CPALL_PV_INSTALL_ONLY)
        self.assertIsNotNone(install)
        assert install is not None
        self.assertEqual(
            IncomeInsertService.description(install, form),
            "บมจ.ซีพีออลล์-ผ่อนเงินสำรอง ด.8/69*10981",
        )
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in IncomeInsertService.voucher(install, form).lines],
            [
                (ACCOUNT_INCOME_ADVANCE, 165.0, False),
                (ACCOUNT_INCOME_RECEIVABLE, 165.0, True),
            ],
        )

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
        form = IncomeFormConfig(pdf_folder=Path("."), start_date="01/09/69")
        with (
            mock.patch("services.income_insert_service.ExpressJournalService.insert", return_value="RV6909-0001"),
            mock.patch("services.income_insert_service.ExpressVatService.insert") as vat_insert,
        ):
            self.assertEqual(IncomeInsertService.insert(Path("."), goods, form), "RV6909-0001")
            self.assertEqual(IncomeInsertService.insert(Path("."), advance, form), "RV6909-0001")
        vat_insert.assert_not_called()

    def test_form_needs_pdf_folder(self) -> None:
        errors = IncomeFormConfig(pdf_folder=Path("/no-folder")).validate()
        self.assertTrue(any("โฟลเดอร์" in item for item in errors))
        self.assertTrue(any("วันที่" in item for item in errors))
        self.assertFalse(any("Excel" in item for item in errors))


if __name__ == "__main__":
    unittest.main()

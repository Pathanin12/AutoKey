import unittest

from pathlib import Path

from constants.date_utils import format_express_pv_date, is_complete_express_date
from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_PP30_DECIMAL,
    ACCOUNT_PP30_NEW_SHOP,
    ACCOUNT_PP30_PENALTY,
    ACCOUNT_PP30_VAT_PAYABLE,
    ACCOUNT_PP30_VAT_PURCHASE,
    ACCOUNT_PP30_VAT_SALE,
)
from models.month_year_period import MonthYearPeriod
from models.pp30_form_config import Pp30FormConfig
from models.pp30_form_values import Pp30FormValues
from models.pp30_payment_kind import Pp30PaymentKind
from services.pp30_insert_lines_service import (
    jv_new_shop,
    jv_no_pay_normal,
    jv_normal,
    jv_pay,
    pv_pay_or_normal,
    pv_penalty,
)
from services.pnd30_extract_service import extract_is_amendment
from services.pp30_insert_service import Pp30InsertService
from services.pp30_pdf_service import Pp30PdfService

_PERIOD = MonthYearPeriod(month=8, year=69)

def _values(**kwargs) -> Pp30FormValues:
    data = dict(
        vat_sale=0.0,
        vat_purchase=0.0,
        amount_due=0.0,
        pv_date="18/09/69",
    )
    data.update(kwargs)
    return Pp30FormValues(**data)


class Pp30InsertLinesTests(unittest.TestCase):
    def test_jv_date_must_be_complete(self) -> None:
        self.assertFalse(is_complete_express_date(""))
        self.assertFalse(is_complete_express_date("31/08"))
        self.assertTrue(is_complete_express_date("31/08/69"))
        self.assertTrue(is_complete_express_date("25/7/69"))
        self.assertTrue(is_complete_express_date("250769"))
        self.assertTrue(is_complete_express_date("2026-10-10"))
        self.assertEqual(format_express_pv_date("25/7/69"), "25/07/69")
        self.assertEqual(format_express_pv_date("250769"), "25/07/69")
        self.assertEqual(format_express_pv_date("2026-10-10"), "10/10/69")

    def test_insert_uses_form_jv_date(self) -> None:
        values = _values(vat_sale=14238, vat_purchase=784, amount_due=13454, line_8=13454)
        form = Pp30FormConfig(
            pdf_folder=Path("."),
            jv_period=_PERIOD,
            pv_period=_PERIOD,
            jv_date="15/07/69",
        )
        vouchers = Pp30InsertService.vouchers(Pp30PaymentKind.normal(), values, form)
        self.assertEqual(vouchers[0].voudat_express, "15/07/69")
        self.assertEqual(vouchers[1].voudat_express, "18/09/69")

    def test_normal_jv_and_pv(self) -> None:
        values = _values(vat_sale=14238, vat_purchase=784, amount_due=13454, line_8=13454)
        jv = jv_normal(values, "31/08/69", "ปิดภาษี")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in jv.lines],
            [
                (ACCOUNT_PP30_VAT_SALE, 14238.0, False),
                (ACCOUNT_PP30_VAT_PURCHASE, 784.0, True),
                (ACCOUNT_PP30_VAT_PAYABLE, 13454.0, True),
            ],
        )
        pv = pv_pay_or_normal(values, "18/09/69", "ภพ.30")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in pv.lines],
            [
                (ACCOUNT_PP30_VAT_PAYABLE, 13454.0, False),
                (ACCOUNT_CASH, 13454.0, True),
            ],
        )

    def test_pay_jv_uses_line_10(self) -> None:
        values = _values(vat_sale=20000, vat_purchase=5000, amount_due=12000, line_8=15000, line_10=3000)
        jv = jv_pay(values, "31/08/69", "jv")
        self.assertEqual(jv.lines[-2].account, ACCOUNT_PP30_NEW_SHOP)
        self.assertEqual(jv.lines[-2].amount, 3000.0)
        self.assertEqual(jv.lines[-1].account, ACCOUNT_PP30_VAT_PAYABLE)
        self.assertEqual(jv.lines[-1].amount, 12000.0)

    def test_no_pay_normal_jv_only(self) -> None:
        values = _values(vat_sale=20000, vat_purchase=5000, line_8=15000, line_10=20000)
        jv = jv_no_pay_normal(values, "31/08/69", "jv")
        self.assertEqual(jv.lines[-1].account, ACCOUNT_PP30_NEW_SHOP)
        self.assertEqual(jv.lines[-1].amount, 15000.0)

    def test_skips_shop_when_line_5_and_7_empty(self) -> None:
        values = _values(line_10=137.2, line_12=137.2)
        form = Pp30FormConfig(pdf_folder=Path("."), jv_period=_PERIOD, pv_period=_PERIOD, jv_date="31/08/69")
        self.assertFalse(values.has_vat_lines)
        self.assertEqual(Pp30InsertService.vouchers(Pp30PaymentKind.no_pay_normal(), values, form), [])
        self.assertEqual(Pp30InsertService.vouchers(Pp30PaymentKind.normal(), values, form), [])

    def test_new_shop_jv(self) -> None:
        values = _values(vat_purchase=1200, line_9=1200, line_12=1200)
        jv = jv_new_shop(values, "31/08/69", "jv")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in jv.lines],
            [
                (ACCOUNT_PP30_NEW_SHOP, 1200.0, False),
                (ACCOUNT_PP30_VAT_PURCHASE, 1200.0, True),
            ],
        )

    def test_penalty_pv(self) -> None:
        values = _values(
            vat_sale=20000,
            vat_purchase=5000,
            amount_due=15000,
            line_13=100,
            line_14=50,
            line_15=15150,
        )
        pv = pv_penalty(values, "18/09/69", "pv")
        accounts = [(line.account, line.amount, line.is_credit) for line in pv.lines]
        self.assertEqual(accounts[0], (ACCOUNT_PP30_VAT_PAYABLE, 15000.0, False))
        self.assertEqual(accounts[1], (ACCOUNT_PP30_PENALTY, 150.0, False))
        self.assertEqual(accounts[-1], (ACCOUNT_CASH, 15150.0, True))

    def test_pv_decimal_uses_4200(self) -> None:
        values = _values(amount_due=13454.75)
        pv = pv_pay_or_normal(values, "18/09/69", "pv")
        self.assertEqual(pv.lines[1].account, ACCOUNT_PP30_DECIMAL)
        self.assertEqual(pv.lines[1].amount, 0.75)
        self.assertEqual(pv.lines[-1].account, ACCOUNT_CASH)
        self.assertEqual(pv.lines[-1].amount, 13454.0)

    def test_amendment_appends_to_jv_and_pv_descriptions(self) -> None:
        self.assertTrue(extract_is_amendment("ยื่นปกติüยื่นเพิ่มเติมครั้งที่........1ของ ภ.พ.30 ซึ่งยื่นไว้"))
        self.assertFalse(extract_is_amendment("5. ภาษีขายเดือนนี้                         หรือกรณียื่นเพิ่มเติม"))
        values = _values(vat_sale=14238, vat_purchase=784, amount_due=13454, line_8=13454, is_amendment=True)
        form = Pp30FormConfig(
            pdf_folder=Path("."),
            jv_period=_PERIOD,
            pv_period=_PERIOD,
            jv_date="31/08/69",
        )
        vouchers = Pp30InsertService.vouchers(Pp30PaymentKind.normal(), values, form)
        self.assertEqual(vouchers[0].description, "ปิดภาษีซื้อ-ขาย เดือน8/69 เพิ่มเติม")
        self.assertEqual(vouchers[1].description, "กรมสรรพากร-ภ.พ.30 เดือน8/69 เพิ่มเติม")


SAMPLE_AMEND_PDF = Path(
    "/Users/pathanin/.cursor/projects/Users-pathanin-job-AutoKey/attachments/"
    "95442e36-2dbc-40d8-8635-d8ec30cd3af5/________________2555.pdf"
)


class Pp30AmendmentPdfTests(unittest.TestCase):
    @unittest.skipUnless(SAMPLE_AMEND_PDF.exists(), "sample ภ.พ.30 amendment pdf")
    def test_reads_amendment_tick_from_pdf(self) -> None:
        record = Pp30PdfService.load_record(SAMPLE_AMEND_PDF)
        self.assertIsNotNone(record.form_values)
        assert record.form_values is not None
        self.assertTrue(record.form_values.is_amendment)


if __name__ == "__main__":
    unittest.main()

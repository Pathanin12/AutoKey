import unittest

from pathlib import Path

from constants.date_utils import is_complete_express_date
from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_PP30_DECIMAL,
    ACCOUNT_PP30_NEW_SHOP,
    ACCOUNT_PP30_PENALTY,
    ACCOUNT_PP30_VAT_PAYABLE,
    ACCOUNT_PP30_VAT_PURCHASE,
    ACCOUNT_PP30_VAT_SALE,
)
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
from services.pp30_insert_service import Pp30InsertService


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

    def test_insert_uses_form_jv_date(self) -> None:
        values = _values(vat_sale=14238, vat_purchase=784, amount_due=13454, line_8=13454)
        form = Pp30FormConfig(
            pdf_folder=Path("."),
            jv_description="ปิดภาษี",
            pv_description="ภพ.30",
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

    def test_no_pay_normal_skips_when_line_5_and_7_empty(self) -> None:
        values = _values(line_10=137.2, line_12=137.2)
        form = Pp30FormConfig(pdf_folder=Path("."), jv_description="jv", pv_description="pv", jv_date="31/08/69")
        self.assertEqual(Pp30InsertService.vouchers(Pp30PaymentKind.no_pay_normal(), values, form), [])

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


if __name__ == "__main__":
    unittest.main()

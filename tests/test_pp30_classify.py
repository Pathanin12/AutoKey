import unittest

from constants.routes import (
    PP30_KIND_NO_PAY_NEW_SHOP,
    PP30_KIND_NO_PAY_NORMAL,
    PP30_KIND_PAY,
    PP30_KIND_PENALTY,
    PP30_KIND_SKIP_ZERO,
    PP30_KIND_UNKNOWN,
)
from models.pp30_form_values import Pp30FormValues
from services.pp30_classify_service import Pp30ClassifyService
from services.pp30_pdf_service import Pp30PdfService


def _values(
    *,
    vat_sale: float,
    vat_purchase: float,
    amount_due: float = 0.0,
    line_8: float = 0.0,
    line_9: float = 0.0,
    line_10: float = 0.0,
    line_12: float = 0.0,
    line_13: float = 0.0,
    line_14: float = 0.0,
) -> Pp30FormValues:
    return Pp30FormValues(
        vat_sale=vat_sale,
        vat_purchase=vat_purchase,
        amount_due=amount_due,
        pv_date="13/08/69",
        line_8=line_8,
        line_9=line_9,
        line_10=line_10,
        line_12=line_12,
        line_13=line_13,
        line_14=line_14,
    )


class Pp30ClassifyServiceTests(unittest.TestCase):
    def test_skip_when_every_line_is_zero(self) -> None:
        kind = Pp30ClassifyService.classify(_values(vat_sale=0.0, vat_purchase=0.0))
        self.assertEqual(kind.key, PP30_KIND_SKIP_ZERO)
        self.assertTrue(kind.is_skip)
        self.assertEqual(kind.label, "ข้าม — ยอดเป็น 0 ทั้งหมด")

    def test_new_shop_is_not_skip_when_purchase_has_amount(self) -> None:
        kind = Pp30ClassifyService.classify(
            _values(vat_sale=0.0, vat_purchase=1200.0, line_9=1200.0, line_12=1200.0)
        )
        self.assertEqual(kind.key, PP30_KIND_NO_PAY_NEW_SHOP)
        self.assertTrue(kind.is_new_shop)
        self.assertFalse(kind.is_skip)
        self.assertFalse(kind.is_no_pay_normal)

    def test_no_pay_normal_when_line_10_greater_than_line_8(self) -> None:
        kind = Pp30ClassifyService.classify(
            _values(vat_sale=20000.0, vat_purchase=5000.0, line_8=15000.0, line_10=20000.0, line_12=5000.0)
        )
        self.assertEqual(kind.key, PP30_KIND_NO_PAY_NORMAL)
        self.assertTrue(kind.is_no_pay_normal)
        self.assertFalse(kind.is_new_shop)
        self.assertEqual(kind.label, "ไม่จ่ายตัง — แบบปกติ")

    def test_no_pay_new_shop_when_line_5_zero_and_7_9_12_equal(self) -> None:
        kind = Pp30ClassifyService.classify(
            _values(vat_sale=0.0, vat_purchase=1200.0, line_9=1200.0, line_12=1200.0)
        )
        self.assertEqual(kind.key, PP30_KIND_NO_PAY_NEW_SHOP)
        self.assertEqual(kind.label, "ไม่จ่ายตัง — เปิดร้านใหม่")

    def test_new_shop_wins_over_no_pay_normal(self) -> None:
        kind = Pp30ClassifyService.classify(
            _values(
                vat_sale=0.0,
                vat_purchase=1200.0,
                line_8=0.0,
                line_9=1200.0,
                line_10=1200.0,
                line_12=1200.0,
            )
        )
        self.assertEqual(kind.key, PP30_KIND_NO_PAY_NEW_SHOP)

    def test_pay_when_line_8_greater_than_line_10(self) -> None:
        kind = Pp30ClassifyService.classify(
            _values(vat_sale=20000.0, vat_purchase=5000.0, amount_due=12000.0, line_8=15000.0, line_10=3000.0)
        )
        self.assertEqual(kind.key, PP30_KIND_PAY)
        self.assertTrue(kind.is_pay)
        self.assertEqual(kind.label, "จ่ายตัง")

    def test_pay_when_has_line_8_without_line_10(self) -> None:
        kind = Pp30ClassifyService.classify(
            _values(vat_sale=51235.94, vat_purchase=168.0, amount_due=51067.94, line_8=51067.94)
        )
        self.assertEqual(kind.key, PP30_KIND_PAY)

    def test_penalty_when_pay_like_and_has_line_13(self) -> None:
        kind = Pp30ClassifyService.classify(
            _values(
                vat_sale=20000.0,
                vat_purchase=5000.0,
                amount_due=15000.0,
                line_8=15000.0,
                line_13=200.0,
            )
        )
        self.assertEqual(kind.key, PP30_KIND_PENALTY)
        self.assertTrue(kind.is_penalty)
        self.assertEqual(kind.label, "เสียค่าปรับ")

    def test_penalty_when_pay_like_and_has_line_14(self) -> None:
        kind = Pp30ClassifyService.classify(
            _values(
                vat_sale=20000.0,
                vat_purchase=5000.0,
                amount_due=15000.0,
                line_8=15000.0,
                line_14=500.0,
            )
        )
        self.assertEqual(kind.key, PP30_KIND_PENALTY)

    def test_penalty_needs_pay_like_not_just_line_13(self) -> None:
        kind = Pp30ClassifyService.classify(
            _values(vat_sale=20000.0, vat_purchase=5000.0, line_8=15000.0, line_10=20000.0, line_13=200.0)
        )
        self.assertEqual(kind.key, PP30_KIND_NO_PAY_NORMAL)

    def test_unknown_when_line_8_equals_line_10(self) -> None:
        kind = Pp30ClassifyService.classify(
            _values(vat_sale=20000.0, vat_purchase=5000.0, line_8=15000.0, line_10=15000.0)
        )
        self.assertEqual(kind.key, PP30_KIND_UNKNOWN)


class Pp30ExtractKindTests(unittest.TestCase):
    def test_sample_rd_form_is_pay(self) -> None:
        text = """
ห้างหุ้นส่วนจำกัด เจนสิริการค้า
5. ภาษีขายเดือนนี้
7. ภาษีซื้อเดือนนี้
11. ต้องชำระ
731,941.96
51,235.94
168.00
51,067.94
51,067.94
ยื่นวันที่่ 13 เดือน สิงหาคม พ.ศ. 2569
"""
        values = Pp30PdfService.extract_form_values(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(Pp30ClassifyService.classify(values).key, PP30_KIND_PAY)

    def test_extracts_new_shop_from_labeled_zero_sale(self) -> None:
        text = """
5. ภาษีขายเดือนนี้ 0.00
7. ภาษีซื้อเดือนนี้ 1,200.00
9. ภาษีที่ชำระเกินเดือนนี้ 1,200.00
12. ชำระเกิน 1,200.00
ยื่นวันที่่ 13 เดือน สิงหาคม พ.ศ. 2569
"""
        values = Pp30PdfService.extract_form_values(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.line_5, 0.0)
        self.assertEqual(values.line_7, 1200.0)
        self.assertEqual(values.line_9, 1200.0)
        self.assertEqual(values.line_12, 1200.0)
        self.assertEqual(Pp30ClassifyService.classify(values).key, PP30_KIND_NO_PAY_NEW_SHOP)

    def test_extracts_no_pay_normal_when_line_10_greater(self) -> None:
        text = """
5. ภาษีขายเดือนนี้ 20,000.00
7. ภาษีซื้อเดือนนี้ 5,000.00
8. ภาษีที่ต้องชำระเดือนนี้ 15,000.00
10. ภาษีที่ชำระเกินยกมา 20,000.00
12. ชำระเกิน 5,000.00
ยื่นวันที่่ 13 เดือน สิงหาคม พ.ศ. 2569
"""
        values = Pp30PdfService.extract_form_values(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.line_8, 15000.0)
        self.assertEqual(values.line_10, 20000.0)
        self.assertEqual(Pp30ClassifyService.classify(values).key, PP30_KIND_NO_PAY_NORMAL)

    def test_extracts_overpay_carry_when_amounts_are_dumped(self) -> None:
        text = """
ห้างหุ้นส่วนจำกัด ฐานพัฒน์ 88
5. ภาษีขายเดือนนี้
7. ภาษีซื้อเดือนนี้
8. ภาษีที่ต้องชำระเดือนนี้
10. ภาษีที่ชำระเกินยกมา
12. ชำระเกิน
335,655.30
23,495.87
1,200.00
84.00
23,411.87
171,572.80
148,160.93
ยื่นวันที่่ 17 เดือน สิงหาคม พ.ศ. 2569
จำนวนเงิน 0.00 บาท
"""
        values = Pp30PdfService.extract_form_values(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.line_5, 23495.87)
        self.assertEqual(values.line_7, 84.0)
        self.assertEqual(values.line_8, 23411.87)
        self.assertEqual(values.line_10, 171572.80)
        self.assertEqual(values.line_11, 0.0)
        self.assertEqual(values.line_12, 148160.93)
        self.assertEqual(Pp30ClassifyService.classify(values).key, PP30_KIND_NO_PAY_NORMAL)

    def test_extracts_penalty_from_line_13(self) -> None:
        text = """
5. ภาษีขายเดือนนี้ 20,000.00
7. ภาษีซื้อเดือนนี้ 5,000.00
8. ภาษีที่ต้องชำระเดือนนี้ 15,000.00
11. ต้องชำระ 15,000.00
13. เงินเพิ่ม 200.00
ยื่นวันที่่ 13 เดือน สิงหาคม พ.ศ. 2569
"""
        values = Pp30PdfService.extract_form_values(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.line_13, 200.0)
        self.assertEqual(values.penalty_amount, 200.0)
        self.assertEqual(values.line_15, 15200.0)
        self.assertEqual(Pp30ClassifyService.classify(values).key, PP30_KIND_PENALTY)

    def test_extracts_penalty_from_line_14(self) -> None:
        text = """
5. ภาษีขายเดือนนี้ 20,000.00
7. ภาษีซื้อเดือนนี้ 5,000.00
8. ภาษีที่ต้องชำระเดือนนี้ 15,000.00
11. ต้องชำระ 15,000.00
14. เบี้ยปรับ 500.00
ยื่นวันที่่ 13 เดือน สิงหาคม พ.ศ. 2569
"""
        values = Pp30PdfService.extract_form_values(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.line_14, 500.0)
        self.assertEqual(values.penalty_amount, 500.0)
        self.assertEqual(values.line_15, 15500.0)
        self.assertEqual(Pp30ClassifyService.classify(values).key, PP30_KIND_PENALTY)

    def test_extracts_penalty_line_13_plus_14_and_labeled_15(self) -> None:
        text = """
5. ภาษีขายเดือนนี้ 20,000.00
7. ภาษีซื้อเดือนนี้ 5,000.00
8. ภาษีที่ต้องชำระเดือนนี้ 15,000.00
11. ต้องชำระ 15,000.00
13. เงินเพิ่ม 200.00
14. เบี้ยปรับ 50.50
15. รวมภาษีที่ต้องชำระทั้งสิ้น 15,250.50
ยื่นวันที่่ 13 เดือน สิงหาคม พ.ศ. 2569
"""
        values = Pp30PdfService.extract_form_values(text)
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.penalty_amount, 250.50)
        self.assertEqual(values.line_15, 15250.50)
        self.assertEqual(values.line_15_decimal, 0.50)
        self.assertEqual(Pp30ClassifyService.classify(values).key, PP30_KIND_PENALTY)


if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import datetime
from pathlib import Path

from constants.routes import ACCOUNT_CASH, ACCOUNT_WCF_CONTRIB, ACCOUNT_WCF_PENALTY, UI_TEXT
from models.wcf_form_config import WcfFormConfig
from models.wcf_row import WcfRow
from services.wcf_excel_service import WcfExcelService, match_name, parse_wcf_pay_date
from services.wcf_insert_lines_service import pv_wcf
from services.wcf_insert_service import WcfInsertService
from services.wcf_match_run_service import WcfMatchRunService

SAMPLE_XLSX = Path("/Users/pathanin/Downloads/กองทุนเงินทดแทน 2569.xlsx")


class WcfExcelTests(unittest.TestCase):
    def test_strips_shop_code_for_match(self) -> None:
        self.assertEqual(match_name("กษิดิศเกรียงไกร (6582)"), "กษิดิศเกรียงไกร")

    def test_reads_date_with_or_without_time(self) -> None:
        self.assertEqual(parse_wcf_pay_date("05/01/2569"), "05/01/69")
        self.assertEqual(parse_wcf_pay_date("05/01/2569 16:28"), "05/01/69")
        self.assertEqual(parse_wcf_pay_date("05/01/2569เวลา16:28 น."), "05/01/69")
        self.assertEqual(parse_wcf_pay_date(datetime(2026, 1, 5, 16, 28)), "05/01/69")

    @unittest.skipUnless(SAMPLE_XLSX.exists(), "sample WCF excel")
    def test_reads_sample_excel(self) -> None:
        rows = WcfExcelService.load_rows(SAMPLE_XLSX)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.shop_name, "กษิดิศเกรียงไกร (6582)")
        self.assertEqual(row.match_name, "กษิดิศเกรียงไกร")
        self.assertEqual(row.pv_date, "05/01/69")
        self.assertEqual(row.contrib_amount, 5200.00)
        self.assertFalse(row.has_surcharge)
        self.assertEqual(row.paid_amount, 5200.00)
        self.assertEqual(row.period, "1/69")
        self.assertEqual(row.receipt_no, "720069100000666")


class WcfInsertLinesTests(unittest.TestCase):
    def test_contrib_then_cash(self) -> None:
        row = WcfRow(
            row_number=2,
            shop_name="กษิดิศเกรียงไกร (6582)",
            match_name="กษิดิศเกรียงไกร",
            pv_date="05/01/69",
            contrib_amount=5200.00,
            surcharge=0.0,
            paid_amount=5200.00,
            period="1/69",
        )
        voucher = pv_wcf(row, "05/01/69", "สำนักงานประกันสังคม-กองทุนเงินทดแทน")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_WCF_CONTRIB, 5200.00, False),
                (ACCOUNT_CASH, 5200.00, True),
            ],
        )
        self.assertEqual(ACCOUNT_WCF_CONTRIB, "5310-10")
        self.assertEqual(ACCOUNT_WCF_PENALTY, "5370-06")

    def test_surcharge_before_cash(self) -> None:
        row = WcfRow(
            row_number=2,
            shop_name="กษิดิศเกรียงไกร",
            match_name="กษิดิศเกรียงไกร",
            pv_date="05/01/69",
            contrib_amount=5000.00,
            surcharge=50.00,
            paid_amount=5050.00,
            period="1/69",
        )
        voucher = pv_wcf(row, "05/01/69", "สำนักงานประกันสังคม-กองทุนเงินทดแทน *1")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_WCF_CONTRIB, 5000.00, False),
                (ACCOUNT_WCF_PENALTY, 50.00, False),
                (ACCOUNT_CASH, 5050.00, True),
            ],
        )

    def test_form_description_and_duplicate_suffix(self) -> None:
        form = WcfFormConfig(excel_path=Path("."), row_count=1)
        self.assertEqual(form.description_for(), "สำนักงานประกันสังคม-กองทุนเงินทดแทน")
        self.assertEqual(form.description_for(1), "สำนักงานประกันสังคม-กองทุนเงินทดแทน *1")
        row = WcfRow(
            row_number=2,
            shop_name="กษิดิศเกรียงไกร",
            match_name="กษิดิศเกรียงไกร",
            pv_date="05/01/69",
            contrib_amount=5200.00,
            surcharge=0.0,
            paid_amount=5200.00,
            period="1/69",
        )
        voucher = WcfInsertService.voucher(row, form, dup_n=1)
        self.assertEqual(voucher.description, "สำนักงานประกันสังคม-กองทุนเงินทดแทน *1")
        self.assertEqual(voucher.voudat_express, "05/01/69")
        self.assertEqual(WcfMatchRunService.dup_star(2, 2), 2)

    def test_form_needs_excel(self) -> None:
        errors = WcfFormConfig(excel_path=Path("/no-file.xlsx"), row_count=0).validate()
        self.assertIn(UI_TEXT["wcf_excel_invalid"], errors)


if __name__ == "__main__":
    unittest.main()

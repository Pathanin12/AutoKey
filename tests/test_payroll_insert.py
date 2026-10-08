import unittest
from pathlib import Path

from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_PAYROLL_SALARY,
    ACCOUNT_PAYROLL_SSO10,
    ACCOUNT_PAYROLL_SSO5,
    ACCOUNT_PAYROLL_WELFARE,
    ACCOUNT_WT_PND1,
    UI_TEXT,
)
from models.month_year_period import MonthYearPeriod
from models.payroll_form_config import PayrollFormConfig
from models.payroll_row import PayrollRow
from services.payroll_excel_service import PayrollExcelService
from services.payroll_insert_lines_service import pv_payroll
from services.payroll_insert_service import PayrollInsertService

SAMPLE_XLSX = Path("/Users/pathanin/Downloads/03.Ploy Exp.xlsx")


class PayrollExcelTests(unittest.TestCase):
    @unittest.skipUnless(SAMPLE_XLSX.exists(), "sample payroll excel")
    def test_reads_only_selected_month(self) -> None:
        jan = PayrollExcelService.load_rows(SAMPLE_XLSX, MonthYearPeriod.parse("01/69"))
        feb = PayrollExcelService.load_rows(SAMPLE_XLSX, MonthYearPeriod.parse("02/69"))
        self.assertEqual(jan[0].legal_name, "วรกร 8891")
        self.assertEqual(jan[0].salary, 225638.75)
        self.assertEqual(jan[0].sso5, 4330.00)
        self.assertEqual(jan[0].sso10, 8660.00)
        self.assertEqual(jan[0].net, 221308.75)
        self.assertTrue(jan[0].has_salary)
        zero = next(row for row in jan if row.legal_name == "วีพีมาร์ท")
        self.assertFalse(zero.has_salary)
        self.assertNotEqual(jan[0].salary, feb[0].salary)
        self.assertEqual(feb[0].salary, 205358.75)

    @unittest.skipUnless(SAMPLE_XLSX.exists(), "sample payroll excel")
    def test_missing_month_raises(self) -> None:
        with self.assertRaises(ValueError) as caught:
            PayrollExcelService.load_rows(SAMPLE_XLSX, MonthYearPeriod.parse("12/50"))
        self.assertIn("12/50", str(caught.exception))


class PayrollInsertLinesTests(unittest.TestCase):
    def test_debit_then_credit_skipping_zero(self) -> None:
        row = PayrollRow(
            row_number=3,
            legal_name="วรกร 8891",
            match_names=("วรกร 8891", "วรกร"),
            salary=225638.75,
            sso5=4330.00,
            welfare025=0.0,
            sso10=8660.00,
            welfare=0.0,
            tax=0.0,
            net=221308.75,
        )
        voucher = pv_payroll(row, "25/03/69", "จ่ายเงินเดือนและประกันสังคม เดือน 3/69")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_PAYROLL_SALARY, 225638.75, False),
                (ACCOUNT_PAYROLL_SSO5, 4330.00, False),
                (ACCOUNT_PAYROLL_SSO10, 8660.00, True),
                (ACCOUNT_CASH, 221308.75, True),
            ],
        )

    def test_includes_welfare_and_tax(self) -> None:
        row = PayrollRow(
            row_number=4,
            legal_name="มหาไชยทรัพย์อนันต์",
            match_names=("มหาไชยทรัพย์อนันต์",),
            salary=285833.00,
            sso5=7315.00,
            welfare025=10.00,
            sso10=14630.00,
            welfare=20.00,
            tax=590.00,
            net=277928.00,
        )
        voucher = pv_payroll(row, "25/01/69", "จ่ายเงินเดือนและประกันสังคม เดือน 1/69")
        self.assertEqual(
            [line.account for line in voucher.lines],
            [
                ACCOUNT_PAYROLL_SALARY,
                ACCOUNT_PAYROLL_SSO5,
                "5310-20",
                ACCOUNT_PAYROLL_SSO10,
                ACCOUNT_PAYROLL_WELFARE,
                ACCOUNT_WT_PND1,
                ACCOUNT_CASH,
            ],
        )

    def test_form_description_from_ui_period(self) -> None:
        form = PayrollFormConfig(
            excel_path=Path("."),
            pv_date="25/03/69",
            period=MonthYearPeriod.parse("03/69"),
            row_count=1,
        )
        self.assertEqual(form.description, "จ่ายเงินเดือนและประกันสังคม เดือน 3/69")
        row = PayrollRow(2, "x", ("x",), 100.0, 0, 0, 0, 0, 0, 100.0)
        self.assertEqual(PayrollInsertService.voucher(row, form).voudat_express, "25/03/69")
        self.assertTrue(row.has_salary)
        self.assertFalse(
            PayrollRow(3, "zero", ("zero",), 0.0, 10.0, 0, 20.0, 0, 0, 0.0).has_salary
        )

    def test_form_needs_date_and_period(self) -> None:
        errors = PayrollFormConfig(
            excel_path=Path("/no-file.xlsx"),
            pv_date="",
            period=MonthYearPeriod.parse(""),
            row_count=0,
        ).validate()
        self.assertIn(UI_TEXT["payroll_excel_invalid"], errors)
        self.assertIn(UI_TEXT["payroll_pv_date_invalid"], errors)
        self.assertIn(UI_TEXT["payroll_period_invalid"], errors)


if __name__ == "__main__":
    unittest.main()

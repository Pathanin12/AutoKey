import tempfile
import unittest
from pathlib import Path

from constants.date_utils import express_month_date_range, express_month_folder_name, express_year_start_date
from constants.routes import (
    ACCOUNT_SERVICE,
    ACCOUNT_VAT,
    ACCOUNT_WT,
    ACCOUNT_PP30_NEW_SHOP,
    PP30_ACCOUNT_REPORT_CODES,
    PP30_NEW_SHOP_REPORT_CODES,
    PP30_NO_PAY_NORMAL_REPORT_CODES,
    PP30_PAY_REPORT_CODES,
    PP30_PENALTY_REPORT_CODES,
)
from constants.template_actions import F12_MENU_REGION, REPORT_NORMAL_ACTION_IDS
from models.ka_tam_row import KaTamRow
from models.ledger_range_report_form import LedgerRangeReportForm
from models.ledger_report_open_plan import LedgerReportOpenPlan
from models.report_output_layout import ReportOutputLayout, safe_folder_name
from models.run_config import RunConfig
from services.account_report_capture_legacy_service import report_reopen_retries
from services.account_report_capture_service import (
    build_account_report_jobs,
    build_ledger_report_jobs,
    should_expand_ledger_report_tree,
)


class AccountReportTests(unittest.TestCase):
    def test_express_month_date_range_august(self) -> None:
        start, end = express_month_date_range("15/08/69")
        self.assertEqual(start, "01/08/69")
        self.assertEqual(end, "31/08/69")

    def test_year_start_date_from_ui_month(self) -> None:
        self.assertEqual(express_year_start_date("15/07/69"), "01/01/69")
        self.assertEqual(express_year_start_date("01/04/70"), "01/01/70")

    def test_ledger_range_report_uses_2137_and_ui_month(self) -> None:
        form = LedgerRangeReportForm.from_ui_date("15/07/69")
        self.assertEqual(form.from_code, "2137-00")
        self.assertEqual(form.to_code, "2137-00")
        self.assertEqual(form.start_date, "01/07/69")
        self.assertEqual(form.end_date, "31/07/69")
        with tempfile.TemporaryDirectory() as raw:
            output = form.screenshot_path(Path(raw) / "reports", "หจก.เจนสิริการค้า")
            self.assertEqual(output.name, "2137-00.png")

    def test_express_month_date_range_april(self) -> None:
        start, end = express_month_date_range("01/04/69")
        self.assertEqual(start, "01/04/69")
        self.assertEqual(end, "30/04/69")

    def test_express_month_date_range_leap_february(self) -> None:
        start, end = express_month_date_range("10/02/67")
        self.assertEqual(start, "01/02/67")
        self.assertEqual(end, "29/02/67")

    def test_express_month_date_range_july_plus_one_is_end_of_august(self) -> None:
        start, end = express_month_date_range("15/7/69", end_month_offset=1)
        self.assertEqual(start, "01/07/69")
        self.assertEqual(end, "31/08/69")

    def test_express_month_date_range_december_plus_one_wraps_year(self) -> None:
        start, end = express_month_date_range("15/12/69", end_month_offset=1)
        self.assertEqual(start, "01/12/69")
        self.assertEqual(end, "31/01/70")

    def test_format_express_pv_date_zero_pads(self) -> None:
        from constants.date_utils import format_express_pv_date

        self.assertEqual(format_express_pv_date("15/7/69"), "15/07/69")
        self.assertEqual(format_express_pv_date("31/8/69"), "31/08/69")
        self.assertEqual(express_month_folder_name("15/08/69"), "08-69")

    def test_safe_folder_name_strips_invalid_chars(self) -> None:
        self.assertEqual(safe_folder_name("บริษัท / ทดสอบ:*"), "บริษัท  ทดสอบ")

    def test_build_account_report_jobs_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp_path = Path(raw)
            row = KaTamRow(
                row_number=2,
                sequence=1,
                sheet_name="srv 2026 07",
                legal_name="บริษัท ตัวอย่าง จำกัด",
                month="08",
                tax_id="",
                service_amount=1,
                vat_amount=1,
                credit_amount=0,
                wt_amount=1,
            )
            config = RunConfig(
                topic="payment_journal",
                excel_path=tmp_path / "dummy.xlsx",
                pv_date="15/08/69",
                report_output_dir=tmp_path / "reports",
            )
            jobs = build_account_report_jobs(config, row)
            self.assertEqual(
                tuple(job.account_code for job in jobs),
                (ACCOUNT_SERVICE, ACCOUNT_VAT, ACCOUNT_WT),
            )
            self.assertEqual(jobs[2].account_code, "2132-02")
            layout = ReportOutputLayout(
                base_dir=config.report_output_dir,
                legal_name=row.legal_name,
            )
            self.assertEqual(jobs[0].output_file, layout.screenshot_path(ACCOUNT_SERVICE))
            self.assertEqual(jobs[0].output_file.name, f"{ACCOUNT_SERVICE}.png")
            self.assertEqual(jobs[0].start_date, "01/08/69")
            self.assertEqual(jobs[0].end_date, "31/08/69")
            expected = tmp_path / "reports" / "บริษัท ตัวอย่าง จำกัด" / "5330-05.png"
            self.assertEqual(jobs[0].output_file, expected)

    def test_build_pp30_ledger_report_jobs_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp_path = Path(raw)
            jobs = build_ledger_report_jobs(
                report_output_dir=tmp_path / "reports",
                legal_name="หจก.เจนสิริการค้า",
                month_date="15/07/69",
                account_codes=PP30_ACCOUNT_REPORT_CODES,
                end_month_offset=0,
            )
            self.assertEqual(tuple(job.account_code for job in jobs), PP30_ACCOUNT_REPORT_CODES)
            self.assertEqual(jobs[0].start_date, "01/07/69")
            self.assertEqual(jobs[0].end_date, "31/07/69")
            expected = tmp_path / "reports" / "หจก.เจนสิริการค้า" / "1154-00.png"
            self.assertEqual(jobs[0].output_file, expected)

    def test_build_new_shop_ledger_report_jobs_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp_path = Path(raw)
            jobs = build_ledger_report_jobs(
                report_output_dir=tmp_path / "reports",
                legal_name="หจก.เจนสิริการค้า",
                month_date="10/10/69",
                account_codes=PP30_NEW_SHOP_REPORT_CODES,
                end_month_offset=0,
            )
            self.assertEqual(tuple(job.account_code for job in jobs), ("1154-00", ACCOUNT_PP30_NEW_SHOP))
            self.assertEqual(jobs[0].start_date, "01/10/69")
            self.assertEqual(jobs[0].end_date, "31/10/69")
            self.assertEqual(
                jobs[0].output_file,
                tmp_path / "reports" / "หจก.เจนสิริการค้า" / "1154-00.png",
            )
            self.assertEqual(
                jobs[1].output_file,
                tmp_path / "reports" / "หจก.เจนสิริการค้า" / "1156-00.png",
            )

    def test_build_no_pay_normal_ledger_report_jobs_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp_path = Path(raw)
            jobs = build_ledger_report_jobs(
                report_output_dir=tmp_path / "reports",
                legal_name="หจก.เจนสิริการค้า",
                month_date="10/10/69",
                account_codes=PP30_NO_PAY_NORMAL_REPORT_CODES,
                end_month_offset=0,
            )
            self.assertEqual(
                tuple(job.account_code for job in jobs),
                ("2135-00", "1154-00", ACCOUNT_PP30_NEW_SHOP),
            )
            self.assertEqual(jobs[0].start_date, "01/10/69")
            self.assertEqual(jobs[0].end_date, "31/10/69")
            self.assertEqual(
                jobs[2].output_file,
                tmp_path / "reports" / "หจก.เจนสิริการค้า" / "1156-00.png",
            )

    def test_build_pay_ledger_report_jobs_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp_path = Path(raw)
            jobs = build_ledger_report_jobs(
                report_output_dir=tmp_path / "reports",
                legal_name="หจก.เจนสิริการค้า",
                month_date="10/10/69",
                account_codes=PP30_PAY_REPORT_CODES,
                end_month_offset=0,
            )
            self.assertEqual(
                tuple(job.account_code for job in jobs),
                ("2135-00", "1154-00", ACCOUNT_PP30_NEW_SHOP, "2137-00"),
            )
            self.assertEqual(jobs[0].start_date, "01/10/69")
            self.assertEqual(jobs[0].end_date, "31/10/69")
            self.assertEqual(
                jobs[3].output_file,
                tmp_path / "reports" / "หจก.เจนสิริการค้า" / "2137-00.png",
            )

    def test_build_penalty_ledger_report_jobs_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp_path = Path(raw)
            jobs = build_ledger_report_jobs(
                report_output_dir=tmp_path / "reports",
                legal_name="หจก.เจนสิริการค้า",
                month_date="10/10/69",
                account_codes=PP30_PENALTY_REPORT_CODES,
                end_month_offset=0,
            )
            self.assertEqual(
                tuple(job.account_code for job in jobs),
                ("2135-00", "5390-01", "1154-00", "2137-00"),
            )
            self.assertEqual(
                jobs[1].output_file,
                tmp_path / "reports" / "หจก.เจนสิริการค้า" / "5390-01.png",
            )

    def test_expand_tree_only_on_first_job_until_opened(self) -> None:
        self.assertTrue(should_expand_ledger_report_tree(0, tree_already_open=False))
        self.assertFalse(should_expand_ledger_report_tree(1, tree_already_open=False))
        self.assertFalse(should_expand_ledger_report_tree(0, tree_already_open=True))

    def test_f12_search_region_is_left_tree_not_full_screen(self) -> None:
        x0, y0, x1, y1 = F12_MENU_REGION
        self.assertLessEqual((x1 - x0) * (y1 - y0), 880 * 700)
        self.assertLessEqual(x1, 900)
        self.assertEqual(REPORT_NORMAL_ACTION_IDS, ("menu_report_normal_selected", "menu_report_normal"))

    def test_report_reopen_retries_cap_at_two(self) -> None:
        self.assertEqual(report_reopen_retries(4), 2)
        self.assertEqual(report_reopen_retries(3), 2)
        self.assertEqual(report_reopen_retries(1), 1)

    def test_new_report_open_uses_keys_not_templates(self) -> None:
        self.assertEqual(LedgerReportOpenPlan(expand_tree=True).after_f12_keys, ("5", "4", "1"))
        self.assertEqual(LedgerReportOpenPlan(expand_tree=False).after_f12_keys, ("1",))


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from constants.date_utils import express_month_date_range, express_month_folder_name
from constants.routes import ACCOUNT_SERVICE, ACCOUNT_VAT, ACCOUNT_WT, REPORT_SCREENSHOT_FILENAME
from models.ka_tam_row import KaTamRow
from models.report_output_layout import ReportOutputLayout, safe_folder_name
from models.run_config import RunConfig
from services.account_report_capture_service import build_account_report_jobs


class AccountReportTests(unittest.TestCase):
    def test_express_month_date_range_august(self) -> None:
        start, end = express_month_date_range("15/08/69")
        self.assertEqual(start, "01/08/69")
        self.assertEqual(end, "31/08/69")

    def test_express_month_date_range_april(self) -> None:
        start, end = express_month_date_range("01/04/69")
        self.assertEqual(start, "01/04/69")
        self.assertEqual(end, "30/04/69")

    def test_express_month_date_range_leap_february(self) -> None:
        start, end = express_month_date_range("10/02/67")
        self.assertEqual(start, "01/02/67")
        self.assertEqual(end, "29/02/67")

    def test_express_month_folder_name(self) -> None:
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
                month_folder="08-69",
            )
            self.assertEqual(jobs[0].output_file, layout.screenshot_path(ACCOUNT_SERVICE))
            self.assertEqual(jobs[0].output_file.name, REPORT_SCREENSHOT_FILENAME)
            self.assertEqual(jobs[0].start_date, "01/08/69")
            self.assertEqual(jobs[0].end_date, "31/08/69")
            expected = tmp_path / "reports" / "บริษัท ตัวอย่าง จำกัด" / "08-69" / "5330-05" / "report.png"
            self.assertEqual(jobs[0].output_file, expected)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from constants.routes import ACCOUNT_CASH, ACCOUNT_SSO_CONTRIB, ACCOUNT_SSO_PENALTY, UI_TEXT
from models.month_year_period import MonthYearPeriod
from models.sso_form_config import SsoFormConfig
from models.sso_form_values import SsoFormValues
from services.sso_extract_service import extract_sso_date, extract_sso_receipt_no, extract_sso_values
from services.sso_insert_lines_service import pv_sso
from services.sso_insert_service import SsoInsertService
from services.sso_match_run_service import SsoMatchRunService
from services.sso_pdf_service import SsoPdfService

_SAMPLE = """
สำนักงานประกันสังคม ใบเสร็จรับเงิน
เลขที่ใบเสร็จรับเงิน.............................................................720069EF0016523
วันที่ออกใบเสร็จรับเงิน.......................................13/09/2569 16:28 น.
วันที่ชำระเงิน.........................................13/09/2569เวลา....................น.16:28
ผู้ชำระเงิน..........................................................................................................ห้างหุ้นส่วนจำกัด กษิดิศเกรียงไกรเงินสมทบนายจ้าง..........................................6,269.00บาท
เงินสมทบผู้ประกันตน....................................6,269.00  บาท
เงินเพิ่มตามกฏหมาย......................................0.00     บาท
เลขที่บัญชีนายจ้าง.......................................7200037338ลำดับที่สาขา...............................000000
จำนวนเงินที่ชำระ..............................................................บาท12,538.00
"""

_SAMPLE_BRANCH = """
ผู้ชำระเงิน ห้างหุ้นส่วนจำกัด กษิดิศเกรียงไกร
เงินสมทบนายจ้าง 1,000.00 บาท
เงินสมทบผู้ประกันตน 1,000.00 บาท
เงินเพิ่มตามกฏหมาย 50.00 บาท
ลำดับที่สาขา...............................000001
วันที่ชำระเงิน 13/09/2569
จำนวนเงินที่ชำระ 2,050.00 บาท
"""

SAMPLE_PDF = Path(
    "/Users/pathanin/.cursor/projects/Users-pathanin-job-AutoKey/attachments/"
    "95442e36-2dbc-40d8-8635-d8ec30cd3af5/_________________6582__03_1.pdf"
)


class SsoExtractTests(unittest.TestCase):
    def test_reads_contrib_penalty_paid_and_date(self) -> None:
        self.assertEqual(extract_sso_values(_SAMPLE), (12538.00, 0.0, 12538.00))
        self.assertEqual(extract_sso_date(_SAMPLE), "13/09/69")
        self.assertEqual(extract_sso_receipt_no(_SAMPLE), "720069EF0016523")

    def test_reads_surcharge(self) -> None:
        self.assertEqual(extract_sso_values(_SAMPLE_BRANCH), (2000.00, 50.00, 2050.00))

    def test_reads_company_and_values(self) -> None:
        name = SsoPdfService.extract_company_name(_SAMPLE)
        values = SsoPdfService.extract_form_values(_SAMPLE)
        self.assertEqual(name, "ห้างหุ้นส่วนจำกัด กษิดิศเกรียงไกร")
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.contrib_amount, 12538.00)
        self.assertFalse(values.has_surcharge)
        self.assertEqual(values.paid_amount, 12538.00)
        self.assertEqual(values.pv_date, "13/09/69")
        self.assertEqual(values.receipt_no, "720069EF0016523")

    @unittest.skipUnless(SAMPLE_PDF.exists(), "sample SSO pdf")
    def test_reads_uploaded_pdf(self) -> None:
        record = SsoPdfService.load_record(SAMPLE_PDF)
        self.assertEqual(record.company_name, "ห้างหุ้นส่วนจำกัด กษิดิศเกรียงไกร")
        self.assertIsNotNone(record.form_values)
        assert record.form_values is not None
        self.assertEqual(record.form_values.contrib_amount, 12538.00)
        self.assertFalse(record.form_values.has_surcharge)
        self.assertEqual(record.form_values.paid_amount, 12538.00)
        self.assertEqual(record.form_values.pv_date, "13/09/69")
        self.assertEqual(record.form_values.receipt_no, "720069EF0016523")


class SsoInsertLinesTests(unittest.TestCase):
    def test_contrib_then_cash(self) -> None:
        values = SsoFormValues(12538.00, 0.0, 12538.00, "13/09/69")
        voucher = pv_sso(values, "13/09/69", "สำนักงานประกันสังคม เดือน 8/69")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_SSO_CONTRIB, 12538.00, False),
                (ACCOUNT_CASH, 12538.00, True),
            ],
        )

    def test_surcharge_before_cash(self) -> None:
        values = SsoFormValues(2000.00, 50.0, 2050.00, "13/09/69")
        voucher = pv_sso(values, "13/09/69", "สำนักงานประกันสังคม เดือน 8/69 *1")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_SSO_CONTRIB, 2000.00, False),
                (ACCOUNT_SSO_PENALTY, 50.0, False),
                (ACCOUNT_CASH, 2050.00, True),
            ],
        )

    def test_form_description_and_duplicate_suffix(self) -> None:
        form = SsoFormConfig(pdf_folder=Path("."), period=MonthYearPeriod.parse("08/69"))
        self.assertEqual(form.description, "สำนักงานประกันสังคม เดือน 8/69")
        self.assertEqual(form.description_for(1), "สำนักงานประกันสังคม เดือน 8/69 *1")
        self.assertEqual(SsoMatchRunService.dup_star(1, 1), None)
        self.assertEqual(SsoMatchRunService.dup_star(2, 1), 1)
        self.assertEqual(SsoMatchRunService.dup_star(2, 2), 2)
        self.assertEqual(
            SsoMatchRunService.receipt_key(Path("/shop-a"), "720069EF0016523"),
            SsoMatchRunService.receipt_key(Path("/shop-a"), "720069ef0016523"),
        )
        self.assertNotEqual(
            SsoMatchRunService.receipt_key(Path("/shop-a"), "720069EF0016523"),
            SsoMatchRunService.receipt_key(Path("/shop-b"), "720069EF0016523"),
        )
        self.assertEqual(SsoMatchRunService.receipt_key(Path("/shop-a"), ""), "")
        voucher = SsoInsertService.voucher(
            SsoFormValues(12538.00, 0.0, 12538.00, "13/09/69"), form, dup_n=1
        )
        self.assertEqual(voucher.description, "สำนักงานประกันสังคม เดือน 8/69 *1")

    def test_form_needs_pdf_folder(self) -> None:
        errors = SsoFormConfig(pdf_folder=Path("/no-folder"), period=MonthYearPeriod.parse("08/69")).validate()
        self.assertTrue(any("โฟลเดอร์" in item for item in errors))
        self.assertNotIn(UI_TEXT["sso_period_invalid"], errors)

    def test_form_needs_period(self) -> None:
        errors = SsoFormConfig(pdf_folder=Path("/no-folder"), period=MonthYearPeriod.parse("")).validate()
        self.assertIn(UI_TEXT["sso_period_invalid"], errors)


if __name__ == "__main__":
    unittest.main()

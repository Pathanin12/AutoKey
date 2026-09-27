import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from openpyxl import Workbook

from api.income_sbp_api import pick_report_types
from constants.date_utils import express_date_to_iso
from constants.routes import INCOME_WANTED_REPORT_CODES
from models.income_form_config import IncomeFormConfig
from models.income_report_type import IncomeReportType
from services.income_excel_service import IncomeExcelService


def _type(code: str, name: str = "") -> IncomeReportType:
    return IncomeReportType(code=code, name=name)


class IncomeExcelTests(unittest.TestCase):
    def test_reads_legal_user_pass(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vat.xlsx"
            book = Workbook()
            sheet = book.active
            sheet.title = "vat - tax 2026 05"
            sheet.append([None, None, "SBP"])
            sheet.append(["NO.", "นิติบุคคล", "user", "pass"])
            sheet.append([1, "หจก. ทดสอบ", "shop@7sbp.store", "secret"])
            book.save(path)
            accounts = IncomeExcelService.load_accounts(path)
            self.assertEqual(len(accounts), 1)
            self.assertEqual(accounts[0].legal_name, "หจก. ทดสอบ")
            self.assertEqual(accounts[0].username, "shop@7sbp.store")
            self.assertEqual(accounts[0].password, "secret")


class IncomeReportTypeTests(unittest.TestCase):
    def test_takes_ticked_types_that_shop_has(self) -> None:
        available = [
            _type("STMTRPT1", "Statement Form 1"),
            _type("STMTRPT2", "Statement Form 2"),
            _type("SAP001ARREC", "ใบเสร็จรับเงิน (ออกให้)"),
            _type("SAP002APREC", "ใบเสร็จรับเงิน (ออกแทน)"),
            _type("SAP002APRECTAX", "ใบเสร็จรับเงิน/ใบกำกับภาษี (ออกแทน)"),
            _type("SAP003WHTAP", "เอกสาร หัก ณ ที่จ่าย (ออกให้)"),
            _type("RT040072", "ใบแจ้งยอดภาษีมูลค่าเพิ่ม"),
            _type("PRESTMT", "Pre-statement Daily"),
        ]
        self.assertEqual(
            pick_report_types(available),
            [
                "STMTRPT1",
                "STMTRPT2",
                "SAP001ARREC",
                "SAP002APREC",
                "SAP002APRECTAX",
                "SAP003WHTAP",
            ],
        )

    def test_skips_missing_and_takes_stamp_if_present(self) -> None:
        available = [
            _type("STMTRPT1", "Statement Form 1"),
            _type("RT040079", "รายงานอากรแสตมป์"),
            _type("CRC1203", "รายงาน รายได้ Commission"),
        ]
        self.assertEqual(pick_report_types(available), ["STMTRPT1", "RT040079"])

    def test_takes_unknown_code_when_name_is_ticked(self) -> None:
        available = [
            _type("SAP00X", "ใบเสร็จรับเงิน/ใบกำกับภาษี (ออกให้)"),
            _type("SAP00Y", "เอกสาร หัก ณ ที่จ่าย (ออกแทน)"),
        ]
        self.assertEqual(pick_report_types(available), ["SAP00X", "SAP00Y"])
        self.assertIn("STMTRPT1", INCOME_WANTED_REPORT_CODES)


class IncomeFormDownloadTests(unittest.TestCase):
    def test_form_needs_excel_and_dates(self) -> None:
        errors = IncomeFormConfig(pdf_folder=Path("/no-folder"), rv_description="x").validate()
        self.assertTrue(any("Excel" in item for item in errors))
        self.assertTrue(any("วันที่" in item for item in errors))
        self.assertTrue(any("โฟลเดอร์" in item for item in errors))

    def test_iso_date_from_express(self) -> None:
        self.assertEqual(express_date_to_iso("01/08/69"), "2026-08-01")
        self.assertEqual(express_date_to_iso("31/08/69"), "2026-08-31")


if __name__ == "__main__":
    unittest.main()

import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from constants.date_utils import calendar_date, same_calendar_date
from models.journal_voucher import JournalLine, JournalVoucher
from services.dbf_table_service import DbfTableService
from services.express_journal_date_service import ExpressJournalDateService

SAMPLE_GLJNL = Path("/Users/pathanin/Downloads/kachapor/GLJNL.DBF")


class CalendarDateTests(unittest.TestCase):
    def test_same_day_month_year(self) -> None:
        self.assertEqual(calendar_date("31/08/69"), (31, 8, 2026))
        self.assertEqual(calendar_date("20260831"), (31, 8, 2026))
        self.assertTrue(same_calendar_date("31/08/69", "20260831"))

    def test_same_day_different_month_or_year_is_not_same(self) -> None:
        self.assertFalse(same_calendar_date("31/08/69", "20260731"))
        self.assertFalse(same_calendar_date("31/08/69", "20250831"))
        self.assertFalse(same_calendar_date("10/08/69", "20260831"))


class ExpressJournalDateTests(unittest.TestCase):
    def test_missing_folder_is_not_duplicate(self) -> None:
        self.assertFalse(ExpressJournalDateService.has_express_date(Path("/tmp/no-shop"), "14/09/69"))

    @unittest.skipUnless(SAMPLE_GLJNL.exists(), "sample GLJNL.DBF")
    def test_existing_voudat_matches_full_date(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            dest = folder / "GLJNL.DBF"
            shutil.copy2(SAMPLE_GLJNL, dest)
            DbfTableService.append(dest, {"VOUDAT": "20260101", "VOUCHER": "JV69010099"})
            self.assertTrue(ExpressJournalDateService.has_express_date(folder, "01/01/69"))
            self.assertFalse(ExpressJournalDateService.has_express_date(folder, "01/01/68"))
            self.assertFalse(ExpressJournalDateService.has_express_date(folder, "01/02/69"))
            jv = JournalVoucher(
                jnltyp="00",
                prefix="JV",
                voudat_express="01/01/69",
                description="jv",
                lines=[JournalLine(account="2135-00", amount=1.0, is_credit=False)],
            )
            self.assertEqual(ExpressJournalDateService.first_existing_voucher_date(folder, [jv]), "01/01/69")

    @unittest.skipUnless(SAMPLE_GLJNL.exists(), "sample GLJNL.DBF")
    def test_fa_same_date_is_not_duplicate(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            dest = folder / "GLJNL.DBF"
            shutil.copy2(SAMPLE_GLJNL, dest)
            DbfTableService.append(dest, {"VOUDAT": "20070202", "VOUCHER": "FA50020001"})
            self.assertFalse(ExpressJournalDateService.has_express_date(folder, "02/02/50"))
            jv = JournalVoucher(
                jnltyp="00",
                prefix="JV",
                voudat_express="02/02/50",
                description="jv",
                lines=[JournalLine(account="2135-00", amount=1.0, is_credit=False)],
            )
            self.assertIsNone(ExpressJournalDateService.first_existing_voucher_date(folder, [jv]))
            DbfTableService.append(dest, {"VOUDAT": "20070202", "VOUCHER": "JV50020099"})
            self.assertTrue(ExpressJournalDateService.has_express_date(folder, "02/02/50", "JV"))
            self.assertEqual(ExpressJournalDateService.first_existing_voucher_date(folder, [jv]), "02/02/50")


if __name__ == "__main__":
    unittest.main()

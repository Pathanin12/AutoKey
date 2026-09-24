import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from models.journal_voucher import JournalLine, JournalVoucher
from services.dbf_table_service import DbfTableService
from services.express_journal_date_service import ExpressJournalDateService

SAMPLE_GLJNL = Path("/Users/pathanin/Downloads/kachapor/GLJNL.DBF")


class ExpressJournalDateTests(unittest.TestCase):
    def test_missing_folder_is_not_duplicate(self) -> None:
        self.assertFalse(ExpressJournalDateService.has_express_date(Path("/tmp/no-shop"), "14/09/69"))

    def test_incomplete_date_is_not_duplicate(self) -> None:
        self.assertFalse(ExpressJournalDateService.has_express_date(Path("/tmp"), "14/09"))

    @unittest.skipUnless(SAMPLE_GLJNL.exists(), "sample GLJNL.DBF")
    def test_existing_voudat_matches_pdf_date(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            shutil.copy2(SAMPLE_GLJNL, folder / "GLJNL.DBF")
            self.assertTrue(ExpressJournalDateService.has_express_date(folder, "14/09/69"))
            self.assertFalse(ExpressJournalDateService.has_express_date(folder, "01/01/60"))

    @unittest.skipUnless(SAMPLE_GLJNL.exists(), "sample GLJNL.DBF")
    def test_appended_voudat_is_found(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            dest = folder / "GLJNL.DBF"
            shutil.copy2(SAMPLE_GLJNL, dest)
            DbfTableService.append(dest, {"VOUDAT": "20260101", "VOUCHER": "JV69010099"})
            self.assertTrue(ExpressJournalDateService.has_express_date(folder, "01/01/69"))
            jv = JournalVoucher(
                jnltyp="00",
                prefix="JV",
                voudat_express="01/01/69",
                description="jv",
                lines=[JournalLine(account="2135-00", amount=1.0, is_credit=False)],
            )
            pv = JournalVoucher(
                jnltyp="01",
                prefix="PV",
                voudat_express="15/07/60",
                description="pv",
                lines=[JournalLine(account="1111-00", amount=1.0, is_credit=True)],
            )
            self.assertEqual(ExpressJournalDateService.first_existing_voucher_date(folder, [jv, pv]), "01/01/69")
            self.assertEqual(ExpressJournalDateService.first_existing_voucher_date(folder, [pv, jv]), "01/01/69")
            self.assertIsNone(ExpressJournalDateService.first_existing_voucher_date(folder, [pv]))


if __name__ == "__main__":
    unittest.main()

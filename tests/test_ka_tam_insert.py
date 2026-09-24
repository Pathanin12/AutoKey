import shutil
import unittest
from pathlib import Path
from struct import unpack
from tempfile import TemporaryDirectory

from constants.date_utils import is_complete_express_date
from constants.routes import ACCOUNT_CASH, ACCOUNT_SERVICE, ACCOUNT_VAT, ACCOUNT_WT
from models.ka_tam_form_config import KaTamFormConfig
from models.ka_tam_row import KaTamRow
from services.dbf_table_service import DbfTableService
from services.ka_tam_excel_service import KaTamExcelService
from services.ka_tam_insert_lines_service import pv_ka_tam
from services.ka_tam_insert_service import KaTamInsertService

SAMPLE_SHOP = Path("/Users/pathanin/Downloads/kachapor 3")
SAMPLE_EXCEL = Path("/Users/pathanin/Downloads/srv 2026 08 acct.8 - Copyค่าทำจ้า.xlsx")


def _row(**kwargs) -> KaTamRow:
    data = dict(
        row_number=2,
        sequence=1,
        sheet_name="sheet",
        legal_name="ห้างทดสอบ",
        service_amount=1200.0,
        vat_amount=84.0,
        wt_amount=36.0,
        invoice_number="NRG2026080001",
        tax_id="0115569014941",
    )
    data.update(kwargs)
    return KaTamRow(**data)


class KaTamInsertLinesTests(unittest.TestCase):
    def test_pv_lines_match_keyed_sample(self) -> None:
        voucher = pv_ka_tam(_row(), "25/07/69", "ค่าทำบัญชี 7/69")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_SERVICE, 1200.0, False),
                (ACCOUNT_VAT, 84.0, False),
                (ACCOUNT_WT, 36.0, True),
                (ACCOUNT_CASH, 1248.0, True),
            ],
        )

    def test_skip_zero_vat_and_wt(self) -> None:
        voucher = pv_ka_tam(_row(vat_amount=0, wt_amount=0), "25/07/69", "jv")
        self.assertEqual(
            [(line.account, line.amount, line.is_credit) for line in voucher.lines],
            [
                (ACCOUNT_SERVICE, 1200.0, False),
                (ACCOUNT_CASH, 1200.0, True),
            ],
        )

    def test_no_service_is_empty(self) -> None:
        voucher = pv_ka_tam(_row(service_amount=0, vat_amount=0, wt_amount=0), "25/07/69", "jv")
        self.assertEqual(voucher.lines, [])

    def test_invoice_follows_row_sequence(self) -> None:
        form = KaTamFormConfig(
            excel_path=Path("."),
            pv_date="25/07/69",
            description="ค่าทำ",
            tax_payer_id="0115569014941",
        )
        self.assertEqual(KaTamInsertService.invoice_number(_row()), "NRG2026080001")
        self.assertEqual(KaTamInsertService.invoice_number(_row(invoice_number="NRG2026080002")), "NRG2026080002")
        self.assertEqual(KaTamInsertService.tax_payer_id(form), "0115569014941")
        form.tax_payer_id = ""
        self.assertEqual(KaTamInsertService.tax_payer_id(form), "")
        self.assertNotEqual(KaTamInsertService.tax_payer_id(form), _row().tax_id)

    def test_form_date_must_be_complete(self) -> None:
        self.assertFalse(is_complete_express_date(""))
        errors = KaTamFormConfig(excel_path=Path("/no.xlsx"), pv_date="25/07", description="x").validate()
        self.assertTrue(any("วันที่" in item for item in errors))


class KaTamExcelInvoiceTests(unittest.TestCase):
    @unittest.skipUnless(SAMPLE_EXCEL.exists(), "sample excel")
    def test_invoice_is_nrg_year_month_sequence(self) -> None:
        rows = KaTamExcelService.load_rows(SAMPLE_EXCEL)
        self.assertEqual([row.sequence for row in rows], [1, 2])
        self.assertEqual([row.invoice_number for row in rows], ["NRG2026080001", "NRG2026080002"])


class KaTamLiveInsertTests(unittest.TestCase):
    @unittest.skipUnless(SAMPLE_SHOP.exists(), "sample shop folder")
    def test_insert_writes_pv_and_isvat(self) -> None:
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "shop"
            shutil.copytree(SAMPLE_SHOP, dest)
            form = KaTamFormConfig(
                excel_path=Path("."),
                pv_date="25/07/69",
                description="บจก.เอ็นอาร์จี แอคเคาท์-ค่าทำบัญชี 7/69",
                tax_payer_id="0115569014941",
            )
            name = KaTamInsertService.insert(dest, _row(tax_id="0123562000773"), form)
            self.assertTrue(name.startswith("PV6907"))
            headers = DbfTableService.read_records(dest / "GLJNL.DBF")
            self.assertEqual(headers[-1]["VOUCHER"], name)
            self.assertEqual(headers[-1]["JNLTYP"], "01")
            items = [row for row in DbfTableService.read_records(dest / "GLJNLIT.DBF") if row["VOUCHER"] == name]
            self.assertEqual([row["ACCNUM"] for row in items], ["5330-05", "1154-00", "2132-02", "1111-00"])
            vat_path = dest / "ISVAT.DBF"
            table = DbfTableService.load(vat_path)
            rec = table.records_blob[(table.nrecords - 1) * table.rec_len : table.nrecords * table.rec_len]
            values = DbfTableService._unpack(table, rec)
            self.assertEqual(values["VATREC"].strip(), "P")
            self.assertEqual(values["DOCNUM"].strip(), name)
            self.assertEqual(values["REFNUM"].strip(), "NRG2026080001")
            self.assertEqual(values["TAXID"].strip(), "0115569014941")
            self.assertEqual(values["VATPRD"].strip(), "20260701")
            amt_off = 1
            for field in table.fields:
                if field.name == "AMT01":
                    raw = rec[amt_off : amt_off + field.length]
                    self.assertEqual(unpack("<d", raw)[0], 1200.0)
                    break
                amt_off += field.length


if __name__ == "__main__":
    unittest.main()

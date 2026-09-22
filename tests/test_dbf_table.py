import shutil
import unittest
from pathlib import Path
from struct import unpack
from tempfile import TemporaryDirectory

from services.dbf_table_service import DbfTableService

SAMPLE_GLJNL = Path("/Users/pathanin/Downloads/kachapor/GLJNL.DBF")


class DbfTableTests(unittest.TestCase):
    @unittest.skipUnless(SAMPLE_GLJNL.exists(), "sample GLJNL.DBF")
    def test_append_does_not_add_eof_byte(self) -> None:
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "GLJNL.DBF"
            shutil.copy2(SAMPLE_GLJNL, dest)
            recno = DbfTableService.append(
                dest,
                {
                    "JNLTYP": "00",
                    "VOUCHER": "JV69089999",
                    "VOUDAT": "20260831",
                    "SRCJNL": "GL",
                    "TRNSTAT": "P",
                    "DOCSTAT": "N",
                },
            )
            data = dest.read_bytes()
            nrecords = unpack("<I", data[4:8])[0]
            header_len = unpack("<H", data[8:10])[0]
            rec_len = unpack("<H", data[10:12])[0]
            self.assertEqual(recno, nrecords)
            self.assertEqual(len(data), header_len + nrecords * rec_len)


if __name__ == "__main__":
    unittest.main()

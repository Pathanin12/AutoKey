import shutil
import unittest
from pathlib import Path
from struct import pack, unpack
from tempfile import TemporaryDirectory

from services.cdx_index_service import (
    CDX_PAGE,
    CdxIndexService,
    _bump_file_version,
    _decode_leaf,
)

SAMPLE_GLJNL_CDX = Path("/Users/pathanin/Downloads/kachapor/GLJNL.CDX")


def _bag_names(data: bytes) -> list[str]:
    root = unpack("<I", data[0:4])[0]
    key_size = unpack("<H", data[12:14])[0]
    page = data[root : root + CDX_PAGE]
    nkeys = unpack("<H", page[2:4])[0]
    rec_mask = unpack("<I", page[14:18])[0]
    decoded = _decode_leaf(
        page, key_size, nkeys, page[23], rec_mask, page[21], page[22], page[18], page[19]
    )
    return [key.decode("ascii", "replace").strip() for key, _recno, _dup, _trl in decoded]


class CdxIndexTests(unittest.TestCase):
    def test_bump_file_version_keeps_key_length(self) -> None:
        data = bytearray(16)
        data[8:12] = pack(">I", 0x8F)
        data[12:14] = pack("<H", 10)
        _bump_file_version(data)
        self.assertEqual(unpack(">I", data[8:12])[0], 0x90)
        self.assertEqual(unpack("<H", data[12:14])[0], 10)

    @unittest.skipUnless(SAMPLE_GLJNL_CDX.exists(), "sample GLJNL.CDX")
    def test_insert_keeps_gljnl3_tag_name(self) -> None:
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "GLJNL.CDX"
            shutil.copy2(SAMPLE_GLJNL_CDX, dest)
            before = dest.read_bytes()
            CdxIndexService.insert_key(
                dest,
                {
                    "JNLTYP": "00",
                    "VOUDAT": "20260831",
                    "VOUCHER": "JV69080099",
                    "TRNSTAT": "P",
                    "CHGDAT": "20260922",
                },
                999,
            )
            after = dest.read_bytes()
            self.assertEqual(unpack("<H", after[12:14])[0], 10)
            self.assertEqual(unpack(">I", after[8:12])[0], unpack(">I", before[8:12])[0] + 1)
            self.assertIn("GLJNL3", _bag_names(after))
            self.assertEqual(after[1024 + 8 : 1024 + 12], before[1024 + 8 : 1024 + 12])


if __name__ == "__main__":
    unittest.main()

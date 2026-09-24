import shutil
import unittest
from pathlib import Path
from struct import pack, unpack
from tempfile import TemporaryDirectory

from services.cdx_index_service import (
    CDX_INT_HEAD,
    CDX_NODE_LEAF,
    CDX_PAGE,
    CdxIndexService,
    _bump_file_version,
    _decode_leaf,
    _tags,
)

SAMPLE_GLJNL_CDX = Path("/Users/pathanin/Downloads/kachapor/GLJNL.CDX")
SAMPLE_GLJNLIT_CDX = Path("/Users/pathanin/Downloads/onestop 2/GLJNLIT.CDX")


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


def _interior_last(data: bytes, tag_index: int) -> tuple[bytes, int]:
    tag = _tags(data)[tag_index]
    page = data[tag.root : tag.root + CDX_PAGE]
    attr = unpack("<H", page[0:2])[0]
    if attr & CDX_NODE_LEAF:
        raise AssertionError("tag root is a leaf")
    nkeys = unpack("<H", page[2:4])[0]
    slot = tag.key_size + 8
    base = CDX_INT_HEAD + (nkeys - 1) * slot
    key = bytes(page[base : base + tag.key_size])
    recno = unpack(">I", page[base + tag.key_size : base + tag.key_size + 4])[0]
    return key, recno


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

    @unittest.skipUnless(SAMPLE_GLJNL_CDX.exists(), "sample GLJNL.CDX")
    def test_insert_updates_gljnl6_parent_last_key(self) -> None:
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "GLJNL.CDX"
            shutil.copy2(SAMPLE_GLJNL_CDX, dest)
            before_key, before_rec = _interior_last(dest.read_bytes(), 5)
            self.assertEqual(before_key.rstrip(), b"20260921PV69090001")
            self.assertEqual(before_rec, 111)
            CdxIndexService.insert_key(
                dest,
                {
                    "JNLTYP": "00",
                    "VOUDAT": "20260831",
                    "VOUCHER": "JV69080001",
                    "TRNSTAT": "P",
                    "CHGDAT": "20260922",
                },
                114,
            )
            CdxIndexService.insert_key(
                dest,
                {
                    "JNLTYP": "01",
                    "VOUDAT": "20260921",
                    "VOUCHER": "PV69090002",
                    "TRNSTAT": "P",
                    "CHGDAT": "20260922",
                },
                115,
            )
            after_key, after_rec = _interior_last(dest.read_bytes(), 5)
            self.assertEqual(after_key.rstrip(), b"20260922PV69090002")
            self.assertEqual(after_rec, 115)

    @unittest.skipUnless(SAMPLE_GLJNLIT_CDX.exists(), "sample GLJNLIT.CDX")
    def test_insert_splits_full_accnum_leaf(self) -> None:
        with TemporaryDirectory() as tmp:
            dest = Path(tmp) / "GLJNLIT.CDX"
            shutil.copy2(SAMPLE_GLJNLIT_CDX, dest)
            before = dest.read_bytes()
            tag = _tags(before)[3]
            self.assertTrue(before[tag.root] & CDX_NODE_LEAF)
            before_keys = _walk_tag_keys(before, tag)
            CdxIndexService.insert_key(
                dest,
                {
                    "VOUCHER": "JV69080002",
                    "SEQIT": " 1",
                    "VOUDAT": "20260831",
                    "ACCNUM": "2135-00",
                    "TRNTYP": "0",
                    "DEPCOD": "",
                    "CHGDAT": "20260924",
                },
                200,
            )
            after = dest.read_bytes()
            tag = _tags(after)[3]
            self.assertFalse(after[tag.root] & CDX_NODE_LEAF)
            keys = _walk_tag_keys(after, tag)
            self.assertEqual(len(keys), len(before_keys) + 1)
            self.assertIn((b"2135-00        ", 200), keys)


def _walk_tag_keys(data: bytes, tag) -> list[tuple[bytes, int]]:
    keys: list[tuple[bytes, int]] = []

    def walk(page_off: int) -> None:
        page = data[page_off : page_off + CDX_PAGE]
        attr = unpack("<H", page[0:2])[0]
        nkeys = unpack("<H", page[2:4])[0]
        if attr & CDX_NODE_LEAF:
            rec_mask = unpack("<I", page[14:18])[0]
            decoded = _decode_leaf(
                page, tag.key_size, nkeys, page[23], rec_mask, page[21], page[22], page[18], page[19]
            )
            keys.extend((item[0], item[1]) for item in decoded)
            return
        slot = tag.key_size + 8
        for index in range(nkeys):
            base = CDX_INT_HEAD + index * slot
            child = unpack(">I", page[base + tag.key_size + 4 : base + tag.key_size + 8])[0]
            walk(child)

    walk(tag.root)
    return keys


if __name__ == "__main__":
    unittest.main()

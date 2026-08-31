import unittest

from topics.ka_tam.sheet_configs import detect_column_map


class DetectColumnMapTests(unittest.TestCase):
    def test_august_headers_use_special_legal_name(self) -> None:
        preview = [
            (None,) * 11,
            (
                "NO.",
                "no",
                "เลขที่ใบกำกับ",
                "นิติบุคคล",
                "นิติบุคคล (special)",
                "เดือน",
                "TAX ID",
                "ค่าบริการ",
                "srv",
                "vat",
                "wt",
            ),
            (1, 1, "NRG2026080001", "บจก. เอ", "เอ", "07.69", "1", 2140, 2000, 140, 60),
        ]
        column_map = detect_column_map(preview)
        self.assertEqual(column_map.header_row, 1)
        self.assertEqual(column_map.data_start_row, 2)
        self.assertEqual(column_map.legal_name, 4)
        self.assertEqual(column_map.invoice_number, 2)
        self.assertEqual(column_map.month, 5)
        self.assertEqual(column_map.tax_id, 6)
        self.assertEqual(column_map.service_amount, 8)
        self.assertEqual(column_map.vat_amount, 9)
        self.assertEqual(column_map.wt_amount, 10)

    def test_july_headers_use_legal_name_column(self) -> None:
        preview = [
            (None,) * 9,
            ("NO.", "เลขที่ใบกำกับ", "นิติบุคคล", "เดือน", "TAX ID", "ค่าบริการ", "srv", "vat", "wt"),
            (1, "NRG2026070001", "บริษัท เอ", "07.69", "1", 2140, 2000, 140, 60),
        ]
        column_map = detect_column_map(preview)
        self.assertEqual(column_map.legal_name, 2)
        self.assertEqual(column_map.invoice_number, 1)
        self.assertEqual(column_map.service_amount, 6)


if __name__ == "__main__":
    unittest.main()

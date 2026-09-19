from __future__ import annotations

import unittest
from pathlib import Path

from models.pnd30_form_config import Pnd30FormConfig
from models.pnd30_form_values import Pnd30FormValues
from models.pnd30_matched_job import Pnd30PdfRecord
from services.pnd30_extract_service import extract_line_2_and_3, extract_pv_date
from services.pnd30_fill_service import fill_pv
from services.pnd30_match_service import Pnd30MatchService
from services.pnd30_pdf_service import Pnd30PdfService


_SAMPLE_SURCHARGE = """
4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (2. + 3.) . . . . . . . 1,036.25
3. เงินเพิ่ม (ถ้ามี). . . . . . . . . . . . . . . 15.31
1,020.94	2. . . . . . . . . . . . .	รวมยอดภาษีที่นำส่งทั้งสิ้
1. . . . . . . . . . . . . . 34,031.25	รวมยอดเงินได้ทั้งสิ้น
ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน) : สาขาที่ 0	0	0	0	0
ห้างหุ้นส่วนจำกัด ธนทรัพย์เจริญ 99	................................................................
ยื่นวันที่ 16 เดือน มิถุนายน พ.ศ. 2569
วันที่: 16/06/2569
"""

_SAMPLE_NO_SURCHARGE = """
4. รวมยอดภาษีที่นำส่งทั้งสิ้น และเงินเพิ่ม (2. + 3.) . . . . . . . 36.00
3. เงินเพิ่ม (ถ้ามี). . . . . . . . . . . . . . .
36.00	2. . . . . . . . . . . .	รวมยอดภาษีที่นำส่งทั้งสิ้
1. . . . . . . . . . . . . . 1,200.00	รวมยอดเงินได้ทั้งสิ้น
ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน) : สาขาที่ 0	0	0	0	0
ห้างหุ้นส่วนจำกัด 2411	................................................................
วันที่: 13/07/2569
ยื่นวันที่ 08 เดือน กรกฎาคม พ.ศ. 2569
"""


class RecordingImage:
    def __init__(self) -> None:
        self.events: list[tuple] = []

    def press(self, *keys: str, presses: int = 1) -> None:
        for _ in range(presses):
            self.events.append(("press", keys))

    def type_text(self, text: str, clear_first: bool = True) -> None:
        self.events.append(("type_text", text, clear_first))

    def type_thai(self, text: str, clear_first: bool = True) -> None:
        self.events.append(("type_thai", text, clear_first))

    def type_keys(self, text: str, *, clear_first: bool = False) -> None:
        self.events.append(("type_keys", text, clear_first))

    def wait(self, _seconds: float) -> None:
        return None


def _config() -> Pnd30FormConfig:
    return Pnd30FormConfig(
        pdf_folder=Path("/tmp"),
        excel_path=Path("/tmp/a.xlsx"),
        pv_date="01/01/69",
        pv_description="รายละเอียด PV",
        report_output_dir=Path("/tmp/out"),
    )


def _typed_and_pressed(events: list[tuple]) -> list[tuple]:
    return [event for event in events if event[0] in {"type_text", "press", "type_keys", "type_thai"}]


class Pnd30ExtractTests(unittest.TestCase):
    def test_reads_line_2_and_surcharge_line_3(self) -> None:
        lines = extract_line_2_and_3(_SAMPLE_SURCHARGE)
        self.assertEqual(lines, (1020.94, 15.31))
        self.assertEqual(extract_pv_date(_SAMPLE_SURCHARGE), "16/06/69")

    def test_empty_line_3_is_zero(self) -> None:
        lines = extract_line_2_and_3(_SAMPLE_NO_SURCHARGE)
        self.assertEqual(lines, (36.00, 0.0))
        self.assertEqual(extract_pv_date(_SAMPLE_NO_SURCHARGE), "08/07/69")

    def test_reads_company_and_values_from_form_text(self) -> None:
        name = Pnd30PdfService.extract_company_name(_SAMPLE_SURCHARGE)
        values = Pnd30PdfService.extract_form_values(_SAMPLE_SURCHARGE)
        self.assertEqual(name, "ห้างหุ้นส่วนจำกัด ธนทรัพย์เจริญ 99")
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.tax_withheld, 1020.94)
        self.assertEqual(values.surcharge, 15.31)
        self.assertTrue(values.has_surcharge)
        self.assertEqual(values.pv_date, "16/06/69")

    def test_strips_statute_suffix_from_company_name(self) -> None:
        glued = (
            "ชื่อผู้มีหน้าที่หักภาษี ณ ที่จ่าย (หน่วยงาน) : สาขาที่ 00000\n"
            "ห้างหุ้นส่วนจำกัด ธนทรัพย์เจริญ 99 (3) มาตรา 69 ทวิ แห่งประมวลรัษฎากร\n"
        )
        self.assertEqual(
            Pnd30PdfService.extract_company_name(glued),
            "ห้างหุ้นส่วนจำกัด ธนทรัพย์เจริญ 99",
        )

    def test_reads_2411_without_surcharge(self) -> None:
        name = Pnd30PdfService.extract_company_name(_SAMPLE_NO_SURCHARGE)
        values = Pnd30PdfService.extract_form_values(_SAMPLE_NO_SURCHARGE)
        self.assertEqual(name, "ห้างหุ้นส่วนจำกัด 2411")
        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values.tax_withheld, 36.00)
        self.assertFalse(values.has_surcharge)
        self.assertEqual(values.pv_date, "08/07/69")


class Pnd30MatchTests(unittest.TestCase):
    def test_matches_pdf_name_to_excel_name(self) -> None:
        records = [
            Pnd30PdfRecord(
                pdf_path=Path("a.pdf"),
                company_name="ห้างหุ้นส่วนจำกัด ธนทรัพย์เจริญ 99",
                form_values=Pnd30FormValues(tax_withheld=1020.94, surcharge=15.31, pv_date="16/06/69"),
            )
        ]
        jobs = Pnd30MatchService.match_jobs(records, ["หจก.ธนทรัพย์เจริญ 99", "หจก.2411"])
        self.assertEqual(jobs[0].excel_name, "หจก.ธนทรัพย์เจริญ 99")


class Pnd30FillTests(unittest.TestCase):
    def test_types_surcharge_line_then_cash(self) -> None:
        image = RecordingImage()
        values = Pnd30FormValues(tax_withheld=1020.94, surcharge=15.31, pv_date="16/06/69")
        fill_pv(image, _config(), values, lambda _msg: None)
        events = _typed_and_pressed(image.events)
        self.assertEqual(
            events,
            [
                ("press", ("enter",)),
                ("type_keys", "16/06/69", True),
                ("press", ("enter",)),
                ("type_thai", "รายละเอียด PV", True),
                ("press", ("enter",)),
                ("type_text", "2132-02", False),
                ("press", ("enter",)),
                ("press", ("enter",)),
                ("type_text", "1,020.94", True),
                ("press", ("enter",)),
                ("type_text", "5390-01", False),
                ("press", ("enter",)),
                ("press", ("enter",)),
                ("type_text", "15.31", True),
                ("press", ("enter",)),
                ("type_text", "1111-00", False),
                ("press", ("enter",)),
                ("press", ("enter",)),
                ("press", ("enter",)),
                ("press", ("f2",)),
                ("press", ("f9",)),
                ("press", ("esc",)),
            ],
        )
        self.assertNotIn(("press", ("alt", "a")), events)

    def test_skips_surcharge_when_line_3_empty(self) -> None:
        image = RecordingImage()
        values = Pnd30FormValues(tax_withheld=36.00, surcharge=0.0, pv_date="08/07/69")
        fill_pv(image, _config(), values, lambda _msg: None)
        events = _typed_and_pressed(image.events)
        codes = [event[1] for event in events if event[0] == "type_text"]
        self.assertEqual(codes, ["2132-02", "36.00", "1111-00"])
        self.assertNotIn("5390-01", codes)


if __name__ == "__main__":
    unittest.main()

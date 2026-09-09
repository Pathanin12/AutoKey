from __future__ import annotations

import unittest
from pathlib import Path

from models.pp30_form_config import Pp30FormConfig
from models.pp30_form_values import Pp30FormValues
from services.pp30_fill_new_shop_service import fill_jv as fill_new_shop_jv
from services.pp30_fill_no_pay_normal_service import fill_jv as fill_no_pay_normal_jv
from services.pp30_fill_pay_service import fill_jv as fill_pay_jv
from services.pp30_fill_pay_service import fill_pv as fill_pay_pv
from services.pp30_fill_penalty_service import fill_jv as fill_penalty_jv
from services.pp30_fill_penalty_service import fill_pv as fill_penalty_pv


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


def _form_config() -> Pp30FormConfig:
    return Pp30FormConfig(
        pdf_folder=Path("/tmp"),
        excel_path=Path("/tmp/a.xlsx"),
        jv_date="10/10/69",
        jv_description="รายละเอียด JV",
        pv_description="รายละเอียด PV",
        report_output_dir=Path("/tmp/out"),
    )


def _values() -> Pp30FormValues:
    return Pp30FormValues(
        vat_sale=100.0,
        vat_purchase=23.5,
        amount_due=88.75,
        pv_date="13/08/69",
        line_8=10.0,
        line_10=171572.80,
        line_13=1.0,
        line_14=2.0,
        line_15=91.75,
    )


def _typed_and_pressed(events: list[tuple]) -> list[tuple]:
    return [event for event in events if event[0] in {"type_text", "press", "type_keys", "type_thai"}]


class Pp30SpecialFillTests(unittest.TestCase):
    def test_no_pay_normal_types_1156_then_f2_then_esc_twice(self) -> None:
        image = RecordingImage()
        fill_no_pay_normal_jv(image, _form_config(), _values(), lambda _msg: None)
        events = _typed_and_pressed(image.events)
        codes = [event[1] for event in events if event[0] == "type_text"]
        self.assertEqual(codes, ["2135-00", "100.00", "1154-00", "23.50", "1156-00"])
        shop_index = events.index(("type_text", "1156-00", False))
        self.assertEqual(
            events[shop_index + 1 :],
            [
                ("press", ("enter",)),
                ("press", ("enter",)),
                ("press", ("enter",)),
                ("press", ("f2",)),
                ("press", ("f9",)),
                ("press", ("esc",)),
                ("press", ("esc",)),
            ],
        )
        self.assertNotIn("171,572.80", codes)
        self.assertNotIn("2137-00", codes)

    def test_new_shop_uses_1156_then_1154_then_esc_once(self) -> None:
        image = RecordingImage()
        fill_new_shop_jv(image, _form_config(), _values(), lambda _msg: None)
        events = _typed_and_pressed(image.events)
        codes = [event[1] for event in events if event[0] == "type_text"]
        self.assertEqual(codes[:2], ["1156-00", "23.50"])
        self.assertIn("1154-00", codes)
        self.assertNotIn("2135-00", codes)
        self.assertEqual(events[-3:], [("press", ("f2",)), ("press", ("f9",)), ("press", ("esc",))])
        self.assertEqual(sum(1 for event in events if event == ("press", ("esc",))), 1)

    def test_pay_jv_enters_after_line_10_then_2137_and_esc_twice(self) -> None:
        image = RecordingImage()
        fill_pay_jv(image, _form_config(), _values(), lambda _msg: None)
        events = _typed_and_pressed(image.events)
        codes = [event[1] for event in events if event[0] == "type_text"]
        self.assertEqual(
            codes,
            ["2135-00", "100.00", "1154-00", "23.50", "1156-00", "171,572.80", "2137-00"],
        )
        self.assertNotIn("10.00", codes)
        self.assertEqual(events[-2:], [("press", ("esc",)), ("press", ("esc",))])

    def test_pay_pv_uses_2137_then_1154_decimal_of_line_11_then_cash(self) -> None:
        image = RecordingImage()
        fill_pay_pv(image, _form_config(), _values(), lambda _msg: None)
        events = _typed_and_pressed(image.events)
        codes = [event[1] for event in events if event[0] == "type_text"]
        self.assertEqual(codes, ["2137-00", "88.75", "1154-00", "0.75", "1111-00"])
        self.assertEqual(events[-2:], [("press", ("f2",)), ("press", ("f9",))])
        self.assertNotIn("4200-03", codes)

    def test_penalty_jv_uses_2135_then_1154_then_2137(self) -> None:
        image = RecordingImage()
        fill_penalty_jv(image, _form_config(), _values(), lambda _msg: None)
        events = _typed_and_pressed(image.events)
        codes = [event[1] for event in events if event[0] == "type_text"]
        self.assertEqual(codes, ["2135-00", "100.00", "1154-00", "23.50", "2137-00"])
        self.assertEqual(events[-2:], [("press", ("esc",)), ("press", ("esc",))])
        self.assertNotIn("5390-01", codes)

    def test_penalty_jv_skips_1154_when_line_7_is_empty(self) -> None:
        image = RecordingImage()
        values = Pp30FormValues(
            vat_sale=26496.79,
            vat_purchase=0.0,
            amount_due=28219.0,
            pv_date="24/08/69",
            line_8=26496.79,
            line_13=397.45,
            line_14=1324.84,
            line_15=29941.29,
        )
        fill_penalty_jv(image, _form_config(), values, lambda _msg: None)
        codes = [event[1] for event in image.events if event[0] == "type_text"]
        self.assertEqual(codes, ["2135-00", "26,496.79", "2137-00"])
        self.assertNotIn("5390-01", codes)

    def test_no_pay_normal_skips_1154_when_line_7_is_empty(self) -> None:
        image = RecordingImage()
        values = Pp30FormValues(
            vat_sale=100.0,
            vat_purchase=0.0,
            amount_due=0.0,
            pv_date="13/08/69",
            line_8=0.0,
            line_10=50.0,
        )
        fill_no_pay_normal_jv(image, _form_config(), values, lambda _msg: None)
        codes = [event[1] for event in image.events if event[0] == "type_text"]
        self.assertEqual(codes, ["2135-00", "100.00", "1156-00"])

    def test_pay_jv_always_types_1154_then_1156_line_10_then_2137(self) -> None:
        image = RecordingImage()
        values = Pp30FormValues(
            vat_sale=100.0,
            vat_purchase=0.0,
            amount_due=88.75,
            pv_date="13/08/69",
            line_8=100.0,
            line_10=10.0,
        )
        fill_pay_jv(image, _form_config(), values, lambda _msg: None)
        codes = [event[1] for event in image.events if event[0] == "type_text"]
        self.assertEqual(codes, ["2135-00", "100.00", "1154-00", "0.00", "1156-00", "10.00", "2137-00"])
        self.assertNotIn("5390-01", codes)

    def test_penalty_pv_uses_2137_then_5390_then_4200_decimal_of_line_15(self) -> None:
        image = RecordingImage()
        fill_penalty_pv(image, _form_config(), _values(), lambda _msg: None)
        events = _typed_and_pressed(image.events)
        codes = [event[1] for event in events if event[0] == "type_text"]
        self.assertEqual(codes, ["2137-00", "91.75", "5390-01", "3.00", "4200-03", "0.75", "1111-00"])

    def test_special_fill_services_do_not_import_each_other(self) -> None:
        root = Path(__file__).resolve().parent.parent
        files = (
            root / "services/pp30_fill_no_pay_normal_service.py",
            root / "services/pp30_fill_new_shop_service.py",
            root / "services/pp30_fill_pay_service.py",
            root / "services/pp30_fill_penalty_service.py",
        )
        names = {path.name for path in files}
        for path in files:
            source = path.read_text(encoding="utf-8")
            others = names - {path.name}
            for other in others:
                self.assertNotIn(other.replace(".py", ""), source)


if __name__ == "__main__":
    unittest.main()

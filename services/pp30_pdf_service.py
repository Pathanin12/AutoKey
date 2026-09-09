from __future__ import annotations

import re
from pathlib import Path

from constants.date_utils import THAI_MONTHS, format_express_pv_date
from models.pp30_form_values import Pp30FormValues
from models.pp30_matched_job import Pp30PdfRecord
from services.lookup_match_service import is_plausible_vendor_name, tidy_vendor_name
from services.pp30_amount_service import line_8_and_9, line_money, money_amounts
from services.pp30_extract_new_shop_service import complete_new_shop_lines
from services.pp30_extract_no_pay_normal_service import complete_no_pay_normal_lines
from services.pp30_extract_pay_service import complete_pay_lines
from services.pp30_extract_penalty_service import complete_penalty_lines

_P30_FILE_SUFFIX = re.compile(r"\s+\d{4}\s+\d{2}\s+P30\s+Form.*$", re.IGNORECASE)
_SLASH_DATE_RE = re.compile(
    r"วันที่่?\s*[:：]?\s*(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{2,4})"
)
_FILE_DATE_RE = re.compile(
    r"ยื่นวันที่่?\s*(\d{1,2})\s*เดือน\s*([ก-๙.]+)\s*พ\.?\s*ศ\.?\s*(\d{4})"
)


_COMPANY_PREFIXES = (
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญนิติบุคคล",
    "ห้างหุ้นส่วนสามัญ",
    "บริษัทจำกัดมหาชน",
    "บริษัท ",
    "บจก.",
    "หจก.",
)

_NUMBERED_LINE_RE = re.compile(r"^\s*(\d{1,2})[\.\)\s]")
_LINE_KEYWORDS = {
    5: ("ภาษีขาย",),
    7: ("ภาษีซื้อ",),
    8: ("ภาษีที่ต้องชำระ",),
    9: ("ภาษีที่ชำระเกินเดือนนี้", "ชำระเกินเดือนนี้"),
    10: ("ยกมา",),
    11: ("ต้องชำระ",),
    12: ("ชำระเกิน",),
    13: ("เงินเพิ่ม",),
    14: ("เบี้ยปรับ",),
    15: ("รวมภาษีที่ต้องชำระ",),
}

_SKIP_LINES = {
    "แบบแสดงรายการภาษีมูลค่าเพิ่ม",
    "ชื่อผู้ประกอบการ",
    "ชื่อสถานประกอบการ",
    "มาหักในการคำนวณภาษีเดือนนี้",
    "ภ.พ.30",
    "ภพ.30",
    "ภพ30",
}


class Pp30PdfService:
    @staticmethod
    def read_text(pdf_path: Path) -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        pages: list[str] = []
        for page in reader.pages:
            layout = ""
            try:
                layout = page.extract_text(extraction_mode="layout") or ""
            except TypeError:
                layout = ""
            plain = page.extract_text() or ""
            pages.append("\n".join(part for part in (layout, plain) if part))
        return "\n".join(pages)

    @staticmethod
    def extract_company_name(text: str) -> str:
        lines = [tidy_vendor_name(line) for line in (text or "").splitlines()]
        lines = [line for line in lines if line]
        after_label: str | None = None
        saw_label = False
        for line in lines:
            if "ชื่อผู้ประกอบการ" in line.replace(" ", ""):
                saw_label = True
                continue
            if saw_label and after_label is None and _is_company_line(line):
                after_label = line
                break
        if after_label:
            return after_label
        for line in lines:
            if _is_company_line(line):
                return line
        return ""

    @staticmethod
    def extract_form_values(text: str) -> Pp30FormValues | None:
        pv_date = _extract_pv_date(text)
        lines = _extract_tax_lines(text)
        if lines is None or not pv_date:
            return None
        return Pp30FormValues(pv_date=pv_date, **lines)

    @staticmethod
    def load_records(pdf_files: list[Path]) -> list[Pp30PdfRecord]:
        records: list[Pp30PdfRecord] = []
        for pdf_path in pdf_files:
            text = Pp30PdfService.read_text(pdf_path)
            name = Pp30PdfService.extract_company_name(text)
            values = Pp30PdfService.extract_form_values(text)
            records.append(
                Pp30PdfRecord(pdf_path=pdf_path, company_name=name, form_values=values)
            )
        return records


def company_hint_from_filename(pdf_path: Path) -> str:
    """ชื่อจากไฟล์ ภพ.30 เช่น 'ฉัตราภัทร์ 2569 07 P30 Form 01.pdf' → 'ฉัตราภัทร์'"""
    return tidy_vendor_name(_P30_FILE_SUFFIX.sub("", pdf_path.stem))


def _is_company_line(line: str) -> bool:
    if line in _SKIP_LINES or not is_plausible_vendor_name(line):
        return False
    compact = line.replace(" ", "")
    if compact in {item.replace(" ", "") for item in _SKIP_LINES}:
        return False
    return any(line.startswith(prefix) for prefix in _COMPANY_PREFIXES)


def _labeled_line_amounts(text: str) -> dict[int, float]:
    found: dict[int, float] = {}
    for raw in (text or "").splitlines():
        match = _NUMBERED_LINE_RE.match(raw)
        if not match:
            continue
        number = int(match.group(1))
        keywords = _LINE_KEYWORDS.get(number)
        if not keywords or not any(key in raw for key in keywords):
            continue
        amount = line_money(raw, allow_zero=True)
        if amount is None:
            continue
        found[number] = amount
    return found


def _extract_tax_lines(text: str) -> dict[str, float] | None:
    labeled = _labeled_line_amounts(text)
    amounts = money_amounts(text)
    line5 = labeled.get(5)
    line7 = labeled.get(7)
    new_shop = complete_new_shop_lines(line5, line7, labeled, text)
    if new_shop is not None:
        return new_shop

    pair = _extract_line_5_7(text)
    if line5 is None and pair is not None:
        line5 = pair[0]
    if line7 is None and pair is not None:
        line7 = pair[1]
    if line5 is None or line7 is None:
        return None

    penalty = complete_penalty_lines(line5, line7, labeled, amounts)
    if penalty is not None:
        return penalty
    no_pay = complete_no_pay_normal_lines(line5, line7, labeled, amounts)
    if no_pay is not None:
        return no_pay
    pay = complete_pay_lines(line5, line7, labeled, amounts)
    if pay is not None:
        return pay
    return _unclassified_lines(line5, line7, labeled)


def _unclassified_lines(
    line5: float,
    line7: float,
    labeled: dict[int, float],
) -> dict[str, float]:
    line8, line9 = line_8_and_9(line5, line7, labeled)
    return {
        "vat_sale": line5,
        "vat_purchase": line7,
        "amount_due": labeled.get(11, 0.0),
        "line_8": line8,
        "line_9": line9,
        "line_10": labeled.get(10, 0.0),
        "line_12": labeled.get(12, 0.0),
        "line_13": labeled.get(13, 0.0),
        "line_14": labeled.get(14, 0.0),
        "line_15": labeled.get(15, 0.0),
    }


def _extract_line_5_7(text: str) -> tuple[float, float] | None:
    amounts = money_amounts(text)
    if not amounts:
        return None

    best: tuple[float, float, float] | None = None
    for vat_sale in amounts:
        for vat_purchase in amounts:
            line8 = round(vat_sale - vat_purchase, 2)
            if line8 <= 0:
                continue
            if not any(abs(line8 - other) < 0.005 for other in amounts):
                continue
            score = 0.0
            for sales in amounts:
                if sales <= vat_sale * 5:
                    continue
                ratio = vat_sale / sales
                if 0.065 <= ratio <= 0.075:
                    score = 2.0
                    break
            if vat_sale > vat_purchase:
                score += 0.5
            if best is None or score > best[0] or (score == best[0] and vat_sale > best[1]):
                best = (score, vat_sale, vat_purchase)
    if best is not None:
        return best[1], best[2]

    for vat_sale in amounts:
        for sales in amounts:
            if sales <= vat_sale * 5:
                continue
            ratio = vat_sale / sales
            if 0.065 <= ratio <= 0.075:
                return vat_sale, 0.0
    return None


def _extract_pv_date(text: str) -> str:
    slash = _SLASH_DATE_RE.search(text or "")
    if slash:
        day, month, year = slash.groups()
        return format_express_pv_date(f"{int(day):02d}/{int(month):02d}/{year}")

    filed = _FILE_DATE_RE.search(text or "")
    if not filed:
        return ""
    day_text, month_name, year_text = filed.groups()
    month = THAI_MONTHS.get(month_name.replace(".", ""))
    if month is None:
        return ""
    return format_express_pv_date(f"{int(day_text):02d}/{month:02d}/{year_text}")

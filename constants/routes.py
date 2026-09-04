import sys
from pathlib import Path

from constants.date_utils import PV_DATE_EXAMPLE


def _resolve_project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _resolve_project_root()
ASSETS_DIR = PROJECT_ROOT / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

TOPIC_PAYMENT_JOURNAL = "payment_journal"
TOPIC_PP30 = "pp30"
TOPIC_LABEL = "สมุดรายวันจ่าย"

PAGE_MENU = "menu"
PAGE_KA_TAM = "ka_tam"
PAGE_PP30 = "pp30"

ACCOUNT_SERVICE = "5330-05"
ACCOUNT_VAT = "1154-00"
ACCOUNT_WT = "2132-02"
ACCOUNT_CASH = "1111-00"
ACCOUNT_PP30_VAT_SALE = "2135-00"
ACCOUNT_PP30_VAT_PURCHASE = ACCOUNT_VAT
ACCOUNT_PP30_VAT_PAYABLE = "2137-00"
ACCOUNT_PP30_DECIMAL = "4200-03"
ACCOUNT_REPORT_CODES = (ACCOUNT_SERVICE, ACCOUNT_VAT, ACCOUNT_WT)
PP30_ACCOUNT_REPORT_CODES = (
    ACCOUNT_PP30_VAT_PURCHASE,
    ACCOUNT_PP30_VAT_SALE,
    ACCOUNT_PP30_VAT_PAYABLE,
)
REPORT_SCREENSHOT_FILENAME = "report.png"
ACCOUNT_REPORT_CAPTURE_WAIT = 1.5
ACCOUNT_REPORT_FIELD_WAIT = 0.08
ACCOUNT_REPORT_MENU_WAIT = 0.35

# เส้นทางเมนู 5 > 1 > 2 — คลิกจับภาพ (Express ไม่มีคีย์ลัด)
MENU_ACCOUNT_LABEL = "5.บัญชี"
MENU_DAILY_ENTRY_LABEL = "1.ลงประจำวัน"
MENU_PAYMENT_JOURNAL_LABEL = "2.สมุดรายวันจ่าย"
MENU_PAYMENT_JOURNAL_PATH = "5 > 1 > 2"
MENU_GENERAL_JOURNAL_LABEL = "1.สมุดรายวันทั่วไป"
MENU_GENERAL_JOURNAL_PATH = "5 > 1 > 1"
MENU_ACCOUNT_REPORT_LABEL = "5. รายงานบัญชี"
MENU_GENERAL_LEDGER_LABEL = "4. แยกประเภท"
MENU_REPORT_NORMAL_LABEL = "1. แบบปกติ"
MENU_LEDGER_REPORT_PATH = "F12 > 5. รายงานบัญชี > 4. แยกประเภท > 1. แบบปกติ"
ACCOUNT_REPORT_FLOW_PATH = "F12 → รายงานบัญชี → แยกประเภท → แบบปกติ → กรอก → F5 → แคป"
ACCOUNT_REPORT_CAPTURE_ENABLED = False
PV_NEW_FILE_KEYS = ("alt", "a")
MENU_OTHERS = "8"
MENU_OTHERS_CHANGE_COMPANY = "8"
VENDOR_LOOKUP_KEY = "f8"
EXCEL_OPEN_EXTENSIONS = ("xlsx", "xlsm")
PDF_OPEN_EXTENSIONS = ("pdf",)

UI_TEXT = {
    "app_title": "AutoKey",
    "menu_title": "เลือกเมนู",
    "menu_hint": "เลือกงานที่ต้องการทำ",
    "menu_ka_tam": "ค่าทำ",
    "menu_ka_tam_hint": "สมุดรายวันจ่าย — ค้นหาบริษัทแล้วกรอก PV",
    "menu_pp30": "ภพ.30",
    "menu_pp30_hint": "ภาษีมูลค่าเพิ่ม — อ่าน PDF แล้วเทียบชื่อกับ Excel",
    "menu_unavailable": "เมนูนี้ยังไม่พร้อมใช้",
    "back_to_menu": "กลับเมนู",
    "settings_frame": "ตั้งค่าก่อนรัน",
    "excel_file": "ไฟล์ Excel",
    "choose_file": "เลือกไฟล์...",
    "excel_summary_empty": "ยังไม่ได้เลือกไฟล์ Excel",
    "pv_date": "วันที่ใบสำคัญ",
    "pv_date_hint": f"รูปแบบ วัน/เดือน/ปี(2 หลัก) เช่น {PV_DATE_EXAMPLE} — ค่าเริ่มต้นเป็นวันนี้",
    "start_from_no": "เริ่มที่ No.",
    "start_from_no_hint": "คอลัมน์ No ใน Excel — ใช้ resume หลัง error (เช่น เริ่มใหม่ที่ 5)",
    "description": "รายละเอียด",
    "description_hint": "ใช้เหมือนกันทุกแถวในรอบนั้น — พิมพ์ในช่องรายละเอียดหลัง Alt+A",
    "tax_payer_id": "เลขผู้เสียภาษี",
    "tax_payer_id_hint": "ใช้ค่าจากช่องนี้ทุกแถวตอนกรอกใบกำกับ — ไม่ได้อ่านจาก Excel",
    "report_output_dir": "โฟลเดอร์เก็บไฟล์",
    "choose_folder": "เลือก...",
    "report_output_dir_hint": "เก็บแคปรายงานเป็น โฟลเดอร์หลัก / นิติ / เดือน / รหัสบัญชี / report.png",
    "start": "เริ่มทำงาน",
    "stop": "หยุด ({hotkey})",
    "cancel_hotkey_hint": "กด {hotkey} เพื่อยกเลิกขณะทำงาน",
    "window_hidden": "ซ่อนหน้าต่างแล้ว — กำลังทำงาน...",
    "window_restored": "แสดงหน้าต่างอีกครั้ง",
    "status_frame": "สถานะ",
    "copy_log": "คัดลอก log",
    "select_all_log": "เลือกทั้งหมด",
    "copy_all_log": "คัดลอกทั้งหมด",
    "welcome_log": (
        "Express อยู่ dialog เลือกข้อมูล → กดเริ่ม\n"
        "AutoKey: ค้นหา + verify → 5 > 1 > 2 → ทำ PV ทุกแถว\n"
        "กด Ctrl+F9 หรือ Esc เพื่อยกเลิกขณะทำงาน"
    ),
    "ready": "พร้อมทำงาน",
    "confirm_title": "ยืนยันการทำงาน",
    "confirm_message": (
        "Express ต้องเปิดอยู่ (AutoKey จะโฟกัส Express ให้อัตโนมัติ)\n"
        "AutoKey: PV ทุกแถว (F10 แล้วกรอกภาษีซื้อต่อแถว)\n"
        "ต้องการเริ่ม Auto หรือไม่?"
    ),
    "stop_requested": "ส่งคำสั่งหยุด...",
    "starting": "กำลังเริ่ม — โฟกัส Express...",
    "warming_up": "เตรียมระบบจับภาพ...",
    "type_log": "พิมพ์ — {field}: {text}",
    "paste_log": "วาง — {field}: {text}",
    "clipboard_copy_log": "คัดลอก — {field}: {text}",
    "excel_copy_log": "Excel copy — {cell}: {text}",
    "excel_loaded": "โหลดไฟล์: {path}",
    "excel_sheet_line": "  • {sheet}: {rows} รายการ",
    "excel_total": "พบ {rows} รายการ",
    "no_excel_data": "ไม่พบข้อมูลที่รองรับในไฟล์นี้",
    "no_excel_loaded": "กรุณาเลือกไฟล์ Excel ก่อน",
    "pp30_pdf_folder": "โฟลเดอร์ PDF",
    "pp30_pdf_summary_empty": "ยังไม่ได้เลือกโฟลเดอร์ PDF",
    "pp30_pdf_total": "พบ {count} ไฟล์ PDF",
    "pp30_jv_date": "วันที่ JV",
    "pp30_jv_description": "รายละเอียด JV",
    "pp30_pv_description": "รายละเอียด PV",
    "pp30_welcome_log": (
        "Express อยู่ dialog เลือกข้อมูล → กดเริ่ม\n"
        "AutoKey: อ่าน ภพ.30 → ค้นห้าง → JV 5-1-1 → PV 5-1-2 → แคปรายงาน\n"
        "กด Ctrl+F9 หรือ Esc เพื่อยกเลิกขณะทำงาน"
    ),
    "pp30_confirm_message": (
        "Express ต้องเปิดอยู่ที่ dialog เลือกข้อมูล\n"
        "AutoKey จะเทียบชื่อ PDF กับ Excel แล้วทำ JV / PV / แคปรายงานทีละห้าง\n"
        "ต้องการเริ่มหรือไม่?"
    ),
    "pp30_match_log": "เทียบชื่อ — PDF: {pdf_name} → Excel: {excel_name}",
    "pp30_pdf_name_missing": "อ่านชื่อจาก PDF ไม่ได้: {path}",
    "pp30_unmatched": "เทียบชื่อกับ Excel ไม่ได้: {pdf_name} ({path})",
    "pp30_search_log": "ค้นหาห้าง: {name}",
    "pp30_done": "ทำ ภพ.30 ครบ {count} รายการ",
    "pp30_pdf_values_missing": "อ่านข้อ 5/7/11 หรือวันที่จาก PDF ไม่ได้: {path}",
    "pp30_jv_log": "กรอก JV {date} — 2135-00={sale} 1154-00={purchase}",
    "pp30_pv_log": "กรอก PV {date} — 2137-00={due} 4200-03={decimal}",
    "pp30_report_log": "แคปรายงาน {codes}",
}

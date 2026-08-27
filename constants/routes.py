import sys
from pathlib import Path


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
TOPIC_LABEL = "สมุดรายวันจ่าย"

ACCOUNT_SERVICE = "5330-05"
ACCOUNT_VAT = "1154-00"
ACCOUNT_WT = "2132-02"
ACCOUNT_CASH = "1111-00"

# เส้นทางเมนู 5 > 1 > 2 — คลิกจับภาพ (Express ไม่มีคีย์ลัด)
MENU_ACCOUNT_LABEL = "5.บัญชี"
MENU_DAILY_ENTRY_LABEL = "1.ลงประจำวัน"
MENU_PAYMENT_JOURNAL_LABEL = "2.สมุดรายวันจ่าย"
MENU_PAYMENT_JOURNAL_PATH = "5 > 1 > 2"
PV_NEW_FILE_KEYS = ("alt", "a")
MENU_OTHERS = "8"
MENU_OTHERS_CHANGE_COMPANY = "8"
VENDOR_LOOKUP_KEY = "f8"

UI_TEXT = {
    "app_title": "AutoKey — สมุดรายวันจ่าย",
    "settings_frame": "ตั้งค่าก่อนรัน",
    "excel_file": "ไฟล์ Excel",
    "choose_file": "เลือกไฟล์...",
    "excel_summary_empty": "ยังไม่ได้เลือกไฟล์ Excel",
    "pv_date": "วันที่ใบสำคัญ",
    "pv_date_hint": "รูปแบบ วัน/เดือน/ปี(2 หลัก) เช่น 25/07/69 — ค่าเริ่มต้นเป็นวันนี้",
    "start_from_no": "เริ่มที่ No.",
    "start_from_no_hint": "คอลัมน์ No ใน Excel — ใช้ resume หลัง error (เช่น เริ่มใหม่ที่ 5)",
    "description": "รายละเอียด",
    "description_hint": "ใช้เหมือนกันทุกแถวในรอบนั้น — พิมพ์ในช่องรายละเอียดหลัง Alt+A",
    "tax_payer_id": "เลขผู้เสียภาษี",
    "tax_payer_id_hint": "อ่านจากคอลัมน์ TAX ID ใน Excel ทุกแถว — ช่องนี้ใช้เมื่อแถวใดใน Excel ว่าง",
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
    "paste_log": "วาง — {field}: {text}",
    "excel_loaded": "โหลดไฟล์: {path}",
    "excel_sheet_line": "  • {sheet}: {rows} รายการ",
    "excel_total": "พบ {rows} รายการ",
    "no_excel_data": "ไม่พบข้อมูลที่รองรับในไฟล์นี้",
    "no_excel_loaded": "กรุณาเลือกไฟล์ Excel ก่อน",
}

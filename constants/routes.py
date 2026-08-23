from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
REFERENCE_DIR = ASSETS_DIR / "reference"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEFAULT_EXCEL_PATH = Path.home() / "Downloads" / "ค่าทำ.xlsx"

TOPIC_PAYMENT_JOURNAL = "payment_journal"
TOPIC_LABEL = "สมุดรายวันจ่าย"

ACCOUNT_SERVICE = "5330-05"
ACCOUNT_VAT = "1154-00"
ACCOUNT_CASH = "1111-00"

MENU_ACCOUNT = "5"
MENU_DAILY_ENTRY = "1"
MENU_PAYMENT_JOURNAL = "2"
MENU_OTHERS = "8"

UI_TEXT = {
    "app_title": "AutoKey — สมุดรายวันจ่าย",
    "settings_frame": "ตั้งค่าก่อนรัน",
    "excel_file": "ไฟล์ Excel",
    "choose_file": "เลือกไฟล์...",
    "excel_summary_empty": "ยังไม่ได้เลือกไฟล์ Excel",
    "pv_date": "วันที่ใบสำคัญ",
    "pv_date_hint": "ค่าเริ่มต้นเป็นวันที่ทำการ (วันนี้) — แก้ได้ก่อนกดเริ่ม",
    "description": "รายละเอียด",
    "tax_payer_id": "เลขผู้เสียภาษี",
    "tax_payer_id_hint": "อ่านจากคอลัมน์ TAX ID ใน Excel ทุกแถว — ช่องนี้ใช้เมื่อแถวใดใน Excel ว่าง",
    "start": "เริ่มทำงาน",
    "stop": "หยุด ({hotkey})",
    "cancel_hotkey_hint": "กด {hotkey} เพื่อยกเลิกขณะทำงาน",
    "window_hidden": "ซ่อนหน้าต่างแล้ว — กำลังทำงาน...",
    "window_restored": "แสดงหน้าต่างอีกครั้ง",
    "status_frame": "สถานะ",
    "welcome_log": (
        "เปิด Express อยู่หน้าเมนูหลัก (เลือกบริษัทแล้ว) แล้วกดเริ่ม — AutoKey เปิด PV (5→1→2)\n"
        "กด Ctrl+F9 หรือ Esc เพื่อยกเลิกขณะทำงาน"
    ),
    "ready": "พร้อมทำงาน",
    "confirm_title": "ยืนยันการทำงาน",
    "confirm_message": (
        "ตรวจสอบว่า Express เปิดอยู่หน้าเมนูหลัก (บริษัทเดียว — เลือกเองก่อนรัน)\n"
        "AutoKey จะเปิดสมุดรายวันจ่าย (5→1→2) แล้วทำทุกแถว\n"
        "ต้องการเริ่ม Auto หรือไม่?"
    ),
    "stop_requested": "ส่งคำสั่งหยุด...",
    "excel_loaded": "โหลดไฟล์: {path}",
    "excel_sheet_line": "  • {sheet}: {rows} รายการ",
    "excel_total": "รวม {rows} รายการ จาก {sheets} ชีต",
    "no_excel_data": "ไม่พบข้อมูลที่รองรับในไฟล์นี้",
    "no_excel_loaded": "กรุณาเลือกไฟล์ Excel ก่อน",
}

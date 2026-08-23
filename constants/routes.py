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
    "use_work_date": "ใช้วันที่ทำการจาก Express Accounting",
    "pv_date": "วันที่ใบสำคัญ",
    "description": "รายละเอียด",
    "tax_payer_id": "เลขผู้เสียภาษี",
    "tax_payer_id_hint": "อ่านจากคอลัมน์ TAX ID ใน Excel ทุกแถว — ช่องนี้ใช้เมื่อแถวใดใน Excel ว่าง",
    "switch_company": "หลังจบ PV ทุกแถว ให้ทำโฟล์สุดท้าย (กด 8 เปลี่ยนบริษัท)",
    "company_name": "ชื่อบริษัท (โฟล์แรก)",
    "company_name_hint": (
        "โฟล์แรก: 1) คลิก ค้นหา  2) พิมพ์ชื่อเต็ม  3) Enter 2 ครั้ง  "
        "→ dialog วันที่ทำการขึ้น  4) ตกลง"
    ),
    "next_company_name": "ชื่อบริษัทถัดไป (โฟล์สุดท้าย)",
    "next_company_name_hint": "โฟล์สุดท้าย — กด 8 แล้วเหมือนโฟล์แรก (ค้นหา → Enter×2 → ตกลง วันที่ทำการ)",
    "start": "เริ่มทำงาน",
    "stop": "หยุด ({hotkey})",
    "cancel_hotkey_hint": "กด {hotkey} เพื่อยกเลิกขณะทำงาน",
    "window_hidden": "ซ่อนหน้าต่างแล้ว — กำลังทำงาน...",
    "window_restored": "แสดงหน้าต่างอีกครั้ง",
    "status_frame": "สถานะ",
    "welcome_log": (
        "เปิด Express อยู่หน้า Dialog เลือกข้อมูล แล้วกดเริ่ม — AutoKey กด ค้นหา ให้เลย\n"
        "กด Ctrl+F9 หรือ Esc เพื่อยกเลิกขณะทำงาน"
    ),
    "ready": "พร้อมทำงาน",
    "confirm_title": "ยืนยันการทำงาน",
    "confirm_message": (
        "ตรวจสอบว่า Express เปิดอยู่หน้า Dialog เลือกข้อมูล (เลือกบริษัท)\n"
        "AutoKey จะกด ค้นหา → พิมพ์ชื่อ → Enter×2 → ตกลง (วันที่ทำการ)\n"
        "ต้องการเริ่ม Auto หรือไม่?"
    ),
    "stop_requested": "ส่งคำสั่งหยุด...",
    "excel_loaded": "โหลดไฟล์: {path}",
    "excel_sheet_line": "  • {sheet}: {rows} รายการ",
    "excel_total": "รวม {rows} รายการ จาก {sheets} ชีต",
    "no_excel_data": "ไม่พบข้อมูลที่รองรับในไฟล์นี้",
    "no_excel_loaded": "กรุณาเลือกไฟล์ Excel ก่อน",
}

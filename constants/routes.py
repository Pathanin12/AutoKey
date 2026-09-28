import sys
from pathlib import Path


def _resolve_project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _resolve_project_root()
ASSETS_DIR = PROJECT_ROOT / "assets"


def _resolve_config_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "config.yaml"
    return PROJECT_ROOT / "config.yaml"


CONFIG_PATH = _resolve_config_path()
SHOPS_FILE_NAME = "shops.yaml"
SHOPS_PATH = CONFIG_PATH.with_name(SHOPS_FILE_NAME)
SHOP_INDEX_FILE_KEY = "file"
SHOP_INDEX_SHOP_KEY = "shop"

PAGE_MENU = "menu"
PAGE_CONFIG = "config"
PAGE_KA_TAM = "ka_tam"
PAGE_PP30 = "pp30"
PAGE_PND30 = "pnd30"
PAGE_PND3 = "pnd3"
PAGE_INCOME = "income"
EKO_HTTP_URL = "https://cpall-h1.ekoapp.com"
EKO_LOGIN_PATH = "/api/v1/auth/login"
EKO_ORIGIN_URL = "https://cpall.ekoapp.com"
SBP_ORIGIN_URL = "https://sbp.cpall.co.th"
SBP_STATEMENT_PATH = "/statement/"
SBP_BFF_URL = "https://sbpmall-bff.cpall.co.th/api/v1"
SBP_AUTH_LOGIN_PATH = "/auth/login"
SBP_STORES_PATH = "/store-statement/dropdown/stores"
SBP_REPORT_TYPES_PATH = "/store-statement/dropdown/report-types"
SBP_SEARCH_REPORT_PATH = "/store-statement/search-report"
SBP_MERGE_FILE_PATH = "/store-statement/merge-file"
SBP_STATEMENT_TYPE = "sbp"
SBP_FILE_TYPE_NORMAL = "NORMAL"
INCOME_WANTED_REPORT_CODES = (
    "STMTRPT1",
    "STMTRPT2",
    "SAP001ARREC",
    "SAP002APREC",
    "SAP002APRECTAX",
    "SAP003WHTAP",
    "RT040079",
)
INCOME_WANTED_REPORT_NAMES = (
    "Statement Form 1",
    "Statement Form 2",
    "ใบเสร็จรับเงิน (ออกให้)",
    "ใบเสร็จรับเงิน (ออกแทน)",
    "ใบเสร็จรับเงิน/ใบกำกับภาษี (ออกให้)",
    "ใบเสร็จรับเงิน/ใบกำกับภาษี (ออกแทน)",
    "เอกสาร หัก ณ ที่จ่าย (ออกให้)",
    "เอกสาร หัก ณ ที่จ่าย (ออกแทน)",
    "รายงานอากรแสตมป์",
)
INCOME_PRINT_ALL_NAME = "{shop}.pdf"
MENU_BUTTON_HEIGHT = 75
MENU_BUTTON_IPADY = 26
PDF_OPEN_EXTENSIONS = ("pdf",)
DBF_ENCODING = "cp874"
ISINFO_FILE_NAMES = ("ISINFO.DBF", "isinfo.dbf")
ISINFO_SHOP_NAME_FIELD = "THINAM"

PP30_MODE_NORMAL = "normal"
PP30_MODE_SPECIAL = "special"
PP30_RUN_MODES = (PP30_MODE_NORMAL, PP30_MODE_SPECIAL)

INCOME_LOCK_NONE = "none"
INCOME_LOCK_PASSWORD = "password"
INCOME_LOCK_MODES = (INCOME_LOCK_NONE, INCOME_LOCK_PASSWORD)
INCOME_PDF_PASSWORD_SEPARATOR = "_"

ACCOUNT_CASH = "1111-00"
ACCOUNT_SERVICE = "5330-05"
ACCOUNT_VAT = "1154-00"
ACCOUNT_WT = "2132-02"
ACCOUNT_WT_PND3 = "2132-02"
ACCOUNT_PP30_VAT_SALE = "2135-00"
ACCOUNT_PP30_VAT_PURCHASE = ACCOUNT_VAT
ACCOUNT_PP30_VAT_PAYABLE = "2137-00"
ACCOUNT_PP30_NEW_SHOP = "1156-00"
ACCOUNT_PP30_PENALTY = "5390-01"
ACCOUNT_PP30_DECIMAL = "4200-03"
ACCOUNT_INCOME_RECEIVABLE = "1113-01"
ACCOUNT_INCOME_WHT = "1151-02"
ACCOUNT_INCOME_GOODS = "1153-01"
ACCOUNT_INCOME_ADVANCE = "2120-01"
ACCOUNT_INCOME_DEPOSIT = "1151-06"
ACCOUNT_INCOME_RENT = "4200-09"
ACCOUNT_INCOME = "4100-02"
INCOME_RV_TAX = "tax"
INCOME_RV_GOODS = "goods"
INCOME_RV_ADVANCE = "advance"
INCOME_RV_RENT = "rent"
INCOME_PV_TAX = "pv_tax"
INCOME_PV_RECEIPT = "pv_receipt"
INCOME_PAY_GOODS = "สินค้าและบริการ"
INCOME_PAY_ADVANCE = "เบิกเงินสำรอง"
INCOME_PAY_ADVANCE_ALT = "เบิกงานสำรอง"
INCOME_PAY_RENT = "ค่าเช่ารับ"
INCOME_PV_DEPOSIT_MARK = "เงินประกัน"
INCOME_PV_TAX_TITLE = "ใบเสร็จรับเงิน/ใบกำกับภาษี"
INCOME_PV_TAX_TITLE_GLUED = "ใบเสร็จรับเงินใบกำกับภาษี"
INCOME_RV_DESC = "บมจ.ซีพีออลล์-{topic} ด.{month}/{year}*{branch}"
INCOME_RV_TOPIC_TAX = "ค่าตอบแทนการบริหาร"
INCOME_RV_TOPIC_GOODS = "สินค้าและบริการ"
INCOME_RV_TOPIC_ADVANCE = "เบิกเงินสำรอง"
INCOME_RV_TOPIC_RENT = "ค่าเช่ารับ"
INCOME_PV_TAX_DESC = "บมจ.ซีพี ออลล์-ค่าสิทธ์ ด.{month}/{year}*{branch}"
INCOME_PV_DEPOSIT_DESC = "บมจ.ซีพีออลล์-เงินประกัน ด.{month}/{year}*{branch}"
INCOME_PV_INSTALL_DESC = "บมจ.ซีพีออลล์-ผ่อนเงินสำรอง ด.{month}/{year}*{branch}"
INCOME_PV_BOTH_DESC = "บมจ.ซีพีออลล์-ผ่อนเงินสำรอง,เงินประกัน {month}/{year}*{branch}"

GLJNL_FILE_NAMES = ("GLJNL.DBF", "gljnl.dbf")
GLJNLIT_FILE_NAMES = ("GLJNLIT.DBF", "gljnlit.dbf")
ISVAT_FILE_NAMES = ("ISVAT.DBF", "isvat.dbf")
VATREC_PURCHASE = "P"
VATREC_SALE = "S"
JNLTYP_JV = "00"
JNLTYP_PV = "01"
JNLTYP_RV = "02"
VOUCHER_JV_PREFIX = "JV"
VOUCHER_PV_PREFIX = "PV"
VOUCHER_RV_PREFIX = "RV"
JOURNAL_SRCJNL = "GL"
JOURNAL_TRNSTAT = "P"
JOURNAL_DOCSTAT = "N"
JOURNAL_CREBY_DEFAULT = "BIT9"
TRNTYP_DEBIT = "0"
TRNTYP_CREDIT = "1"
SEQIT_DEFAULT = " 1"

PP30_KIND_NORMAL = "normal"
PP30_KIND_NO_PAY_NORMAL = "no_pay_normal"
PP30_KIND_NO_PAY_NEW_SHOP = "no_pay_new_shop"
PP30_KIND_PAY = "pay"
PP30_KIND_PENALTY = "penalty"
PP30_KIND_SKIP_ZERO = "skip_zero"
PP30_KIND_UNKNOWN = "unknown"
PP30_PAYMENT_KINDS = (
    PP30_KIND_NORMAL,
    PP30_KIND_NO_PAY_NORMAL,
    PP30_KIND_NO_PAY_NEW_SHOP,
    PP30_KIND_PAY,
    PP30_KIND_PENALTY,
    PP30_KIND_SKIP_ZERO,
    PP30_KIND_UNKNOWN,
)

UI_TEXT = {
    "app_title": "AutoKey",
    "menu_title": "เลือกเมนู",
    "menu_hint": "เลือกงานที่ต้องการทำ",
    "menu_config": "Config",
    "menu_ka_tam": "ค่าทำ",
    "menu_ka_tam_hint": "สมุดรายวันจ่าย — อ่าน Excel แล้ว insert PV และใบกำกับ",
    "choose_file": "เลือกไฟล์...",
    "ka_tam_excel": "ไฟล์ Excel",
    "ka_tam_excel_empty": "ยังไม่ได้เลือกไฟล์ Excel",
    "ka_tam_excel_total": "พบ {count} แถว",
    "ka_tam_excel_invalid": "กรุณาเลือกไฟล์ Excel",
    "ka_tam_excel_none": "ไม่พบรายการในไฟล์ Excel",
    "ka_tam_pv_date": "วันที่ PV",
    "ka_tam_pv_date_invalid": "กรุณากรอกวันที่ PV ให้ครบ เช่น 25/07/69",
    "ka_tam_description": "รายละเอียด",
    "ka_tam_tax_payer": "เลขผู้เสียภาษี",
    "ka_tam_welcome_log": "เลือกไฟล์ Excel กรอกวันที่ รายละเอียด และเลขผู้เสียภาษี แล้วกดเริ่ม",
    "ka_tam_unmatched": "ไม่ตรง — Excel: {name}",
    "ka_tam_match_log": "ตรง — Excel: {excel_name} → {shop_name}",
    "ka_tam_skip_zero_log": "ข้าม — {name} ไม่มียอดค่าบริการ",
    "ka_tam_insert_log": "สรุป — {shop}: {detail}",
    "ka_tam_insert_done": "insert เสร็จ {inserted}/{total}",
    "menu_pp30": "ภ.พ.30",
    "menu_pp30_hint": "ภาษีมูลค่าเพิ่ม — อ่าน PDF แล้วเทียบชื่อกับโฟลเดอร์ห้าง",
    "menu_pnd30": "ภ.ง.ด.53",
    "menu_pnd30_hint": "ภาษีเงินได้หัก ณ ที่จ่าย — อ่าน PDF แล้วเทียบชื่อกับโฟลเดอร์ห้าง",
    "pnd30_description": "รายละเอียด",
    "pnd30_pdf_invalid": "กรุณาเลือกโฟลเดอร์ PDF",
    "pnd30_pdf_none": "ไม่พบไฟล์ PDF ในโฟลเดอร์นี้",
    "pnd30_welcome_log": "เลือกโฟลเดอร์ PDF กรอกรายละเอียด แล้วกดเริ่ม",
    "pnd30_skip_zero_log": "ข้าม — {name} ไม่มียอดภาษี",
    "pnd30_insert_log": "สรุป — {shop}: {detail}",
    "menu_pnd3": "ภ.ง.ด.3",
    "menu_pnd3_hint": "ภาษีเงินได้หัก ณ ที่จ่าย — อ่าน PDF แล้วเทียบชื่อกับโฟลเดอร์ห้าง",
    "pnd3_description": "รายละเอียด",
    "pnd3_pdf_invalid": "กรุณาเลือกโฟลเดอร์ PDF",
    "pnd3_pdf_none": "ไม่พบไฟล์ PDF ในโฟลเดอร์นี้",
    "pnd3_welcome_log": "เลือกโฟลเดอร์ PDF กรอกรายละเอียด แล้วกดเริ่ม",
    "pnd3_skip_zero_log": "ข้าม — {name} ไม่มียอดภาษี",
    "pnd3_insert_log": "สรุป — {shop}: {detail}",
    "menu_income": "รายได้",
    "menu_income_hint": "รายได้",
    "income_excel": "ไฟล์ Excel",
    "income_excel_empty": "ยังไม่ได้เลือกไฟล์ Excel",
    "income_excel_total": "พบ {count} ร้าน",
    "income_excel_invalid": "กรุณาเลือกไฟล์ Excel",
    "income_excel_none": "ไม่พบร้านในไฟล์ Excel",
    "income_start_date": "วันที่",
    "income_end_date": "วันที่สิ้นสุด",
    "income_date_invalid": "กรุณากรอกวันที่ให้ครบ เช่น 01/08/69",
    "income_save_folder": "โฟลเดอร์บันทึก PDF",
    "income_save_folder_empty": "ยังไม่ได้เลือกโฟลเดอร์บันทึก PDF",
    "income_pdf_invalid": "กรุณาเลือกโฟลเดอร์ PDF",
    "income_pdf_none": "ไม่พบไฟล์ PDF ในโฟลเดอร์นี้",
    "income_lock": "PDF",
    "income_lock_none": "ไม่มีรหัส",
    "income_lock_password": "มีรหัส",
    "income_login_failed": "เข้าสู่ระบบไม่ได้ — {name}",
    "income_download_log": "โหลดแล้ว — {name} สาขา {store}",
    "income_download_none": "ไม่พบรายงาน — {name} สาขา {store}",
    "income_welcome_log": "เลือกโฟลเดอร์ PDF กรอกวันที่ แล้วกดเริ่ม",
    "income_skip_zero_log": "ข้าม — {name} ไม่มียอด",
    "income_skip_image_log": "ข้าม — {path} เป็นรูปภาพ",
    "income_skip_locked_log": "ข้าม — {path} ติดรหัส",
    "income_skip_wrong_password_log": "ข้าม — {path} รหัสไม่ตรง",
    "income_skip_no_password_log": "ข้าม — {path} ชื่อไฟล์ไม่มีรหัส (ชื่อห้าง_รหัส)",
    "income_skip_no_invoice_log": "ข้าม — {path} ไม่เจอใบกำกับภาษีหรือใบเสร็จ",
    "income_skip_no_month_log": "ข้าม — {path} ไม่มีใบเดือน {month}/{year}",
    "income_insert_log": "สรุป — {shop}: {detail}",
    "income_insert_done": "insert เสร็จ {inserted}/{total}",
    "income_multi_bill_log": "สรุป — {name} สาขา {branch} มี {count} บิล",
    "menu_unavailable": "เมนูนี้ยังไม่พร้อมใช้",
    "back_to_menu": "กลับเมนู",
    "config_title": "ตั้งค่า",
    "choose_folder": "เลือก...",
    "save": "บันทึก",
    "start": "เริ่มทำงาน",
    "status_frame": "สถานะ",
    "copy_log": "คัดลอก log",
    "express_data_dir": "โฟลเดอร์ข้อมูล",
    "express_data_dir_hint": "โฟลเดอร์ที่รวมโฟลเดอร์ห้าง Express ไว้ด้วยกัน",
    "express_data_dir_empty": "ยังไม่ได้เลือกโฟลเดอร์ข้อมูล",
    "express_data_dir_invalid": "กรุณาเลือกโฟลเดอร์ข้อมูล Express",
    "express_data_dir_saved": "บันทึกแล้ว — พบ {count} ห้าง",
    "express_data_dir_none": "บันทึกแล้ว — ยังไม่พบโฟลเดอร์ห้างใน path นี้",
    "pp30_pdf_folder": "โฟลเดอร์ PDF",
    "pp30_pdf_summary_empty": "ยังไม่ได้เลือกโฟลเดอร์ PDF",
    "pp30_pdf_total": "พบ PDF {count} ไฟล์",
    "pp30_jv_date": "วันที่ JV",
    "pp30_jv_date_invalid": "กรุณากรอกวันที่ JV ให้ครบ เช่น 31/08/69",
    "pp30_jv_description": "รายละเอียด JV",
    "pp30_pv_description": "รายละเอียด PV",
    "pp30_run_mode": "รูปแบบ",
    "pp30_mode_normal": "แบบปกติ",
    "pp30_mode_special": "แบบพิเศษ",
    "pp30_mode_invalid": "กรุณาเลือกรูปแบบ แบบปกติ หรือ แบบพิเศษ",
    "pp30_welcome_log": "เลือกโฟลเดอร์ PDF แล้วกดเริ่ม — จะเทียบห้างจากไฟล์รายชื่อใน Config",
    "pp30_progress": "{done} / {total}  ({percent}%)",
    "pp30_shops_total": "พบห้างในไฟล์รายชื่อ {count} รายการ",
    "pp30_shops_none": "ไม่พบรายชื่อห้าง — บันทึก Config เพื่อสร้างไฟล์เทียบชื่อ",
    "pp30_pdf_name_missing": "อ่านชื่อห้างจาก PDF ไม่ได้ — {path}",
    "pp30_match_log": "ตรง — PDF: {pdf_name} → {shop_name}",
    "pp30_unmatched": "ไม่ตรง — PDF: {pdf_name} ({path})",
    "pp30_match_done": "เทียบชื่อเสร็จ {matched}/{total}",
    "pp30_kind_normal": "แบบปกติ",
    "pp30_kind_no_pay_normal": "ไม่จ่ายตัง — แบบปกติ",
    "pp30_kind_no_pay_new_shop": "ไม่จ่ายตัง — เปิดร้านใหม่",
    "pp30_kind_pay": "จ่ายตัง",
    "pp30_kind_penalty": "เสียค่าปรับ",
    "pp30_kind_skip_zero": "ข้าม — ยอดเป็น 0 ทั้งหมด",
    "pp30_kind_unknown": "ยังไม่เข้าเงื่อนไข",
    "pp30_kind_log": "เงื่อนไข: {kind}",
    "pp30_skip_mode_log": "ข้าม — เงื่อนไข {kind} ไม่ใช่โหมดที่เลือก",
    "pp30_skip_zero_log": "ข้าม — {name} ยอดเป็น 0",
    "pp30_skip_no_vat_lines_log": "ข้าม — {name} ไม่มีข้อ 5 และข้อ 7",
    "pp30_skip_date_exists_log": "ข้าม — {name} มีวันที่ {date} อยู่แล้ว",
    "pp30_values_missing": "อ่านยอดจาก PDF ไม่ได้ — {path}",
    "pp30_insert_log": "สรุป — {shop}: {kind} {detail}",
    "pp30_insert_done": "insert เสร็จ {inserted}/{total}",
}

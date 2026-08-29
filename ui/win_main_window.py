"""หน้าต่าง AutoKey บน Windows — ช่องกรอกเป็น Win32 EDIT ของระบบ"""

from __future__ import annotations

import ctypes
import queue
from ctypes import wintypes
from pathlib import Path

from constants.date_utils import default_work_date, format_express_pv_date, mask_express_pv_date
from constants.routes import TOPIC_PAYMENT_JOURNAL, UI_TEXT
from constants.version import __version__
from models.ka_tam_row import KaTamRow
from models.run_config import ExcelSheetSummary, RunConfig
from services.clipboard_service import copy_text
from services.automation_service import AutomationService
from services.excel_service import ExcelService
from services.hotkey_service import HotkeyService
from services.windows_file_dialog import pick_excel_path
from ui.app_icon import ico_icon_path

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_COMMAND = 0x0111
WM_SETFONT = 0x0030
WM_SETICON = 0x0080
WM_APP = 0x8000
WM_TIMER = 0x0113
EN_KILLFOCUS = 0x0100
EN_CHANGE = 0x0300
BN_CLICKED = 0
ICON_BIG = 1
SW_HIDE = 0
SW_RESTORE = 9
SW_SHOW = 5
MB_OK = 0x00000000
MB_YESNO = 0x00000004
MB_ICONWARNING = 0x00000030
MB_ICONERROR = 0x00000010
MB_ICONINFORMATION = 0x00000040
IDYES = 6
WS_CHILD = 0x40000000
WS_VISIBLE = 0x10000000
WS_TABSTOP = 0x00010000
WS_VSCROLL = 0x00200000
WS_BORDER = 0x00800000
ES_AUTOHSCROLL = 0x0080
ES_MULTILINE = 0x0004
ES_AUTOVSCROLL = 0x0040
ES_READONLY = 0x0800
ES_WANTRETURN = 0x1000
SS_LEFT = 0
BS_PUSHBUTTON = 0
BS_GROUPBOX = 0x00000007
HWND_TOP = wintypes.HWND(0)
HWND_TOPMOST = wintypes.HWND(-1)
HWND_NOTOPMOST = wintypes.HWND(-2)
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
EM_SETSEL = 0x00B1
EM_REPLACESEL = 0x00C2
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010

ID_EXCEL = 101
ID_BROWSE = 102
ID_SUMMARY = 103
ID_PV = 104
ID_START_NO = 105
ID_DESC = 106
ID_TAX = 107
ID_START = 108
ID_STOP = 109
ID_PROGRESS = 110
ID_COPY = 111
ID_LOG = 112
ID_SETTINGS_BOX = 201
ID_STATUS_BOX = 211

WIN_W = 560
WIN_H = 620

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]


_WINDOWS: dict[int, "MainWindow"] = {}


class MainWindow:
    def __init__(self) -> None:
        self.automation_service = AutomationService()
        ui_settings = self.automation_service.ui_settings
        self.hide_on_start = bool(ui_settings.get("hide_on_start", False))
        self.clear_log_on_start = bool(ui_settings.get("clear_log_on_start", True))
        raw_log_max = ui_settings.get("log_max_lines", 0)
        self.log_max_lines = max(0, int(raw_log_max if raw_log_max is not None else 0))
        self.verbose_log = bool(ui_settings.get("verbose_log", False))
        cancel_hotkeys = ui_settings.get("cancel_hotkeys") or ui_settings.get("cancel_hotkey", "esc")
        self.hotkey_service = HotkeyService(cancel_hotkeys)
        self.hotkey_label = self.hotkey_service.display_label
        self.is_running = False
        self._total_rows = 0
        self.sheet_summaries: list[ExcelSheetSummary] = []
        self.sheet_rows: dict[str, list[KaTamRow]] = {}
        self._queue: queue.Queue = queue.Queue()
        self._hwnd = wintypes.HWND()
        self._status_value = UI_TEXT["ready"]
        self._controls: dict[int, wintypes.HWND] = {}
        self._font = None
        self._masking_pv_date = False

        defaults = self.automation_service.default_settings
        self._initial_pv_date = format_express_pv_date(
            str(defaults.get("pv_date", "")).strip() or default_work_date()
        )
        self._initial_start_from_no = str(defaults.get("start_from_no", 1) or 1).strip() or "1"

        self._wndproc = WNDPROC(self._wnd_proc)
        ole32 = ctypes.WinDLL("ole32")
        ole32.OleInitialize.argtypes = [ctypes.c_void_p]
        ole32.OleInitialize.restype = ctypes.HRESULT
        ole32.OleInitialize(None)
        self._create_window()
        self._load_excel()

    def _create_window(self) -> None:
        hinstance = kernel32.GetModuleHandleW(None)
        class_name = "AutoKeyMainWindow"
        wndclass = WNDCLASSEXW()
        wndclass.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wndclass.lpfnWndProc = self._wndproc
        wndclass.hInstance = hinstance
        wndclass.hCursor = user32.LoadCursorW(None, 32512)
        wndclass.hbrBackground = 16
        wndclass.lpszClassName = class_name
        user32.RegisterClassExW(ctypes.byref(wndclass))

        style = 0x00CA0000
        hwnd = user32.CreateWindowExW(
            0,
            class_name,
            f"{UI_TEXT['app_title']} v{__version__}",
            style,
            200,
            120,
            WIN_W,
            WIN_H,
            None,
            None,
            hinstance,
            None,
        )
        self._hwnd = hwnd
        _WINDOWS[int(hwnd)] = self
        self._font = gdi32.CreateFontW(16, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 0, 0, "Tahoma")
        self._build_controls()
        self._set_icon()
        user32.ShowWindow(hwnd, SW_SHOW)
        user32.UpdateWindow(hwnd)

    def _ctrl(self, class_name: str, text: str, style: int, x: int, y: int, w: int, h: int, ctrl_id: int) -> wintypes.HWND:
        hwnd = user32.CreateWindowExW(
            0x00000200 if class_name == "EDIT" else 0,
            class_name,
            text,
            WS_CHILD | WS_VISIBLE | style,
            x,
            y,
            w,
            h,
            self._hwnd,
            ctrl_id,
            kernel32.GetModuleHandleW(None),
            None,
        )
        user32.SendMessageW(hwnd, WM_SETFONT, self._font, 1)
        self._controls[ctrl_id] = hwnd
        return hwnd

    def _build_controls(self) -> None:
        self._ctrl("STATIC", f"{UI_TEXT['app_title']} v{__version__}", SS_LEFT, 12, 10, 520, 22, 200)
        self._ctrl("STATIC", UI_TEXT["settings_frame"], SS_LEFT, 12, 36, 520, 20, ID_SETTINGS_BOX)
        self._ctrl("STATIC", UI_TEXT["excel_file"], SS_LEFT, 24, 62, 90, 20, 202)
        self._ctrl("EDIT", "", WS_TABSTOP | ES_AUTOHSCROLL, 120, 60, 280, 24, ID_EXCEL)
        self._ctrl("STATIC", UI_TEXT["excel_summary_empty"], SS_LEFT, 24, 88, 490, 32, ID_SUMMARY)
        self._ctrl("STATIC", UI_TEXT["pv_date"], SS_LEFT, 24, 124, 110, 20, 203)
        self._ctrl("EDIT", self._initial_pv_date, WS_TABSTOP | ES_AUTOHSCROLL, 140, 122, 140, 22, ID_PV)
        self._ctrl("STATIC", UI_TEXT["pv_date_hint"], SS_LEFT, 24, 148, 490, 28, 204)
        self._ctrl("STATIC", UI_TEXT["start_from_no"], SS_LEFT, 24, 180, 110, 20, 205)
        self._ctrl("EDIT", self._initial_start_from_no, WS_TABSTOP | ES_AUTOHSCROLL, 140, 178, 60, 22, ID_START_NO)
        self._ctrl("STATIC", UI_TEXT["start_from_no_hint"], SS_LEFT, 24, 204, 490, 28, 206)
        self._ctrl("STATIC", UI_TEXT["description"], SS_LEFT, 24, 236, 110, 20, 207)
        self._ctrl("EDIT", "", WS_TABSTOP | ES_AUTOHSCROLL, 140, 234, 370, 22, ID_DESC)
        self._ctrl("STATIC", UI_TEXT["description_hint"], SS_LEFT, 24, 258, 490, 28, 208)
        self._ctrl("STATIC", UI_TEXT["tax_payer_id"], SS_LEFT, 24, 290, 110, 20, 209)
        self._ctrl("EDIT", "", WS_TABSTOP | ES_AUTOHSCROLL, 140, 288, 370, 22, ID_TAX)
        self._ctrl("STATIC", UI_TEXT["tax_payer_id_hint"], SS_LEFT, 24, 312, 490, 28, 210)
        self._ctrl("BUTTON", f"▶ {UI_TEXT['start']}", WS_TABSTOP | BS_PUSHBUTTON, 12, 348, 140, 28, ID_START)
        self._ctrl(
            "BUTTON",
            f"■ {UI_TEXT['stop'].format(hotkey=self.hotkey_label)}",
            WS_TABSTOP | BS_PUSHBUTTON,
            160,
            348,
            180,
            28,
            ID_STOP,
        )
        self._ctrl("STATIC", UI_TEXT["status_frame"], SS_LEFT, 12, 386, 200, 20, ID_STATUS_BOX)
        self._ctrl("STATIC", "0 / 0", SS_LEFT, 24, 410, 200, 20, ID_PROGRESS)
        self._ctrl("BUTTON", UI_TEXT["copy_log"], WS_TABSTOP | BS_PUSHBUTTON, 412, 406, 100, 24, ID_COPY)
        log_style = WS_TABSTOP | WS_VSCROLL | ES_MULTILINE | ES_AUTOVSCROLL | ES_READONLY | ES_WANTRETURN
        self._ctrl("EDIT", "", log_style, 24, 434, 492, 128, ID_LOG)
        self._write_log(UI_TEXT["welcome_log"] + "\n", trim=False)
        self._ctrl("BUTTON", UI_TEXT["choose_file"], WS_TABSTOP | BS_PUSHBUTTON, 412, 58, 120, 28, ID_BROWSE)

    def _set_icon(self) -> None:
        ico = ico_icon_path()
        if not ico.exists():
            return
        handle = user32.LoadImageW(None, str(ico), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
        if handle:
            user32.SendMessageW(self._hwnd, WM_SETICON, ICON_BIG, handle)

    def _text(self, ctrl_id: int) -> str:
        hwnd = self._controls[ctrl_id]
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value

    def _set_text(self, ctrl_id: int, text: str) -> None:
        user32.SetWindowTextW(self._controls[ctrl_id], text)

    def _mask_pv_date(self) -> None:
        if self._masking_pv_date:
            return
        raw = self._text(ID_PV)
        masked = mask_express_pv_date(raw)
        if masked == raw:
            return
        self._masking_pv_date = True
        self._set_text(ID_PV, masked)
        hwnd = self._controls[ID_PV]
        user32.SendMessageW(hwnd, EM_SETSEL, len(masked), len(masked))
        self._masking_pv_date = False

    def _format_pv_date(self) -> None:
        formatted = format_express_pv_date(self._text(ID_PV))
        if not formatted or formatted == self._text(ID_PV):
            return
        self._masking_pv_date = True
        self._set_text(ID_PV, formatted)
        self._masking_pv_date = False

    def _wnd_proc(self, hwnd, message, wparam, lparam) -> int:
        if message == WM_COMMAND:
            notify = (wparam >> 16) & 0xFFFF
            ctrl_id = wparam & 0xFFFF
            if ctrl_id == ID_BROWSE:
                self._choose_excel()
            elif notify == BN_CLICKED:
                if ctrl_id == ID_START:
                    self._start()
                elif ctrl_id == ID_STOP:
                    self._stop()
                elif ctrl_id == ID_COPY:
                    self._copy_all_log()
            elif ctrl_id == ID_PV:
                if notify == EN_CHANGE:
                    self._mask_pv_date()
                elif notify == EN_KILLFOCUS:
                    self._format_pv_date()
        elif message == WM_APP:
            self._drain_queue()
        elif message == WM_TIMER and wparam == 1:
            user32.KillTimer(hwnd, 1)
            user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        elif message == WM_CLOSE:
            self._on_close()
            return 0
        elif message == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, message, wparam, lparam)

    def _on_close(self) -> None:
        if self.is_running:
            self._stop()
        self.hotkey_service.stop_listening()
        user32.DestroyWindow(self._hwnd)

    def _call_main(self, fn) -> None:
        self._queue.put(fn)
        if self._hwnd:
            user32.PostMessageW(self._hwnd, WM_APP, 0, 0)

    def _drain_queue(self) -> None:
        while True:
            try:
                fn = self._queue.get_nowait()
            except queue.Empty:
                return
            fn()

    def _load_excel(self) -> None:
        raw_path = self._text(ID_EXCEL).strip()
        if not raw_path:
            self.sheet_summaries = []
            self.sheet_rows = {}
            self._set_text(ID_SUMMARY, UI_TEXT["excel_summary_empty"])
            return
        excel_path = Path(raw_path).expanduser()
        if not excel_path.exists():
            self.sheet_summaries = []
            self.sheet_rows = {}
            self._set_text(ID_SUMMARY, UI_TEXT["excel_summary_empty"])
            return
        try:
            self.sheet_summaries, self.sheet_rows = ExcelService.load_workbook(excel_path)
        except Exception as exc:
            self.sheet_summaries = []
            self.sheet_rows = {}
            self._set_text(ID_SUMMARY, str(exc))
            return
        if not self.sheet_summaries:
            self._set_text(ID_SUMMARY, UI_TEXT["no_excel_data"])
            self._append_log(UI_TEXT["no_excel_data"])
            return
        total_rows = sum(summary.row_count for summary in self.sheet_summaries)
        self._set_text(ID_SUMMARY, UI_TEXT["excel_total"].format(rows=total_rows))
        self._append_log(UI_TEXT["excel_loaded"].format(path=excel_path.name))
        self._append_log(UI_TEXT["excel_total"].format(rows=total_rows))

    def _parse_start_from_no(self) -> int:
        raw = self._text(ID_START_NO).strip()
        if not raw:
            return 1
        try:
            return int(raw)
        except ValueError:
            return 0

    def _choose_excel(self) -> None:
        self._append_log("เปิดหน้าต่างเลือกไฟล์...")
        try:
            path = pick_excel_path(self._hwnd)
        except Exception as exc:
            user32.MessageBoxW(self._hwnd, str(exc), "AutoKey", MB_OK | MB_ICONERROR)
            return
        if not path:
            return
        self._set_text(ID_EXCEL, path)
        self._load_excel()

    def _start(self) -> None:
        if self.is_running:
            return
        if not self.sheet_summaries:
            self._load_excel()
        if not self.sheet_summaries:
            user32.MessageBoxW(self._hwnd, UI_TEXT["no_excel_loaded"], "AutoKey", MB_OK | MB_ICONWARNING)
            return
        run_config = RunConfig(
            topic=TOPIC_PAYMENT_JOURNAL,
            excel_path=Path(self._text(ID_EXCEL)).expanduser(),
            pv_date=format_express_pv_date(self._text(ID_PV).strip()),
            description=self._text(ID_DESC).strip(),
            tax_payer_id=self._text(ID_TAX).strip(),
            start_from_no=self._parse_start_from_no(),
            sheet_summaries=self.sheet_summaries,
            sheet_rows=self.sheet_rows,
        )
        if run_config.pv_date:
            self._masking_pv_date = True
            self._set_text(ID_PV, run_config.pv_date)
            self._masking_pv_date = False
        errors = run_config.validate()
        if errors:
            user32.MessageBoxW(self._hwnd, "\n".join(errors), "AutoKey", MB_OK | MB_ICONWARNING)
            return
        confirm_rows = run_config.planned_row_count()
        start_label = f"เริ่มที่ No. {run_config.start_from_no}"
        msg = f"{UI_TEXT['confirm_message']}\n\n{start_label} — จะทำ {confirm_rows} รายการ"
        if user32.MessageBoxW(self._hwnd, msg, UI_TEXT["confirm_title"], MB_YESNO | MB_ICONWARNING) != IDYES:
            return
        self.is_running = True
        self._total_rows = confirm_rows
        if self.clear_log_on_start:
            self._clear_log()
        self._append_log(UI_TEXT["cancel_hotkey_hint"].format(hotkey=self.hotkey_label))
        self.hotkey_service.start_listening(self._stop)
        if self.hide_on_start:
            user32.ShowWindow(self._hwnd, SW_HIDE)
        self.automation_service.run_async(
            run_config=run_config,
            on_status=self._set_status,
            on_progress=self._set_progress,
            on_step=self._set_step,
            on_finished=self._on_finished,
            verbose_log=self.verbose_log,
        )

    def _stop(self) -> None:
        if not self.is_running:
            return
        self.automation_service.request_stop()
        self._append_log(UI_TEXT["stop_requested"])

    def _restore_window(self) -> None:
        if self.hide_on_start:
            user32.ShowWindow(self._hwnd, SW_RESTORE)
            user32.SetWindowPos(self._hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            user32.SetTimer(self._hwnd, 1, 200, None)
            user32.SetForegroundWindow(self._hwnd)
            self._append_log(UI_TEXT["window_restored"])

    def _cleanup_run(self) -> None:
        self.is_running = False
        self.hotkey_service.stop_listening()

    def _set_status(self, message: str) -> None:
        self._call_main(lambda: self._append_log(message))

    def _set_progress(self, current: int, total: int) -> None:
        progress = f"{current} / {total}"
        self._call_main(lambda: self._set_text(ID_PROGRESS, progress))

    def _set_step(self, step_index: int, step_label: str, detail: str) -> None:
        del step_index, step_label, detail

    def _on_finished(self, success: bool, message: str) -> None:
        def update() -> None:
            self._cleanup_run()
            self._restore_window()
            self._status_value = message
            self._append_log(message, trim=success)
            icon = MB_ICONINFORMATION if success else MB_ICONERROR
            title = "AutoKey" if success else "AutoKey — หยุดทำงาน"
            user32.MessageBoxW(self._hwnd, message, title, MB_OK | icon)

        self._call_main(update)

    def _write_log(self, text: str, *, trim: bool = True) -> None:
        current = self._text(ID_LOG)
        current += text
        if trim and not self.is_running and self.log_max_lines > 0:
            lines = current.splitlines(keepends=True)
            if len(lines) > self.log_max_lines:
                current = "".join(lines[-self.log_max_lines:])
        user32.SetWindowTextW(self._controls[ID_LOG], current)
        length = user32.GetWindowTextLengthW(self._controls[ID_LOG])
        user32.SendMessageW(self._controls[ID_LOG], EM_SETSEL, length, length)

    def _append_log(self, message: str, *, trim: bool = True) -> None:
        self._write_log(message + "\n", trim=trim)
        self._status_value = message

    def _clear_log(self) -> None:
        user32.SetWindowTextW(self._controls[ID_LOG], "")

    def _copy_all_log(self) -> None:
        text = self._text(ID_LOG)
        if text.strip():
            copy_text(text)

    def run(self) -> None:
        msg = MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

"""หน้าต่าง AutoKey บน macOS — ช่องกรอกเป็น NSTextField ของระบบ"""

from __future__ import annotations

from pathlib import Path

from AppKit import (  # type: ignore
    NSAlert,
    NSApp,
    NSApplication,
    NSApplicationActivationPolicyRegular,
    NSBezelStyleRounded,
    NSBox,
    NSButton,
    NSColor,
    NSEvent,
    NSEventModifierFlagCommand,
    NSEventModifierFlagControl,
    NSFont,
    NSImage,
    NSKeyDownMask,
    NSMakeRect,
    NSMenu,
    NSMenuItem,
    NSOpenPanel,
    NSPasteboard,
    NSPasteboardTypeString,
    NSScrollView,
    NSTextField,
    NSTextView,
    NSView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSObject, NSOperationQueue  # type: ignore
import objc
from PyObjCTools import AppHelper  # type: ignore

from constants.date_utils import (
    PV_DATE_EXAMPLE,
    default_work_date,
    format_express_pv_date,
    mask_express_pv_date,
)
from constants.routes import EXCEL_OPEN_EXTENSIONS, TOPIC_PAYMENT_JOURNAL, UI_TEXT
from constants.version import __version__
from models.ka_tam_row import KaTamRow
from models.run_config import ExcelSheetSummary, RunConfig
from services.automation_service import AutomationService
from services.clipboard_service import normalize_pasted_cell
from services.excel_service import ExcelService
from services.hotkey_service import HotkeyService
from ui.app_icon import icon_dir

WIN_W = 560
WIN_H = 640


class FlippedView(NSView):
    def isFlipped(self) -> bool:
        return True


class MainNSWindow(NSWindow):
    def performKeyEquivalent_(self, event) -> bool:
        flags = int(event.modifierFlags())
        if flags & int(NSEventModifierFlagCommand):
            chars = str(event.charactersIgnoringModifiers() or "").lower()
            responder = self.firstResponder()
            method = {"v": "paste_", "c": "copy_", "x": "cut_", "a": "selectAll_"}.get(chars)
            if method and responder is not None and hasattr(responder, method):
                getattr(responder, method)(None)
                if method == "paste_" and responder.respondsToSelector_("isEditable") and responder.isEditable():
                    raw = str(responder.string() or "")
                    cleaned = normalize_pasted_cell(raw)
                    if cleaned != raw:
                        responder.setString_(cleaned)
                        responder.setSelectedRange_((len(cleaned), 0))
                return True
        return objc.super(MainNSWindow, self).performKeyEquivalent_(event)


class _CallbackTarget(NSObject):
    def invoke_(self, _sender) -> None:
        callback = getattr(self, "_callback", None)
        if callback is not None:
            callback()


class _WindowDelegate(NSObject):
    def windowShouldClose_(self, _sender) -> bool:
        owner = getattr(self, "_owner", None)
        if owner is not None:
            owner._on_close()
        return True


class _DateFieldDelegate(NSObject):
    def controlTextDidChange_(self, notification) -> None:
        field = notification.object()
        raw = str(field.stringValue() or "")
        masked = mask_express_pv_date(raw)
        if masked == raw:
            return
        field.setStringValue_(masked)
        editor = field.currentEditor()
        if editor is not None:
            editor.setSelectedRange_((len(masked), 0))

    def controlTextDidEndEditing_(self, notification) -> None:
        field = notification.object()
        formatted = format_express_pv_date(str(field.stringValue() or ""))
        if formatted:
            field.setStringValue_(formatted)


class _PlainFieldDelegate(NSObject):
    """ช่องบรรทัดเดียว — ตัด CR/LF ที่ Excel ก๊อปเซลล์มาด้วย"""

    def controlTextDidChange_(self, notification) -> None:
        field = notification.object()
        raw = str(field.stringValue() or "")
        cleaned = normalize_pasted_cell(raw)
        if cleaned == raw:
            return
        field.setStringValue_(cleaned)
        editor = field.currentEditor()
        if editor is not None:
            editor.setSelectedRange_((len(cleaned), 0))


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
        self._targets: list[_CallbackTarget] = []
        self._key_monitor = None
        self._status_value = UI_TEXT["ready"]

        defaults = self.automation_service.default_settings
        initial_pv_date = format_express_pv_date(
            str(defaults.get("pv_date", "")).strip() or default_work_date()
        )
        initial_start_from_no = str(defaults.get("start_from_no", 1) or 1).strip() or "1"

        self._app = NSApplication.sharedApplication()
        self._app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        _install_standard_edit_menu()
        self._set_app_icon()
        self._build_window(initial_pv_date, initial_start_from_no)
        self._bind_shortcuts()
        self._load_excel()

    def _keep(self, callback) -> _CallbackTarget:
        target = _CallbackTarget.alloc().init()
        target._callback = callback
        self._targets.append(target)
        return target

    def _set_app_icon(self) -> None:
        png = icon_dir() / "app_icon.png"
        if not png.exists():
            return
        image = NSImage.alloc().initWithContentsOfFile_(str(png))
        if image is not None:
            self._app.setApplicationIconImage_(image)

    def _build_window(self, initial_pv_date: str, initial_start_from_no: str) -> None:
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable
        self.window = MainNSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, WIN_W, WIN_H),
            style,
            2,
            False,
        )
        self.window.setTitle_(f"{UI_TEXT['app_title']} v{__version__}")
        self.window.center()
        delegate = _WindowDelegate.alloc().init()
        delegate._owner = self
        self.window.setDelegate_(delegate)
        self._window_delegate = delegate

        root = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, WIN_H))
        self.window.setContentView_(root)
        self._root = root

        y = 12
        title = _static_label(root, f"{UI_TEXT['app_title']} v{__version__}", 16, y, WIN_W - 32, 22, size=15, bold=True)
        y = 42

        settings_box, settings = _box(root, UI_TEXT["settings_frame"], 12, y, WIN_W - 24, 310)
        sy = 8
        _static_label(settings, UI_TEXT["excel_file"], 8, sy, 90, 18)
        self.excel_path_field = _edit_field(settings, 100, sy, 280)
        choose = _button(settings, UI_TEXT["choose_file"], 386, sy - 2, 90, 24, self._keep(self._choose_excel))
        self._plain_delegate = _PlainFieldDelegate.alloc().init()
        self.excel_path_field.setDelegate_(self._plain_delegate)
        sy += 26
        self.excel_summary_field = _static_label(settings, UI_TEXT["excel_summary_empty"], 8, sy, 500, 32, size=11, gray=True)
        self.excel_summary_field.setUsesSingleLineMode_(False)
        sy += 34
        _static_label(settings, UI_TEXT["pv_date"], 8, sy, 110, 18)
        self.pv_date_field = _edit_field(settings, 120, sy, 160)
        self.pv_date_field.setStringValue_(initial_pv_date)
        self.pv_date_field.setPlaceholderString_(PV_DATE_EXAMPLE)
        date_delegate = _DateFieldDelegate.alloc().init()
        self.pv_date_field.setDelegate_(date_delegate)
        self._date_delegate = date_delegate
        sy += 22
        _static_label(settings, UI_TEXT["pv_date_hint"], 8, sy, 500, 28, size=11, gray=True)
        sy += 32
        _static_label(settings, UI_TEXT["start_from_no"], 8, sy, 110, 18)
        self.start_from_no_field = _edit_field(settings, 120, sy, 80)
        self.start_from_no_field.setStringValue_(initial_start_from_no)
        self.start_from_no_field.setDelegate_(self._plain_delegate)
        sy += 22
        _static_label(settings, UI_TEXT["start_from_no_hint"], 8, sy, 500, 28, size=11, gray=True)
        sy += 32
        _static_label(settings, UI_TEXT["description"], 8, sy, 110, 18)
        self.description_field = _edit_field(settings, 120, sy, 356)
        self.description_field.setDelegate_(self._plain_delegate)
        sy += 26
        _static_label(settings, UI_TEXT["description_hint"], 8, sy, 500, 28, size=11, gray=True)
        sy += 32
        _static_label(settings, UI_TEXT["tax_payer_id"], 8, sy, 110, 18)
        self.tax_payer_id_field = _edit_field(settings, 120, sy, 356)
        self.tax_payer_id_field.setDelegate_(self._plain_delegate)
        sy += 22
        _static_label(settings, UI_TEXT["tax_payer_id_hint"], 8, sy, 500, 28, size=11, gray=True)

        y = 360
        start_btn = _button(
            root,
            f"▶ {UI_TEXT['start']}",
            16,
            y,
            140,
            28,
            self._keep(self._start),
        )
        self.stop_button = _button(
            root,
            f"■ {UI_TEXT['stop'].format(hotkey=self.hotkey_label)}",
            164,
            y,
            180,
            28,
            self._keep(self._stop),
        )

        y = 396
        status_box, status = _box(root, UI_TEXT["status_frame"], 12, y, WIN_W - 24, WIN_H - y - 12)
        self.progress_field = _static_label(status, "0 / 0", 8, 6, 300, 18)
        copy_btn = _button(status, UI_TEXT["copy_log"], 380, 4, 110, 24, self._keep(self._copy_all_log))
        self.log_view = _log_view(status, 8, 32, WIN_W - 56, WIN_H - y - 56)
        self._write_log(UI_TEXT["welcome_log"] + "\n", trim=False)
        del title, choose, start_btn, copy_btn

        self.window.makeKeyAndOrderFront_(None)
        self.window.makeFirstResponder_(self.description_field)

    def _bind_shortcuts(self) -> None:
        def monitor(event):
            flags = int(event.modifierFlags())
            if flags & NSEventModifierFlagCommand:
                return event
            keycode = event.keyCode()
            if keycode == 53:
                self._stop()
            elif keycode == 101 and flags & NSEventModifierFlagControl:
                self._stop()
            return event

        self._key_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, monitor)

    def _on_close(self) -> None:
        if self.is_running:
            self._stop()
        self.hotkey_service.stop_listening()
        NSApp.terminate_(None)

    def _field_text(self, field: NSTextField) -> str:
        return normalize_pasted_cell(str(field.stringValue() or "")).strip()

    def _load_excel(self) -> None:
        raw_path = self._field_text(self.excel_path_field)
        if not raw_path:
            self.sheet_summaries = []
            self.sheet_rows = {}
            self.excel_summary_field.setStringValue_(UI_TEXT["excel_summary_empty"])
            return

        excel_path = Path(raw_path).expanduser()
        if not excel_path.exists():
            self.sheet_summaries = []
            self.sheet_rows = {}
            self.excel_summary_field.setStringValue_(UI_TEXT["excel_summary_empty"])
            return

        try:
            self.sheet_summaries, self.sheet_rows = ExcelService.load_workbook(excel_path)
        except Exception as exc:
            self.sheet_summaries = []
            self.sheet_rows = {}
            self.excel_summary_field.setStringValue_(str(exc))
            return

        if not self.sheet_summaries:
            self.excel_summary_field.setStringValue_(UI_TEXT["no_excel_data"])
            self._append_log(UI_TEXT["no_excel_data"])
            return

        total_rows = sum(summary.row_count for summary in self.sheet_summaries)
        self.excel_summary_field.setStringValue_(UI_TEXT["excel_total"].format(rows=total_rows))
        self._append_log(UI_TEXT["excel_loaded"].format(path=excel_path.name))
        self._append_log(UI_TEXT["excel_total"].format(rows=total_rows))

    def _parse_start_from_no(self) -> int:
        raw = self._field_text(self.start_from_no_field)
        if not raw:
            return 1
        try:
            return int(raw)
        except ValueError:
            return 0

    def _choose_excel(self) -> None:
        panel = NSOpenPanel.openPanel()
        panel.setAllowedFileTypes_(list(EXCEL_OPEN_EXTENSIONS))
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        if panel.runModal() != 1:
            return
        urls = panel.URLs()
        if not urls:
            return
        self.excel_path_field.setStringValue_(str(urls[0].path()))
        self._load_excel()

    def _start(self) -> None:
        if self.is_running:
            return
        if not self.sheet_summaries:
            self._load_excel()
        if not self.sheet_summaries:
            _alert("AutoKey", UI_TEXT["no_excel_loaded"])
            return

        run_config = RunConfig(
            topic=TOPIC_PAYMENT_JOURNAL,
            excel_path=Path(self._field_text(self.excel_path_field)).expanduser(),
            pv_date=format_express_pv_date(self._field_text(self.pv_date_field)),
            description=self._field_text(self.description_field),
            tax_payer_id=self._field_text(self.tax_payer_id_field),
            start_from_no=self._parse_start_from_no(),
            sheet_summaries=self.sheet_summaries,
            sheet_rows=self.sheet_rows,
        )
        if run_config.pv_date:
            self.pv_date_field.setStringValue_(run_config.pv_date)
        errors = run_config.validate()
        if errors:
            _alert("AutoKey", "\n".join(errors))
            return

        confirm_rows = run_config.planned_row_count()
        start_label = f"เริ่มที่ No. {run_config.start_from_no}"
        if not _confirm(UI_TEXT["confirm_title"], f"{UI_TEXT['confirm_message']}\n\n{start_label} — จะทำ {confirm_rows} รายการ"):
            return

        self.is_running = True
        self._total_rows = confirm_rows
        if self.clear_log_on_start:
            self._clear_log()
        self._append_log(UI_TEXT["cancel_hotkey_hint"].format(hotkey=self.hotkey_label))
        self.hotkey_service.start_listening(self._stop)
        if self.hide_on_start:
            self.window.orderOut_(None)

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
            self.window.makeKeyAndOrderFront_(None)
            NSApp.activateIgnoringOtherApps_(True)
            self._append_log(UI_TEXT["window_restored"])
        self.log_view.scrollRangeToVisible_((len(self.log_view.string()), 0))

    def _cleanup_run(self) -> None:
        self.is_running = False
        self.hotkey_service.stop_listening()

    def _call_main(self, fn) -> None:
        NSOperationQueue.mainQueue().addOperationWithBlock_(fn)

    def _set_status(self, message: str) -> None:
        self._call_main(lambda: self._append_log(message))

    def _set_progress(self, current: int, total: int) -> None:
        progress = f"{current} / {total}"
        self._call_main(lambda: self.progress_field.setStringValue_(progress))

    def _set_step(self, step_index: int, step_label: str, detail: str) -> None:
        del step_index, step_label, detail

    def _on_finished(self, success: bool, message: str) -> None:
        def update() -> None:
            self._cleanup_run()
            self._restore_window()
            self._status_value = message
            self._append_log(message, trim=success)
            if success:
                _alert("AutoKey", message)
            else:
                _alert("AutoKey — หยุดทำงาน", message)

        self._call_main(update)

    def _write_log(self, text: str, *, trim: bool = True) -> None:
        current = str(self.log_view.string() or "")
        current += text
        if trim:
            current = _trim_log_text(current, self.log_max_lines, self.is_running)
        self.log_view.setString_(current)
        self.log_view.scrollRangeToVisible_((len(current), 0))

    def _append_log(self, message: str, *, trim: bool = True) -> None:
        self._write_log(message + "\n", trim=trim)
        self._status_value = message

    def _clear_log(self) -> None:
        self.log_view.setString_("")

    def _copy_all_log(self) -> None:
        text = str(self.log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)

    def run(self) -> None:
        NSApp.activateIgnoringOtherApps_(True)
        AppHelper.runEventLoop()


def _install_standard_edit_menu() -> None:
    """เมนู Edit ของระบบ — ส่ง cut:/copy:/paste:/selectAll: ไป first responder"""
    menubar = NSMenu.alloc().init()
    app_item = NSMenuItem.alloc().init()
    menubar.addItem_(app_item)
    app_item.setSubmenu_(NSMenu.alloc().init())

    edit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Edit", None, "")
    menubar.addItem_(edit_item)
    edit = NSMenu.alloc().initWithTitle_("Edit")
    edit.addItemWithTitle_action_keyEquivalent_("Cut", "cut:", "x")
    edit.addItemWithTitle_action_keyEquivalent_("Copy", "copy:", "c")
    edit.addItemWithTitle_action_keyEquivalent_("Paste", "paste:", "v")
    edit.addItem_(NSMenuItem.separatorItem())
    edit.addItemWithTitle_action_keyEquivalent_("Select All", "selectAll:", "a")
    edit_item.setSubmenu_(edit)
    NSApp.setMainMenu_(menubar)


def _static_label(parent, text: str, x, y, w, h, *, size: float = 13, gray: bool = False, bold: bool = False):
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    field.setStringValue_(text)
    field.setEditable_(False)
    field.setBezeled_(False)
    field.setDrawsBackground_(False)
    field.setSelectable_(False)
    font = NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size)
    field.setFont_(font)
    if gray:
        field.setTextColor_(NSColor.secondaryLabelColor())
    parent.addSubview_(field)
    return field


def _edit_field(parent, x, y, w, h: float = 22):
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    field.setEditable_(True)
    field.setSelectable_(True)
    field.setBezeled_(True)
    field.setDrawsBackground_(True)
    field.setFont_(NSFont.systemFontOfSize_(13))
    parent.addSubview_(field)
    return field


def _button(parent, title: str, x, y, w, h, target: _CallbackTarget):
    button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    button.setBezelStyle_(NSBezelStyleRounded)
    button.setTitle_(title)
    button.setTarget_(target)
    button.setAction_("invoke:")
    parent.addSubview_(button)
    return button


def _box(parent, title: str, x, y, w, h):
    box = NSBox.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    box.setTitle_(title)
    parent.addSubview_(box)
    content = box.contentView()
    inner = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, max(w - 16, 80), max(h - 26, 80)))
    inner.setAutoresizingMask_(18)
    content.addSubview_(inner)
    return box, inner


def _log_view(parent, x, y, w, h) -> NSTextView:
    scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    scroll.setHasVerticalScroller_(True)
    scroll.setAutohidesScrollers_(True)
    view = NSTextView.alloc().initWithFrame_(scroll.contentView().bounds())
    view.setEditable_(False)
    view.setSelectable_(True)
    view.setFont_(NSFont.userFixedPitchFontOfSize_(11))
    view.setMinSize_((0, h))
    view.setMaxSize_((1_000_000, 1_000_000))
    view.setVerticallyResizable_(True)
    view.setHorizontallyResizable_(False)
    view.textContainer().setWidthTracksTextView_(True)
    scroll.setDocumentView_(view)
    parent.addSubview_(scroll)
    return view


def _alert(title: str, message: str) -> None:
    alert = NSAlert.alloc().init()
    alert.setMessageText_(title)
    alert.setInformativeText_(message)
    alert.addButtonWithTitle_("ตกลง")
    alert.runModal()


def _confirm(title: str, message: str) -> bool:
    alert = NSAlert.alloc().init()
    alert.setMessageText_(title)
    alert.setInformativeText_(message)
    alert.addButtonWithTitle_("ใช่")
    alert.addButtonWithTitle_("ไม่")
    return alert.runModal() == 1000


def _trim_log_text(text: str, log_max_lines: int, is_running: bool) -> str:
    if is_running or log_max_lines <= 0:
        return text
    lines = text.splitlines(keepends=True)
    if len(lines) <= log_max_lines:
        return text
    return "".join(lines[-log_max_lines:])

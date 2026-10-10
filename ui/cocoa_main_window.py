"""หน้าต่าง AutoKey บน macOS — เมนูใหญ่"""

from __future__ import annotations

from pathlib import Path
import threading

from AppKit import (  # type: ignore
    NSAlert,
    NSApp,
    NSApplication,
    NSApplicationActivationPolicyRegular,
    NSBezelStyleRegularSquare,
    NSBezelStyleRounded,
    NSBox,
    NSButton,
    NSButtonTypeRadio,
    NSColor,
    NSFont,
    NSImage,
    NSMakeRect,
    NSOpenPanel,
    NSPasteboard,
    NSPasteboardTypeString,
    NSProgressIndicator,
    NSProgressIndicatorStyleBar,
    NSScrollView,
    NSTextField,
    NSTextView,
    NSView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSObject  # type: ignore
from PyObjCTools import AppHelper  # type: ignore

from constants.date_utils import PV_DATE_EXAMPLE, format_express_pv_date, is_complete_express_date
from constants.routes import (
    MENU_BUTTON_HEIGHT,
    PAGE_CONFIG,
    PAGE_INCOME,
    PAGE_KA_TAM,
    PAGE_MENU,
    PAGE_PND1,
    PAGE_BT40,
    PAGE_PND2,
    PAGE_PND3,
    PAGE_PND30,
    PAGE_PP30,
    PAGE_SSO,
    PAGE_WCF,
    PAGE_PAYROLL,
    INCOME_LOCK_NONE,
    INCOME_LOCK_PASSWORD,
    PERIOD_EXAMPLE,
    PP30_MODE_NORMAL,
    PP30_MODE_SPECIAL,
    UI_TEXT,
)
from constants.topic_menu import TOPIC_MENU_ITEMS
from constants.version import __version__
from models.app_config import AppConfig
from models.income_form_config import IncomeFormConfig
from models.income_lock_mode import IncomeLockMode
from models.ka_tam_form_config import KaTamFormConfig
from models.month_year_period import MonthYearPeriod
from models.pnd1_form_config import Pnd1FormConfig
from models.bt40_form_config import Bt40FormConfig
from models.pnd2_form_config import Pnd2FormConfig
from models.pnd3_form_config import Pnd3FormConfig
from models.pnd30_form_config import Pnd30FormConfig
from models.pp30_form_config import Pp30FormConfig
from models.sso_form_config import SsoFormConfig
from models.wcf_form_config import WcfFormConfig
from models.payroll_form_config import PayrollFormConfig
from models.pp30_run_mode import Pp30RunMode
from models.topic_menu_item import TopicMenuItem
from services.app_config_service import AppConfigService
from services.express_shop_index_service import ExpressShopIndexService
from services.ka_tam_excel_service import KaTamExcelService
from services.income_match_run_service import IncomeMatchRunService
from services.ka_tam_match_run_service import KaTamMatchRunService
from services.pnd1_match_run_service import Pnd1MatchRunService
from services.bt40_match_run_service import Bt40MatchRunService
from services.pnd2_match_run_service import Pnd2MatchRunService
from services.pnd3_match_run_service import Pnd3MatchRunService
from services.pnd30_match_run_service import Pnd30MatchRunService
from services.pp30_folder_service import Pp30FolderService
from services.pp30_match_run_service import Pp30MatchRunService
from services.sso_match_run_service import SsoMatchRunService
from services.wcf_excel_service import WcfExcelService
from services.wcf_match_run_service import WcfMatchRunService
from services.payroll_excel_service import PayrollExcelService
from services.payroll_match_run_service import PayrollMatchRunService
from ui.app_icon import icon_dir

WIN_W = 560
MENU_WIN_H = 740
CONFIG_WIN_H = 360
PP30_WIN_H = 680
KA_TAM_WIN_H = 680
PND30_WIN_H = 620
PND3_WIN_H = 620
PND1_WIN_H = 620
PND2_WIN_H = 620
BT40_WIN_H = 660
SSO_WIN_H = 620
WCF_WIN_H = 580
PAYROLL_WIN_H = 660
INCOME_WIN_H = 684


class FlippedView(NSView):
    def isFlipped(self) -> bool:
        return True


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
    def controlTextDidEndEditing_(self, notification) -> None:
        field = notification.object()
        raw = str(field.stringValue() or "")
        if is_complete_express_date(raw):
            field.setStringValue_(format_express_pv_date(raw))


class _PeriodFieldDelegate(NSObject):
    def controlTextDidChange_(self, notification) -> None:
        field = notification.object()
        current = str(field.stringValue() or "")
        masked = MonthYearPeriod.mask(current)
        if masked != current:
            field.setStringValue_(masked)


class MainWindow:
    def __init__(self) -> None:
        self._targets: list[_CallbackTarget] = []
        self._current_page = PAGE_MENU
        self.app_config_service = AppConfigService()
        self.app_config = self.app_config_service.load()
        self.pp30_pdf_files: list[Path] = []
        self._pp30_mode = Pp30RunMode.normal()
        self._pp30_running = False
        self.ka_tam_rows_count = 0
        self._ka_tam_running = False
        self.pnd30_pdf_files: list[Path] = []
        self._pnd30_running = False
        self.pnd3_pdf_files: list[Path] = []
        self._pnd3_running = False
        self.pnd1_pdf_files: list[Path] = []
        self._pnd1_running = False
        self.pnd2_pdf_files: list[Path] = []
        self._pnd2_running = False
        self.bt40_pdf_files: list[Path] = []
        self._bt40_running = False
        self.sso_pdf_files: list[Path] = []
        self._sso_running = False
        self.wcf_rows_count = 0
        self._wcf_running = False
        self.payroll_rows_count = 0
        self._payroll_running = False
        self.income_pdf_files: list[Path] = []
        self._income_running = False
        self._period_delegate = _PeriodFieldDelegate.alloc().init()

        self._app = NSApplication.sharedApplication()
        self._app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        self._set_app_icon()
        self._build_window()
        self._show_page(PAGE_MENU)

    def _keep(self, callback) -> _CallbackTarget:
        target = _CallbackTarget.alloc().init()
        target._callback = callback
        self._targets.append(target)
        return target

    def _period_field(self, parent, x, y):
        field = _edit_field(parent, x, y, 120)
        field.setPlaceholderString_(PERIOD_EXAMPLE)
        field.setDelegate_(self._period_delegate)
        return field

    def _set_app_icon(self) -> None:
        png = icon_dir() / "app_icon.png"
        if not png.exists():
            return
        image = NSImage.alloc().initWithContentsOfFile_(str(png))
        if image is not None:
            self._app.setApplicationIconImage_(image)

    def _build_window(self) -> None:
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, WIN_W, MENU_WIN_H),
            style,
            2,
            False,
        )
        self.window.center()
        delegate = _WindowDelegate.alloc().init()
        delegate._owner = self
        self.window.setDelegate_(delegate)
        self._window_delegate = delegate

        root = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, MENU_WIN_H))
        self.window.setContentView_(root)
        self._root = root
        self._menu_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, MENU_WIN_H))
        self._config_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, CONFIG_WIN_H))
        self._pp30_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, PP30_WIN_H))
        self._ka_tam_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, KA_TAM_WIN_H))
        self._pnd30_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, PND30_WIN_H))
        self._pnd3_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, PND3_WIN_H))
        self._pnd1_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, PND1_WIN_H))
        self._pnd2_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, PND2_WIN_H))
        self._bt40_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, BT40_WIN_H))
        self._sso_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, SSO_WIN_H))
        self._wcf_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, WCF_WIN_H))
        self._payroll_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, PAYROLL_WIN_H))
        self._income_view = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, WIN_W, INCOME_WIN_H))
        root.addSubview_(self._menu_view)
        root.addSubview_(self._config_view)
        root.addSubview_(self._pp30_view)
        root.addSubview_(self._ka_tam_view)
        root.addSubview_(self._pnd30_view)
        root.addSubview_(self._pnd3_view)
        root.addSubview_(self._pnd1_view)
        root.addSubview_(self._pnd2_view)
        root.addSubview_(self._bt40_view)
        root.addSubview_(self._sso_view)
        root.addSubview_(self._wcf_view)
        root.addSubview_(self._payroll_view)
        root.addSubview_(self._income_view)
        self._build_menu_page(self._menu_view)
        self._build_config_page(self._config_view)
        self._build_pp30_page(self._pp30_view)
        self._build_ka_tam_page(self._ka_tam_view)
        self._build_pnd30_page(self._pnd30_view)
        self._build_pnd3_page(self._pnd3_view)
        self._build_pnd1_page(self._pnd1_view)
        self._build_pnd2_page(self._pnd2_view)
        self._build_bt40_page(self._bt40_view)
        self._build_sso_page(self._sso_view)
        self._build_wcf_page(self._wcf_view)
        self._build_payroll_page(self._payroll_view)
        self._build_income_page(self._income_view)
        self.window.makeKeyAndOrderFront_(None)

    def _build_menu_page(self, page) -> None:
        margin = 24
        content_w = WIN_W - margin * 2
        _button(
            page,
            UI_TEXT["menu_config"],
            WIN_W - margin - 110,
            28,
            110,
            32,
            self._keep(lambda: self._show_page(PAGE_CONFIG)),
            font_size=13,
            bezel=NSBezelStyleRounded,
        )
        y = 36
        _static_label(page, UI_TEXT["menu_title"], margin, y, content_w - 120, 28, size=18, bold=True)
        button_h = MENU_BUTTON_HEIGHT
        gap = 8
        inner_h = max(len(TOPIC_MENU_ITEMS) * (button_h + gap), 1)
        scroll_y = 80
        scroll_h = MENU_WIN_H - scroll_y - 16
        scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(margin, scroll_y, content_w, scroll_h))
        scroll.setHasVerticalScroller_(True)
        scroll.setHasHorizontalScroller_(False)
        scroll.setAutohidesScrollers_(True)
        scroll.setDrawsBackground_(False)
        scroll.setBorderType_(0)
        inner = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, content_w, inner_h))
        y = 0
        for item in TOPIC_MENU_ITEMS:
            _button(
                inner,
                item.title,
                0,
                y,
                content_w - 18,
                button_h,
                self._keep(lambda selected=item: self._open_topic(selected)),
                font_size=15,
            )
            y += button_h + gap
        inner.setFrame_(NSMakeRect(0, 0, content_w, max(y, scroll_h)))
        scroll.setDocumentView_(inner)
        page.addSubview_(scroll)
        self._menu_scroll = scroll

    def _build_config_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["config_title"], 188, 30, WIN_W - 212, 24, size=16, bold=True)
        _static_label(page, UI_TEXT["express_data_dir"], 24, 84, 140, 22)
        self.express_data_dir_field = _edit_field(page, 170, 84, 250)
        _button(
            page,
            UI_TEXT["choose_folder"],
            428,
            80,
            108,
            28,
            self._keep(self._choose_express_data_dir),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["express_data_dir_hint"], 24, 116, WIN_W - 48, 20, size=11, gray=True)
        self.express_data_summary_field = _static_label(
            page, UI_TEXT["express_data_dir_empty"], 24, 144, WIN_W - 48, 20, size=12, gray=True
        )
        _button(
            page,
            UI_TEXT["save"],
            24,
            184,
            120,
            36,
            self._keep(self._save_config),
            bezel=NSBezelStyleRounded,
        )
        self._refresh_config_fields()

    def _build_pp30_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_pp30"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 228)
        sy = 8
        _static_label(settings, UI_TEXT["pp30_run_mode"], 8, sy, 110, 22)
        self.pp30_mode_normal = _radio(
            settings,
            UI_TEXT["pp30_mode_normal"],
            120,
            sy - 2,
            130,
            26,
            self._keep(lambda: self._set_pp30_mode(PP30_MODE_NORMAL)),
        )
        self.pp30_mode_special = _radio(
            settings,
            UI_TEXT["pp30_mode_special"],
            260,
            sy - 2,
            130,
            26,
            self._keep(lambda: self._set_pp30_mode(PP30_MODE_SPECIAL)),
        )
        self._set_pp30_mode(PP30_MODE_NORMAL)
        sy += 32
        _static_label(settings, UI_TEXT["pp30_pdf_folder"], 8, sy, 110, 22)
        self.pp30_folder_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_folder"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_pp30_folder),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.pp30_folder_summary_field = _static_label(
            settings, UI_TEXT["pp30_pdf_summary_empty"], 8, sy, 500, 20, size=11, gray=True
        )
        sy += 28
        _static_label(settings, UI_TEXT["pp30_jv_date"], 8, sy, 110, 22)
        self.pp30_jv_date_field = _edit_field(settings, 120, sy, 120)
        self.pp30_jv_date_field.setPlaceholderString_(PV_DATE_EXAMPLE)
        date_delegate = _DateFieldDelegate.alloc().init()
        self.pp30_jv_date_field.setDelegate_(date_delegate)
        self._pp30_date_delegate = date_delegate
        sy += 30
        _static_label(settings, UI_TEXT["pp30_jv_period"], 8, sy, 140, 22)
        self.pp30_jv_period_field = self._period_field(settings, 150, sy)
        sy += 30
        _static_label(settings, UI_TEXT["pp30_pv_period"], 8, sy, 140, 22)
        self.pp30_pv_period_field = self._period_field(settings, 150, sy)

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            312,
            160,
            36,
            self._keep(self._start_pp30),
            bezel=NSBezelStyleRounded,
        )

        y = 360
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, PP30_WIN_H - y - 12)
        self.pp30_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.pp30_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.pp30_progress_bar.setIndeterminate_(False)
        self.pp30_progress_bar.setMinValue_(0)
        self.pp30_progress_bar.setMaxValue_(100)
        self.pp30_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.pp30_progress_bar)
        self.pp30_progress_field = _static_label(status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22)
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_pp30_log), bezel=NSBezelStyleRounded)
        self.pp30_log_view = _log_view(status, 8, 60, WIN_W - 56, PP30_WIN_H - y - 100)
        self.pp30_log_view.setString_(UI_TEXT["pp30_welcome_log"] + "\n")
        del _settings_box, _status_box

    def _build_ka_tam_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_ka_tam"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 198)
        sy = 8
        _static_label(settings, UI_TEXT["ka_tam_excel"], 8, sy, 110, 22)
        self.ka_tam_excel_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_file"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_ka_tam_excel),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.ka_tam_excel_summary_field = _static_label(
            settings, UI_TEXT["ka_tam_excel_empty"], 8, sy, 500, 20, size=11, gray=True
        )
        sy += 28
        _static_label(settings, UI_TEXT["ka_tam_pv_date"], 8, sy, 110, 22)
        self.ka_tam_pv_date_field = _edit_field(settings, 120, sy, 120)
        self.ka_tam_pv_date_field.setPlaceholderString_(PV_DATE_EXAMPLE)
        date_delegate = _DateFieldDelegate.alloc().init()
        self.ka_tam_pv_date_field.setDelegate_(date_delegate)
        self._ka_tam_date_delegate = date_delegate
        sy += 30
        _static_label(settings, UI_TEXT["ka_tam_period"], 8, sy, 110, 22)
        self.ka_tam_period_field = self._period_field(settings, 120, sy)
        sy += 30
        _static_label(settings, UI_TEXT["ka_tam_tax_payer"], 8, sy, 110, 22)
        self.ka_tam_tax_payer_field = _edit_field(settings, 120, sy, 356)

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            286,
            160,
            36,
            self._keep(self._start_ka_tam),
            bezel=NSBezelStyleRounded,
        )

        y = 336
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, KA_TAM_WIN_H - y - 12)
        self.ka_tam_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.ka_tam_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.ka_tam_progress_bar.setIndeterminate_(False)
        self.ka_tam_progress_bar.setMinValue_(0)
        self.ka_tam_progress_bar.setMaxValue_(100)
        self.ka_tam_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.ka_tam_progress_bar)
        self.ka_tam_progress_field = _static_label(
            status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22
        )
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_ka_tam_log), bezel=NSBezelStyleRounded)
        self.ka_tam_log_view = _log_view(status, 8, 60, WIN_W - 56, KA_TAM_WIN_H - y - 100)
        self.ka_tam_log_view.setString_(UI_TEXT["ka_tam_welcome_log"] + "\n")
        del _settings_box, _status_box

    def _build_pnd30_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_pnd30"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 138)
        sy = 8
        _static_label(settings, UI_TEXT["pp30_pdf_folder"], 8, sy, 110, 22)
        self.pnd30_folder_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_folder"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_pnd30_folder),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.pnd30_folder_summary_field = _static_label(
            settings, UI_TEXT["pp30_pdf_summary_empty"], 8, sy, 500, 20, size=11, gray=True
        )
        sy += 28
        _static_label(settings, UI_TEXT["pnd30_period"], 8, sy, 110, 22)
        self.pnd30_period_field = self._period_field(settings, 120, sy)

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            226,
            160,
            36,
            self._keep(self._start_pnd30),
            bezel=NSBezelStyleRounded,
        )

        y = 276
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, PND30_WIN_H - y - 12)
        self.pnd30_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.pnd30_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.pnd30_progress_bar.setIndeterminate_(False)
        self.pnd30_progress_bar.setMinValue_(0)
        self.pnd30_progress_bar.setMaxValue_(100)
        self.pnd30_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.pnd30_progress_bar)
        self.pnd30_progress_field = _static_label(
            status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22
        )
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_pnd30_log), bezel=NSBezelStyleRounded)
        self.pnd30_log_view = _log_view(status, 8, 60, WIN_W - 56, PND30_WIN_H - y - 100)
        self.pnd30_log_view.setString_(UI_TEXT["pnd30_welcome_log"] + "\n")
        del _settings_box, _status_box

    def _build_pnd3_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_pnd3"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 138)
        sy = 8
        _static_label(settings, UI_TEXT["pp30_pdf_folder"], 8, sy, 110, 22)
        self.pnd3_folder_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_folder"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_pnd3_folder),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.pnd3_folder_summary_field = _static_label(
            settings, UI_TEXT["pp30_pdf_summary_empty"], 8, sy, 500, 20, size=11, gray=True
        )
        sy += 28
        _static_label(settings, UI_TEXT["pnd3_period"], 8, sy, 110, 22)
        self.pnd3_period_field = self._period_field(settings, 120, sy)

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            226,
            160,
            36,
            self._keep(self._start_pnd3),
            bezel=NSBezelStyleRounded,
        )

        y = 276
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, PND3_WIN_H - y - 12)
        self.pnd3_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.pnd3_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.pnd3_progress_bar.setIndeterminate_(False)
        self.pnd3_progress_bar.setMinValue_(0)
        self.pnd3_progress_bar.setMaxValue_(100)
        self.pnd3_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.pnd3_progress_bar)
        self.pnd3_progress_field = _static_label(
            status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22
        )
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_pnd3_log), bezel=NSBezelStyleRounded)
        self.pnd3_log_view = _log_view(status, 8, 60, WIN_W - 56, PND3_WIN_H - y - 100)
        self.pnd3_log_view.setString_(UI_TEXT["pnd3_welcome_log"] + "\n")
        del _settings_box, _status_box


    def _build_pnd1_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_pnd1"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 138)
        sy = 8
        _static_label(settings, UI_TEXT["pp30_pdf_folder"], 8, sy, 110, 22)
        self.pnd1_folder_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_folder"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_pnd1_folder),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.pnd1_folder_summary_field = _static_label(
            settings, UI_TEXT["pp30_pdf_summary_empty"], 8, sy, 500, 20, size=11, gray=True
        )
        sy += 28
        _static_label(settings, UI_TEXT["pnd1_period"], 8, sy, 110, 22)
        self.pnd1_period_field = self._period_field(settings, 120, sy)

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            226,
            160,
            36,
            self._keep(self._start_pnd1),
            bezel=NSBezelStyleRounded,
        )

        y = 276
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, PND1_WIN_H - y - 12)
        self.pnd1_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.pnd1_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.pnd1_progress_bar.setIndeterminate_(False)
        self.pnd1_progress_bar.setMinValue_(0)
        self.pnd1_progress_bar.setMaxValue_(100)
        self.pnd1_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.pnd1_progress_bar)
        self.pnd1_progress_field = _static_label(
            status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22
        )
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_pnd1_log), bezel=NSBezelStyleRounded)
        self.pnd1_log_view = _log_view(status, 8, 60, WIN_W - 56, PND1_WIN_H - y - 100)
        self.pnd1_log_view.setString_(UI_TEXT["pnd1_welcome_log"] + "\n")
        del _settings_box, _status_box


    def _build_pnd2_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_pnd2"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 138)
        sy = 8
        _static_label(settings, UI_TEXT["pp30_pdf_folder"], 8, sy, 110, 22)
        self.pnd2_folder_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_folder"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_pnd2_folder),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.pnd2_folder_summary_field = _static_label(
            settings, UI_TEXT["pp30_pdf_summary_empty"], 8, sy, 500, 20, size=11, gray=True
        )

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            226,
            160,
            36,
            self._keep(self._start_pnd2),
            bezel=NSBezelStyleRounded,
        )

        y = 276
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, PND2_WIN_H - y - 12)
        self.pnd2_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.pnd2_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.pnd2_progress_bar.setIndeterminate_(False)
        self.pnd2_progress_bar.setMinValue_(0)
        self.pnd2_progress_bar.setMaxValue_(100)
        self.pnd2_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.pnd2_progress_bar)
        self.pnd2_progress_field = _static_label(
            status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22
        )
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_pnd2_log), bezel=NSBezelStyleRounded)
        self.pnd2_log_view = _log_view(status, 8, 60, WIN_W - 56, PND2_WIN_H - y - 100)
        self.pnd2_log_view.setString_(UI_TEXT["pnd2_welcome_log"] + "\n")
        del _settings_box, _status_box

    def _build_bt40_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_bt40"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 168)
        sy = 8
        _static_label(settings, UI_TEXT["pp30_pdf_folder"], 8, sy, 110, 22)
        self.bt40_folder_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_folder"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_bt40_folder),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.bt40_folder_summary_field = _static_label(
            settings, UI_TEXT["pp30_pdf_summary_empty"], 8, sy, 500, 20, size=11, gray=True
        )
        sy += 28
        _static_label(settings, UI_TEXT["bt40_rv_date"], 8, sy, 110, 22)
        self.bt40_rv_date_field = _edit_field(settings, 120, sy, 120)
        self.bt40_rv_date_field.setPlaceholderString_(PV_DATE_EXAMPLE)
        date_delegate = _DateFieldDelegate.alloc().init()
        self.bt40_rv_date_field.setDelegate_(date_delegate)
        self._bt40_date_delegate = date_delegate
        sy += 30
        _static_label(settings, UI_TEXT["bt40_period"], 8, sy, 110, 22)
        self.bt40_period_field = self._period_field(settings, 120, sy)

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            256,
            160,
            36,
            self._keep(self._start_bt40),
            bezel=NSBezelStyleRounded,
        )

        y = 306
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, BT40_WIN_H - y - 12)
        self.bt40_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.bt40_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.bt40_progress_bar.setIndeterminate_(False)
        self.bt40_progress_bar.setMinValue_(0)
        self.bt40_progress_bar.setMaxValue_(100)
        self.bt40_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.bt40_progress_bar)
        self.bt40_progress_field = _static_label(
            status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22
        )
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_bt40_log), bezel=NSBezelStyleRounded)
        self.bt40_log_view = _log_view(status, 8, 60, WIN_W - 56, BT40_WIN_H - y - 100)
        self.bt40_log_view.setString_(UI_TEXT["bt40_welcome_log"] + "\n")
        del _settings_box, _status_box

    def _build_sso_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_sso"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 138)
        sy = 8
        _static_label(settings, UI_TEXT["pp30_pdf_folder"], 8, sy, 110, 22)
        self.sso_folder_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_folder"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_sso_folder),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.sso_folder_summary_field = _static_label(
            settings, UI_TEXT["pp30_pdf_summary_empty"], 8, sy, 500, 20, size=11, gray=True
        )
        sy += 28
        _static_label(settings, UI_TEXT["sso_period"], 8, sy, 110, 22)
        self.sso_period_field = self._period_field(settings, 120, sy)

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            226,
            160,
            36,
            self._keep(self._start_sso),
            bezel=NSBezelStyleRounded,
        )

        y = 276
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, SSO_WIN_H - y - 12)
        self.sso_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.sso_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.sso_progress_bar.setIndeterminate_(False)
        self.sso_progress_bar.setMinValue_(0)
        self.sso_progress_bar.setMaxValue_(100)
        self.sso_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.sso_progress_bar)
        self.sso_progress_field = _static_label(
            status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22
        )
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_sso_log), bezel=NSBezelStyleRounded)
        self.sso_log_view = _log_view(status, 8, 60, WIN_W - 56, SSO_WIN_H - y - 100)
        self.sso_log_view.setString_(UI_TEXT["sso_welcome_log"] + "\n")
        del _settings_box, _status_box

    def _build_wcf_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_wcf"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 90)
        sy = 8
        _static_label(settings, UI_TEXT["wcf_excel"], 8, sy, 110, 22)
        self.wcf_excel_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_file"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_wcf_excel),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.wcf_excel_summary_field = _static_label(
            settings, UI_TEXT["wcf_excel_empty"], 8, sy, 500, 20, size=11, gray=True
        )

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            180,
            160,
            36,
            self._keep(self._start_wcf),
            bezel=NSBezelStyleRounded,
        )

        y = 230
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, WCF_WIN_H - y - 12)
        self.wcf_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.wcf_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.wcf_progress_bar.setIndeterminate_(False)
        self.wcf_progress_bar.setMinValue_(0)
        self.wcf_progress_bar.setMaxValue_(100)
        self.wcf_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.wcf_progress_bar)
        self.wcf_progress_field = _static_label(
            status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22
        )
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_wcf_log), bezel=NSBezelStyleRounded)
        self.wcf_log_view = _log_view(status, 8, 60, WIN_W - 56, WCF_WIN_H - y - 100)
        self.wcf_log_view.setString_(UI_TEXT["wcf_welcome_log"] + "\n")
        del _settings_box, _status_box

    def _build_payroll_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_payroll"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 168)
        sy = 8
        _static_label(settings, UI_TEXT["payroll_excel"], 8, sy, 110, 22)
        self.payroll_excel_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_file"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_payroll_excel),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.payroll_excel_summary_field = _static_label(
            settings, UI_TEXT["payroll_excel_empty"], 8, sy, 500, 20, size=11, gray=True
        )
        sy += 28
        _static_label(settings, UI_TEXT["payroll_pv_date"], 8, sy, 110, 22)
        self.payroll_pv_date_field = _edit_field(settings, 120, sy, 120)
        self.payroll_pv_date_field.setPlaceholderString_(PV_DATE_EXAMPLE)
        date_delegate = _DateFieldDelegate.alloc().init()
        self.payroll_pv_date_field.setDelegate_(date_delegate)
        self._payroll_date_delegate = date_delegate
        sy += 30
        _static_label(settings, UI_TEXT["payroll_period"], 8, sy, 110, 22)
        self.payroll_period_field = self._period_field(settings, 120, sy)

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            256,
            160,
            36,
            self._keep(self._start_payroll),
            bezel=NSBezelStyleRounded,
        )

        y = 306
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, PAYROLL_WIN_H - y - 12)
        self.payroll_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.payroll_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.payroll_progress_bar.setIndeterminate_(False)
        self.payroll_progress_bar.setMinValue_(0)
        self.payroll_progress_bar.setMaxValue_(100)
        self.payroll_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.payroll_progress_bar)
        self.payroll_progress_field = _static_label(
            status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22
        )
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_payroll_log), bezel=NSBezelStyleRounded)
        self.payroll_log_view = _log_view(status, 8, 60, WIN_W - 56, PAYROLL_WIN_H - y - 100)
        self.payroll_log_view.setString_(UI_TEXT["payroll_welcome_log"] + "\n")
        del _settings_box, _status_box

    def _build_income_page(self, page) -> None:
        _button(
            page,
            f"← {UI_TEXT['back_to_menu']}",
            16,
            24,
            160,
            36,
            self._keep(lambda: self._show_page(PAGE_MENU)),
            bezel=NSBezelStyleRounded,
        )
        _static_label(page, UI_TEXT["menu_income"], 188, 30, WIN_W - 212, 24, size=16, bold=True)

        _settings_box, settings = _box(page, "", 12, 72, WIN_W - 24, 202)
        sy = 8
        _static_label(settings, UI_TEXT["income_lock"], 8, sy, 110, 22)
        self.income_lock_none = _radio(
            settings,
            UI_TEXT["income_lock_none"],
            120,
            sy - 2,
            130,
            26,
            self._keep(lambda: self._set_income_lock(INCOME_LOCK_NONE)),
        )
        self.income_lock_password = _radio(
            settings,
            UI_TEXT["income_lock_password"],
            260,
            sy - 2,
            130,
            26,
            self._keep(lambda: self._set_income_lock(INCOME_LOCK_PASSWORD)),
        )
        self._income_lock = IncomeLockMode.parse(INCOME_LOCK_NONE)
        self._sync_income_lock_radios()
        sy += 32
        _static_label(settings, UI_TEXT["pp30_pdf_folder"], 8, sy, 110, 22)
        self.income_folder_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_folder"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_income_folder),
            bezel=NSBezelStyleRounded,
        )
        sy += 26
        self.income_folder_summary_field = _static_label(
            settings, UI_TEXT["pp30_pdf_summary_empty"], 8, sy, 500, 20, size=11, gray=True
        )
        sy += 28
        _static_label(settings, UI_TEXT["income_report_folder"], 8, sy, 110, 22)
        self.income_report_field = _edit_field(settings, 120, sy, 248)
        _button(
            settings,
            UI_TEXT["choose_folder"],
            376,
            sy - 2,
            108,
            28,
            self._keep(self._choose_income_report_folder),
            bezel=NSBezelStyleRounded,
        )
        sy += 32
        _static_label(settings, UI_TEXT["income_start_date"], 8, sy, 110, 22)
        self.income_start_field = _edit_field(settings, 120, sy, 120)
        self.income_start_field.setPlaceholderString_(PV_DATE_EXAMPLE)
        date_delegate = _DateFieldDelegate.alloc().init()
        self.income_start_field.setDelegate_(date_delegate)
        self._income_date_delegate = date_delegate

        _button(
            page,
            f"▶ {UI_TEXT['start']}",
            16,
            290,
            160,
            36,
            self._keep(self._start_income),
            bezel=NSBezelStyleRounded,
        )

        y = 340
        _status_box, status = _box(page, UI_TEXT["status_frame"], 12, y, WIN_W - 24, INCOME_WIN_H - y - 12)
        self.income_progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSMakeRect(8, 8, 360, 16))
        self.income_progress_bar.setStyle_(NSProgressIndicatorStyleBar)
        self.income_progress_bar.setIndeterminate_(False)
        self.income_progress_bar.setMinValue_(0)
        self.income_progress_bar.setMaxValue_(100)
        self.income_progress_bar.setDoubleValue_(0)
        status.addSubview_(self.income_progress_bar)
        self.income_progress_field = _static_label(
            status, UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0), 376, 4, 140, 22
        )
        _button(status, UI_TEXT["copy_log"], 376, 28, 120, 28, self._keep(self._copy_income_log), bezel=NSBezelStyleRounded)
        self.income_log_view = _log_view(status, 8, 60, WIN_W - 56, INCOME_WIN_H - y - 100)
        self.income_log_view.setString_(UI_TEXT["income_welcome_log"] + "\n")
        del _settings_box, _status_box

    def _set_income_lock(self, key: str) -> None:
        self._income_lock = IncomeLockMode.parse(key)
        self._sync_income_lock_radios()

    def _sync_income_lock_radios(self) -> None:
        self.income_lock_none.setState_(0 if self._income_lock.is_locked else 1)
        self.income_lock_password.setState_(1 if self._income_lock.is_locked else 0)

    def _set_pp30_mode(self, key: str) -> None:
        self._pp30_mode = Pp30RunMode.parse(key)
        self.pp30_mode_normal.setState_(1 if self._pp30_mode.key == PP30_MODE_NORMAL else 0)
        self.pp30_mode_special.setState_(1 if self._pp30_mode.key == PP30_MODE_SPECIAL else 0)

    def _open_topic(self, item: TopicMenuItem) -> None:
        if item.page_route == PAGE_PP30:
            self._show_page(PAGE_PP30)
            return
        if item.page_route == PAGE_KA_TAM:
            self._show_page(PAGE_KA_TAM)
            return
        if item.page_route == PAGE_PND30:
            self._show_page(PAGE_PND30)
            return
        if item.page_route == PAGE_PND3:
            self._show_page(PAGE_PND3)
            return
        if item.page_route == PAGE_PND1:
            self._show_page(PAGE_PND1)
            return
        if item.page_route == PAGE_PND2:
            self._show_page(PAGE_PND2)
            return
        if item.page_route == PAGE_BT40:
            self._show_page(PAGE_BT40)
            return
        if item.page_route == PAGE_SSO:
            self._show_page(PAGE_SSO)
            return
        if item.page_route == PAGE_WCF:
            self._show_page(PAGE_WCF)
            return
        if item.page_route == PAGE_PAYROLL:
            self._show_page(PAGE_PAYROLL)
            return
        if item.page_route == PAGE_INCOME:
            self._show_page(PAGE_INCOME)
            return
        _alert(UI_TEXT["app_title"], UI_TEXT["menu_unavailable"])

    def _choose_express_data_dir(self) -> None:
        selected = _pick_folder()
        if not selected:
            return
        self.express_data_dir_field.setStringValue_(selected)
        self._save_config()

    def _choose_pp30_folder(self) -> None:
        selected = _pick_folder()
        if not selected:
            return
        self.pp30_folder_field.setStringValue_(selected)
        self._load_pp30_folder()

    def _load_pp30_folder(self) -> None:
        folder = Path(str(self.pp30_folder_field.stringValue() or "")).expanduser()
        self.pp30_pdf_files = Pp30FolderService.list_pdfs(folder)
        if self.pp30_pdf_files:
            self.pp30_folder_summary_field.setStringValue_(
                UI_TEXT["pp30_pdf_total"].format(count=len(self.pp30_pdf_files))
            )
        else:
            self.pp30_folder_summary_field.setStringValue_(UI_TEXT["pp30_pdf_summary_empty"])

    def _pp30_form_config(self) -> Pp30FormConfig:
        folder = Path(str(self.pp30_folder_field.stringValue() or "")).expanduser()
        return Pp30FormConfig(
            pdf_folder=folder,
            jv_period=MonthYearPeriod.parse(str(self.pp30_jv_period_field.stringValue() or "")),
            pv_period=MonthYearPeriod.parse(str(self.pp30_pv_period_field.stringValue() or "")),
            jv_date=format_express_pv_date(str(self.pp30_jv_date_field.stringValue() or "")),
            pdf_files=list(self.pp30_pdf_files),
            run_mode=self._pp30_mode,
        )

    def _start_pp30(self) -> None:
        if self._pp30_running:
            return
        self.app_config = self.app_config_service.load()
        errors = self.app_config.validate()
        self._load_pp30_folder()
        errors.extend(self._pp30_form_config().validate())
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = len(self.pp30_pdf_files)
        self._set_pp30_progress(0, total)
        self._append_pp30_log(UI_TEXT["pp30_pdf_total"].format(count=total))
        pdf_files = list(self.pp30_pdf_files)
        express_data_dir = self.app_config.express_data_dir
        form_config = self._pp30_form_config()
        self._pp30_running = True
        threading.Thread(
            target=self._run_pp30_match,
            args=(pdf_files, express_data_dir, form_config),
            daemon=True,
        ).start()

    def _run_pp30_match(self, pdf_files: list[Path], express_data_dir: Path, form_config) -> None:
        try:
            Pp30MatchRunService.run(
                pdf_files,
                express_data_dir,
                form_config=form_config,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_pp30_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_pp30_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._pp30_match_finished)

    def _pp30_match_finished(self) -> None:
        self._pp30_running = False

    def _set_pp30_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.pp30_progress_bar.setDoubleValue_(percent)
        self.pp30_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_pp30_log(self, message: str) -> None:
        current = str(self.pp30_log_view.string() or "")
        current += message + "\n"
        self.pp30_log_view.setString_(current)
        self.pp30_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_pp30_log(self) -> None:
        text = str(self.pp30_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)

    def _choose_ka_tam_excel(self) -> None:
        selected = _pick_file(("xlsx", "xls"))
        if not selected:
            return
        self.ka_tam_excel_field.setStringValue_(selected)
        self._load_ka_tam_excel()

    def _load_ka_tam_excel(self) -> None:
        path = Path(str(self.ka_tam_excel_field.stringValue() or "")).expanduser()
        if not path.exists():
            self.ka_tam_rows_count = 0
            self.ka_tam_excel_summary_field.setStringValue_(UI_TEXT["ka_tam_excel_empty"])
            return
        try:
            rows = KaTamExcelService.load_rows(path)
        except Exception as exc:
            self.ka_tam_rows_count = 0
            self.ka_tam_excel_summary_field.setStringValue_(str(exc))
            return
        self.ka_tam_rows_count = len(rows)
        self.ka_tam_excel_summary_field.setStringValue_(UI_TEXT["ka_tam_excel_total"].format(count=len(rows)))

    def _ka_tam_form_config(self) -> KaTamFormConfig:
        return KaTamFormConfig(
            excel_path=Path(str(self.ka_tam_excel_field.stringValue() or "")).expanduser(),
            pv_date=format_express_pv_date(str(self.ka_tam_pv_date_field.stringValue() or "")),
            period=MonthYearPeriod.parse(str(self.ka_tam_period_field.stringValue() or "")),
            tax_payer_id=str(self.ka_tam_tax_payer_field.stringValue() or "").strip(),
        )

    def _start_ka_tam(self) -> None:
        if self._ka_tam_running:
            return
        self.app_config = self.app_config_service.load()
        self._load_ka_tam_excel()
        errors = self.app_config.validate()
        errors.extend(self._ka_tam_form_config().validate())
        if self.ka_tam_rows_count == 0 and not errors:
            errors.append(UI_TEXT["ka_tam_excel_none"])
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = self.ka_tam_rows_count
        self._set_ka_tam_progress(0, total)
        self._append_ka_tam_log(UI_TEXT["ka_tam_excel_total"].format(count=total))
        form_config = self._ka_tam_form_config()
        express_data_dir = self.app_config.express_data_dir
        self._ka_tam_running = True
        threading.Thread(target=self._run_ka_tam, args=(form_config, express_data_dir), daemon=True).start()

    def _run_ka_tam(self, form_config: KaTamFormConfig, express_data_dir: Path) -> None:
        try:
            KaTamMatchRunService.run(
                form_config,
                express_data_dir,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_ka_tam_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_ka_tam_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._ka_tam_finished)

    def _ka_tam_finished(self) -> None:
        self._ka_tam_running = False

    def _set_ka_tam_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.ka_tam_progress_bar.setDoubleValue_(percent)
        self.ka_tam_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_ka_tam_log(self, message: str) -> None:
        current = str(self.ka_tam_log_view.string() or "")
        current += message + "\n"
        self.ka_tam_log_view.setString_(current)
        self.ka_tam_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_ka_tam_log(self) -> None:
        text = str(self.ka_tam_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)

    def _choose_pnd30_folder(self) -> None:
        selected = _pick_folder()
        if not selected:
            return
        self.pnd30_folder_field.setStringValue_(selected)
        self._load_pnd30_folder()

    def _load_pnd30_folder(self) -> None:
        folder = Path(str(self.pnd30_folder_field.stringValue() or "")).expanduser()
        self.pnd30_pdf_files = Pp30FolderService.list_pdfs(folder)
        if self.pnd30_pdf_files:
            self.pnd30_folder_summary_field.setStringValue_(
                UI_TEXT["pp30_pdf_total"].format(count=len(self.pnd30_pdf_files))
            )
        else:
            self.pnd30_folder_summary_field.setStringValue_(UI_TEXT["pp30_pdf_summary_empty"])

    def _pnd30_form_config(self) -> Pnd30FormConfig:
        return Pnd30FormConfig(
            pdf_folder=Path(str(self.pnd30_folder_field.stringValue() or "")).expanduser(),
            period=MonthYearPeriod.parse(str(self.pnd30_period_field.stringValue() or "")),
            pdf_files=list(self.pnd30_pdf_files),
        )

    def _start_pnd30(self) -> None:
        if self._pnd30_running:
            return
        self.app_config = self.app_config_service.load()
        self._load_pnd30_folder()
        errors = self.app_config.validate()
        errors.extend(self._pnd30_form_config().validate())
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = len(self.pnd30_pdf_files)
        self._set_pnd30_progress(0, total)
        self._append_pnd30_log(UI_TEXT["pp30_pdf_total"].format(count=total))
        form_config = self._pnd30_form_config()
        express_data_dir = self.app_config.express_data_dir
        self._pnd30_running = True
        threading.Thread(target=self._run_pnd30, args=(form_config, express_data_dir), daemon=True).start()

    def _run_pnd30(self, form_config: Pnd30FormConfig, express_data_dir: Path) -> None:
        try:
            Pnd30MatchRunService.run(
                form_config,
                express_data_dir,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_pnd30_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_pnd30_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._pnd30_finished)

    def _pnd30_finished(self) -> None:
        self._pnd30_running = False

    def _set_pnd30_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.pnd30_progress_bar.setDoubleValue_(percent)
        self.pnd30_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_pnd30_log(self, message: str) -> None:
        current = str(self.pnd30_log_view.string() or "")
        current += message + "\n"
        self.pnd30_log_view.setString_(current)
        self.pnd30_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_pnd30_log(self) -> None:
        text = str(self.pnd30_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)

    def _choose_pnd3_folder(self) -> None:
        selected = _pick_folder()
        if not selected:
            return
        self.pnd3_folder_field.setStringValue_(selected)
        self._load_pnd3_folder()

    def _load_pnd3_folder(self) -> None:
        folder = Path(str(self.pnd3_folder_field.stringValue() or "")).expanduser()
        self.pnd3_pdf_files = Pp30FolderService.list_pdfs(folder)
        if self.pnd3_pdf_files:
            self.pnd3_folder_summary_field.setStringValue_(
                UI_TEXT["pp30_pdf_total"].format(count=len(self.pnd3_pdf_files))
            )
        else:
            self.pnd3_folder_summary_field.setStringValue_(UI_TEXT["pp30_pdf_summary_empty"])

    def _pnd3_form_config(self) -> Pnd3FormConfig:
        return Pnd3FormConfig(
            pdf_folder=Path(str(self.pnd3_folder_field.stringValue() or "")).expanduser(),
            period=MonthYearPeriod.parse(str(self.pnd3_period_field.stringValue() or "")),
            pdf_files=list(self.pnd3_pdf_files),
        )

    def _start_pnd3(self) -> None:
        if self._pnd3_running:
            return
        self.app_config = self.app_config_service.load()
        self._load_pnd3_folder()
        errors = self.app_config.validate()
        errors.extend(self._pnd3_form_config().validate())
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = len(self.pnd3_pdf_files)
        self._set_pnd3_progress(0, total)
        self._append_pnd3_log(UI_TEXT["pp30_pdf_total"].format(count=total))
        form_config = self._pnd3_form_config()
        express_data_dir = self.app_config.express_data_dir
        self._pnd3_running = True
        threading.Thread(target=self._run_pnd3, args=(form_config, express_data_dir), daemon=True).start()

    def _run_pnd3(self, form_config: Pnd3FormConfig, express_data_dir: Path) -> None:
        try:
            Pnd3MatchRunService.run(
                form_config,
                express_data_dir,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_pnd3_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_pnd3_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._pnd3_finished)

    def _pnd3_finished(self) -> None:
        self._pnd3_running = False

    def _set_pnd3_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.pnd3_progress_bar.setDoubleValue_(percent)
        self.pnd3_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_pnd3_log(self, message: str) -> None:
        current = str(self.pnd3_log_view.string() or "")
        current += message + "\n"
        self.pnd3_log_view.setString_(current)
        self.pnd3_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_pnd3_log(self) -> None:
        text = str(self.pnd3_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)


    def _choose_pnd1_folder(self) -> None:
        selected = _pick_folder()
        if not selected:
            return
        self.pnd1_folder_field.setStringValue_(selected)
        self._load_pnd1_folder()

    def _load_pnd1_folder(self) -> None:
        folder = Path(str(self.pnd1_folder_field.stringValue() or "")).expanduser()
        self.pnd1_pdf_files = Pp30FolderService.list_pdfs(folder)
        if self.pnd1_pdf_files:
            self.pnd1_folder_summary_field.setStringValue_(
                UI_TEXT["pp30_pdf_total"].format(count=len(self.pnd1_pdf_files))
            )
        else:
            self.pnd1_folder_summary_field.setStringValue_(UI_TEXT["pp30_pdf_summary_empty"])

    def _pnd1_form_config(self) -> Pnd1FormConfig:
        return Pnd1FormConfig(
            pdf_folder=Path(str(self.pnd1_folder_field.stringValue() or "")).expanduser(),
            period=MonthYearPeriod.parse(str(self.pnd1_period_field.stringValue() or "")),
            pdf_files=list(self.pnd1_pdf_files),
        )

    def _start_pnd1(self) -> None:
        if self._pnd1_running:
            return
        self.app_config = self.app_config_service.load()
        self._load_pnd1_folder()
        errors = self.app_config.validate()
        errors.extend(self._pnd1_form_config().validate())
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = len(self.pnd1_pdf_files)
        self._set_pnd1_progress(0, total)
        self._append_pnd1_log(UI_TEXT["pp30_pdf_total"].format(count=total))
        form_config = self._pnd1_form_config()
        express_data_dir = self.app_config.express_data_dir
        self._pnd1_running = True
        threading.Thread(target=self._run_pnd1, args=(form_config, express_data_dir), daemon=True).start()

    def _run_pnd1(self, form_config: Pnd1FormConfig, express_data_dir: Path) -> None:
        try:
            Pnd1MatchRunService.run(
                form_config,
                express_data_dir,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_pnd1_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_pnd1_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._pnd1_finished)

    def _pnd1_finished(self) -> None:
        self._pnd1_running = False

    def _set_pnd1_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.pnd1_progress_bar.setDoubleValue_(percent)
        self.pnd1_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_pnd1_log(self, message: str) -> None:
        current = str(self.pnd1_log_view.string() or "")
        current += message + "\n"
        self.pnd1_log_view.setString_(current)
        self.pnd1_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_pnd1_log(self) -> None:
        text = str(self.pnd1_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)

    def _choose_sso_folder(self) -> None:
        selected = _pick_folder()
        if not selected:
            return
        self.sso_folder_field.setStringValue_(selected)
        self._load_sso_folder()

    def _load_sso_folder(self) -> None:
        folder = Path(str(self.sso_folder_field.stringValue() or "")).expanduser()
        self.sso_pdf_files = Pp30FolderService.list_pdfs(folder)
        if self.sso_pdf_files:
            self.sso_folder_summary_field.setStringValue_(
                UI_TEXT["pp30_pdf_total"].format(count=len(self.sso_pdf_files))
            )
        else:
            self.sso_folder_summary_field.setStringValue_(UI_TEXT["pp30_pdf_summary_empty"])

    def _sso_form_config(self) -> SsoFormConfig:
        return SsoFormConfig(
            pdf_folder=Path(str(self.sso_folder_field.stringValue() or "")).expanduser(),
            period=MonthYearPeriod.parse(str(self.sso_period_field.stringValue() or "")),
            pdf_files=list(self.sso_pdf_files),
        )

    def _start_sso(self) -> None:
        if self._sso_running:
            return
        self.app_config = self.app_config_service.load()
        self._load_sso_folder()
        errors = self.app_config.validate()
        errors.extend(self._sso_form_config().validate())
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = len(self.sso_pdf_files)
        self._set_sso_progress(0, total)
        self._append_sso_log(UI_TEXT["pp30_pdf_total"].format(count=total))
        form_config = self._sso_form_config()
        express_data_dir = self.app_config.express_data_dir
        self._sso_running = True
        threading.Thread(
            target=self._run_sso,
            args=(form_config, express_data_dir),
            daemon=True,
        ).start()

    def _run_sso(self, form_config: SsoFormConfig, express_data_dir: Path) -> None:
        try:
            SsoMatchRunService.run(
                form_config,
                express_data_dir,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_sso_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_sso_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._sso_finished)

    def _sso_finished(self) -> None:
        self._sso_running = False

    def _set_sso_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.sso_progress_bar.setDoubleValue_(percent)
        self.sso_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_sso_log(self, message: str) -> None:
        current = str(self.sso_log_view.string() or "")
        current = current + message + "\n"
        self.sso_log_view.setString_(current)
        self.sso_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_sso_log(self) -> None:
        text = str(self.sso_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)

    def _choose_wcf_excel(self) -> None:
        selected = _pick_file(("xlsx", "xls"))
        if not selected:
            return
        self.wcf_excel_field.setStringValue_(selected)
        self._load_wcf_excel()

    def _load_wcf_excel(self) -> None:
        path = Path(str(self.wcf_excel_field.stringValue() or "")).expanduser()
        if not path.exists():
            self.wcf_rows_count = 0
            self.wcf_excel_summary_field.setStringValue_(UI_TEXT["wcf_excel_empty"])
            return
        try:
            rows = WcfExcelService.load_rows(path)
        except Exception as exc:
            self.wcf_rows_count = 0
            self.wcf_excel_summary_field.setStringValue_(str(exc))
            return
        self.wcf_rows_count = len(rows)
        self.wcf_excel_summary_field.setStringValue_(UI_TEXT["wcf_excel_total"].format(count=len(rows)))

    def _wcf_form_config(self) -> WcfFormConfig:
        return WcfFormConfig(
            excel_path=Path(str(self.wcf_excel_field.stringValue() or "")).expanduser(),
            row_count=self.wcf_rows_count,
        )

    def _start_wcf(self) -> None:
        if self._wcf_running:
            return
        self.app_config = self.app_config_service.load()
        self._load_wcf_excel()
        errors = self.app_config.validate()
        errors.extend(self._wcf_form_config().validate())
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = self.wcf_rows_count
        self._set_wcf_progress(0, total)
        self._append_wcf_log(UI_TEXT["wcf_excel_total"].format(count=total))
        form_config = self._wcf_form_config()
        express_data_dir = self.app_config.express_data_dir
        self._wcf_running = True
        threading.Thread(
            target=self._run_wcf,
            args=(form_config, express_data_dir),
            daemon=True,
        ).start()

    def _run_wcf(self, form_config: WcfFormConfig, express_data_dir: Path) -> None:
        try:
            WcfMatchRunService.run(
                form_config,
                express_data_dir,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_wcf_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_wcf_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._wcf_finished)

    def _wcf_finished(self) -> None:
        self._wcf_running = False

    def _set_wcf_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.wcf_progress_bar.setDoubleValue_(percent)
        self.wcf_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_wcf_log(self, message: str) -> None:
        current = str(self.wcf_log_view.string() or "")
        current = current + message + "\n"
        self.wcf_log_view.setString_(current)
        self.wcf_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_wcf_log(self) -> None:
        text = str(self.wcf_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)

    def _choose_payroll_excel(self) -> None:
        selected = _pick_file(("xlsx", "xls"))
        if not selected:
            return
        self.payroll_excel_field.setStringValue_(selected)
        self._load_payroll_excel()

    def _load_payroll_excel(self) -> None:
        path = Path(str(self.payroll_excel_field.stringValue() or "")).expanduser()
        if not path.exists():
            self.payroll_rows_count = 0
            self.payroll_excel_summary_field.setStringValue_(UI_TEXT["payroll_excel_empty"])
            return
        try:
            self.payroll_rows_count = PayrollExcelService.count_rows(path)
        except Exception as exc:
            self.payroll_rows_count = 0
            self.payroll_excel_summary_field.setStringValue_(str(exc))
            return
        if self.payroll_rows_count:
            self.payroll_excel_summary_field.setStringValue_(
                UI_TEXT["payroll_excel_total"].format(count=self.payroll_rows_count)
            )
        else:
            self.payroll_excel_summary_field.setStringValue_(UI_TEXT["payroll_excel_empty"])

    def _payroll_form_config(self) -> PayrollFormConfig:
        return PayrollFormConfig(
            excel_path=Path(str(self.payroll_excel_field.stringValue() or "")).expanduser(),
            pv_date=format_express_pv_date(str(self.payroll_pv_date_field.stringValue() or "")),
            period=MonthYearPeriod.parse(str(self.payroll_period_field.stringValue() or "")),
            row_count=self.payroll_rows_count,
        )

    def _start_payroll(self) -> None:
        if self._payroll_running:
            return
        self.app_config = self.app_config_service.load()
        self._load_payroll_excel()
        errors = self.app_config.validate()
        errors.extend(self._payroll_form_config().validate())
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = self.payroll_rows_count
        self._set_payroll_progress(0, total)
        self._append_payroll_log(UI_TEXT["payroll_excel_total"].format(count=total))
        form_config = self._payroll_form_config()
        express_data_dir = self.app_config.express_data_dir
        self._payroll_running = True
        threading.Thread(
            target=self._run_payroll,
            args=(form_config, express_data_dir),
            daemon=True,
        ).start()

    def _run_payroll(self, form_config: PayrollFormConfig, express_data_dir: Path) -> None:
        try:
            PayrollMatchRunService.run(
                form_config,
                express_data_dir,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_payroll_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_payroll_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._payroll_finished)

    def _payroll_finished(self) -> None:
        self._payroll_running = False

    def _set_payroll_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.payroll_progress_bar.setDoubleValue_(percent)
        self.payroll_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_payroll_log(self, message: str) -> None:
        current = str(self.payroll_log_view.string() or "")
        current = current + message + "\n"
        self.payroll_log_view.setString_(current)
        self.payroll_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_payroll_log(self) -> None:
        text = str(self.payroll_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)

    def _choose_bt40_folder(self) -> None:
        selected = _pick_folder()
        if not selected:
            return
        self.bt40_folder_field.setStringValue_(selected)
        self._load_bt40_folder()

    def _load_bt40_folder(self) -> None:
        folder = Path(str(self.bt40_folder_field.stringValue() or "")).expanduser()
        self.bt40_pdf_files = Pp30FolderService.list_pdfs(folder)
        if self.bt40_pdf_files:
            self.bt40_folder_summary_field.setStringValue_(
                UI_TEXT["pp30_pdf_total"].format(count=len(self.bt40_pdf_files))
            )
        else:
            self.bt40_folder_summary_field.setStringValue_(UI_TEXT["pp30_pdf_summary_empty"])

    def _bt40_form_config(self) -> Bt40FormConfig:
        return Bt40FormConfig(
            pdf_folder=Path(str(self.bt40_folder_field.stringValue() or "")).expanduser(),
            rv_date=format_express_pv_date(str(self.bt40_rv_date_field.stringValue() or "")),
            period=MonthYearPeriod.parse(str(self.bt40_period_field.stringValue() or "")),
            pdf_files=list(self.bt40_pdf_files),
        )

    def _start_bt40(self) -> None:
        if self._bt40_running:
            return
        self.app_config = self.app_config_service.load()
        self._load_bt40_folder()
        errors = self.app_config.validate()
        errors.extend(self._bt40_form_config().validate())
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = len(self.bt40_pdf_files)
        self._set_bt40_progress(0, total)
        self._append_bt40_log(UI_TEXT["pp30_pdf_total"].format(count=total))
        form_config = self._bt40_form_config()
        express_data_dir = self.app_config.express_data_dir
        self._bt40_running = True
        threading.Thread(target=self._run_bt40, args=(form_config, express_data_dir), daemon=True).start()

    def _run_bt40(self, form_config: Bt40FormConfig, express_data_dir: Path) -> None:
        try:
            Bt40MatchRunService.run(
                form_config,
                express_data_dir,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_bt40_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_bt40_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._bt40_finished)

    def _bt40_finished(self) -> None:
        self._bt40_running = False

    def _set_bt40_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.bt40_progress_bar.setDoubleValue_(percent)
        self.bt40_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_bt40_log(self, message: str) -> None:
        current = str(self.bt40_log_view.string() or "")
        current = current + message + "\n"
        self.bt40_log_view.setString_(current)
        self.bt40_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_bt40_log(self) -> None:
        text = str(self.bt40_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)

    def _choose_pnd2_folder(self) -> None:
        selected = _pick_folder()
        if not selected:
            return
        self.pnd2_folder_field.setStringValue_(selected)
        self._load_pnd2_folder()

    def _load_pnd2_folder(self) -> None:
        folder = Path(str(self.pnd2_folder_field.stringValue() or "")).expanduser()
        self.pnd2_pdf_files = Pp30FolderService.list_pdfs(folder)
        if self.pnd2_pdf_files:
            self.pnd2_folder_summary_field.setStringValue_(
                UI_TEXT["pp30_pdf_total"].format(count=len(self.pnd2_pdf_files))
            )
        else:
            self.pnd2_folder_summary_field.setStringValue_(UI_TEXT["pp30_pdf_summary_empty"])

    def _pnd2_form_config(self) -> Pnd2FormConfig:
        return Pnd2FormConfig(
            pdf_folder=Path(str(self.pnd2_folder_field.stringValue() or "")).expanduser(),
            pdf_files=list(self.pnd2_pdf_files),
        )

    def _start_pnd2(self) -> None:
        if self._pnd2_running:
            return
        self.app_config = self.app_config_service.load()
        self._load_pnd2_folder()
        errors = self.app_config.validate()
        errors.extend(self._pnd2_form_config().validate())
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = len(self.pnd2_pdf_files)
        self._set_pnd2_progress(0, total)
        self._append_pnd2_log(UI_TEXT["pp30_pdf_total"].format(count=total))
        form_config = self._pnd2_form_config()
        express_data_dir = self.app_config.express_data_dir
        self._pnd2_running = True
        threading.Thread(target=self._run_pnd2, args=(form_config, express_data_dir), daemon=True).start()

    def _run_pnd2(self, form_config: Pnd2FormConfig, express_data_dir: Path) -> None:
        try:
            Pnd2MatchRunService.run(
                form_config,
                express_data_dir,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_pnd2_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_pnd2_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._pnd2_finished)

    def _pnd2_finished(self) -> None:
        self._pnd2_running = False

    def _set_pnd2_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.pnd2_progress_bar.setDoubleValue_(percent)
        self.pnd2_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_pnd2_log(self, message: str) -> None:
        current = str(self.pnd2_log_view.string() or "")
        current += message + "\n"
        self.pnd2_log_view.setString_(current)
        self.pnd2_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_pnd2_log(self) -> None:
        text = str(self.pnd2_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)



    def _choose_income_folder(self) -> None:
        selected = _pick_folder()
        if not selected:
            return
        self.income_folder_field.setStringValue_(selected)
        self._load_income_folder()

    def _choose_income_report_folder(self) -> None:
        selected = _pick_folder()
        if selected:
            self.income_report_field.setStringValue_(selected)

    def _load_income_folder(self) -> None:
        folder = Path(str(self.income_folder_field.stringValue() or "")).expanduser()
        self.income_pdf_files = Pp30FolderService.list_pdfs(folder)
        if self.income_pdf_files:
            self.income_folder_summary_field.setStringValue_(
                UI_TEXT["pp30_pdf_total"].format(count=len(self.income_pdf_files))
            )
        else:
            self.income_folder_summary_field.setStringValue_(UI_TEXT["pp30_pdf_summary_empty"])

    def _income_form_config(self) -> IncomeFormConfig:
        return IncomeFormConfig(
            pdf_folder=Path(str(self.income_folder_field.stringValue() or "")).expanduser(),
            start_date=format_express_pv_date(str(self.income_start_field.stringValue() or "")),
            pdf_files=list(self.income_pdf_files),
            lock=self._income_lock,
            report_folder=Path(str(self.income_report_field.stringValue() or "").strip()),
        )

    def _start_income(self) -> None:
        if self._income_running:
            return
        self.app_config = self.app_config_service.load()
        self._load_income_folder()
        errors = self.app_config.validate()
        errors.extend(self._income_form_config().validate())
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        total = len(self.income_pdf_files)
        self._set_income_progress(0, total)
        form_config = self._income_form_config()
        self._append_income_log(UI_TEXT["pp30_pdf_total"].format(count=total))
        express_data_dir = self.app_config.express_data_dir
        self._income_running = True
        threading.Thread(target=self._run_income, args=(form_config, express_data_dir), daemon=True).start()

    def _run_income(self, form_config: IncomeFormConfig, express_data_dir: Path) -> None:
        try:
            IncomeMatchRunService.run(
                form_config,
                express_data_dir,
                on_status=lambda message: AppHelper.callAfter(lambda m=message: self._append_income_log(m)),
                on_progress=lambda done, total: AppHelper.callAfter(
                    lambda d=done, t=total: self._set_income_progress(d, t)
                ),
            )
        except ValueError as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        except Exception as exc:
            AppHelper.callAfter(lambda text=str(exc): _alert(UI_TEXT["app_title"], text))
        finally:
            AppHelper.callAfter(self._income_finished)

    def _income_finished(self) -> None:
        self._income_running = False

    def _set_income_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.income_progress_bar.setDoubleValue_(percent)
        self.income_progress_field.setStringValue_(
            UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent)
        )

    def _append_income_log(self, message: str) -> None:
        current = str(self.income_log_view.string() or "")
        current += message + "\n"
        self.income_log_view.setString_(current)
        self.income_log_view.scrollRangeToVisible_((len(current), 0))

    def _copy_income_log(self) -> None:
        text = str(self.income_log_view.string() or "")
        if not text.strip():
            return
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(text, NSPasteboardTypeString)

    def _save_config(self) -> None:
        config = AppConfig(
            express_data_dir=Path(str(self.express_data_dir_field.stringValue() or "")).expanduser()
        )
        errors = config.validate()
        if errors:
            _alert(UI_TEXT["app_title"], "\n".join(errors))
            return
        self.app_config_service.save(config)
        self.app_config = config
        count = len(ExpressShopIndexService().write_from_dir(config.express_data_dir))
        self._refresh_config_fields()
        if count:
            _alert(UI_TEXT["app_title"], UI_TEXT["express_data_dir_saved"].format(count=count))
        else:
            _alert(UI_TEXT["app_title"], UI_TEXT["express_data_dir_none"])

    def _refresh_config_fields(self) -> None:
        path = str(self.app_config.express_data_dir).strip()
        self.express_data_dir_field.setStringValue_(path)
        if not path:
            self.express_data_summary_field.setStringValue_(UI_TEXT["express_data_dir_empty"])
            return
        count = ExpressShopIndexService().count()
        self.express_data_summary_field.setStringValue_(
            UI_TEXT["express_data_dir_saved"].format(count=count)
            if count
            else UI_TEXT["express_data_dir_none"]
        )

    def _show_page(self, page_route: str) -> None:
        self._current_page = page_route
        self._menu_view.setHidden_(page_route != PAGE_MENU)
        self._config_view.setHidden_(page_route != PAGE_CONFIG)
        self._pp30_view.setHidden_(page_route != PAGE_PP30)
        self._ka_tam_view.setHidden_(page_route != PAGE_KA_TAM)
        self._pnd30_view.setHidden_(page_route != PAGE_PND30)
        self._pnd3_view.setHidden_(page_route != PAGE_PND3)
        self._pnd1_view.setHidden_(page_route != PAGE_PND1)
        self._pnd2_view.setHidden_(page_route != PAGE_PND2)
        self._bt40_view.setHidden_(page_route != PAGE_BT40)
        self._sso_view.setHidden_(page_route != PAGE_SSO)
        self._wcf_view.setHidden_(page_route != PAGE_WCF)
        self._payroll_view.setHidden_(page_route != PAGE_PAYROLL)
        self._income_view.setHidden_(page_route != PAGE_INCOME)
        heights = {
            PAGE_MENU: MENU_WIN_H,
            PAGE_CONFIG: CONFIG_WIN_H,
            PAGE_PP30: PP30_WIN_H,
            PAGE_KA_TAM: KA_TAM_WIN_H,
            PAGE_PND30: PND30_WIN_H,
            PAGE_PND3: PND3_WIN_H,
            PAGE_PND1: PND1_WIN_H,
            PAGE_PND2: PND2_WIN_H,
            PAGE_BT40: BT40_WIN_H,
            PAGE_SSO: SSO_WIN_H,
            PAGE_WCF: WCF_WIN_H,
            PAGE_PAYROLL: PAYROLL_WIN_H,
            PAGE_INCOME: INCOME_WIN_H,
        }
        height = heights.get(page_route, MENU_WIN_H)
        self.window.setContentSize_((WIN_W, height))
        self._root.setFrame_(NSMakeRect(0, 0, WIN_W, height))
        if page_route == PAGE_MENU:
            self._menu_view.setFrame_(NSMakeRect(0, 0, WIN_W, height))
            self._menu_scroll.setFrame_(NSMakeRect(24, 80, WIN_W - 48, height - 96))
        if page_route == PAGE_CONFIG:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['config_title']} v{__version__}")
            self._refresh_config_fields()
        elif page_route == PAGE_PP30:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_pp30']} v{__version__}")
        elif page_route == PAGE_KA_TAM:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_ka_tam']} v{__version__}")
        elif page_route == PAGE_PND30:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_pnd30']} v{__version__}")
        elif page_route == PAGE_PND3:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_pnd3']} v{__version__}")
        elif page_route == PAGE_PND1:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_pnd1']} v{__version__}")
        elif page_route == PAGE_PND2:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_pnd2']} v{__version__}")
        elif page_route == PAGE_BT40:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_bt40']} v{__version__}")
        elif page_route == PAGE_SSO:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_sso']} v{__version__}")
        elif page_route == PAGE_WCF:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_wcf']} v{__version__}")
        elif page_route == PAGE_PAYROLL:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_payroll']} v{__version__}")
        elif page_route == PAGE_INCOME:
            self.window.setTitle_(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_income']} v{__version__}")
        else:
            self.window.setTitle_(f"{UI_TEXT['app_title']} v{__version__}")

    def _on_close(self) -> None:
        NSApp.terminate_(None)

    def run(self) -> None:
        NSApp.activateIgnoringOtherApps_(True)
        AppHelper.runEventLoop()


def _pick_folder() -> str:
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(False)
    panel.setCanChooseDirectories_(True)
    panel.setAllowsMultipleSelection_(False)
    if panel.runModal() != 1:
        return ""
    urls = panel.URLs()
    if not urls:
        return ""
    return str(urls[0].path())


def _pick_file(extensions: tuple[str, ...]) -> str:
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(True)
    panel.setCanChooseDirectories_(False)
    panel.setAllowsMultipleSelection_(False)
    panel.setAllowedFileTypes_(list(extensions))
    if panel.runModal() != 1:
        return ""
    urls = panel.URLs()
    if not urls:
        return ""
    return str(urls[0].path())


def _static_label(parent, text: str, x, y, w, h, *, size: float = 13, bold: bool = False, gray: bool = False):
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


def _radio(parent, title: str, x, y, w, h, target: _CallbackTarget):
    button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    button.setButtonType_(NSButtonTypeRadio)
    button.setTitle_(title)
    button.setFont_(NSFont.systemFontOfSize_(13))
    button.setTarget_(target)
    button.setAction_("invoke:")
    parent.addSubview_(button)
    return button


def _button(parent, title: str, x, y, w, h, target: _CallbackTarget, *, font_size: float = 13, bezel=NSBezelStyleRegularSquare):
    button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    button.setBezelStyle_(bezel)
    button.setTitle_(title)
    button.setFont_(NSFont.systemFontOfSize_(font_size))
    button.setTarget_(target)
    button.setAction_("invoke:")
    parent.addSubview_(button)
    return button


def _box(parent, title: str, x, y, w, h):
    box = NSBox.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    if title:
        box.setTitle_(title)
    else:
        box.setTitlePosition_(0)
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

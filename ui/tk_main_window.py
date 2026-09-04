from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from constants.date_utils import default_work_date, format_express_pv_date
from constants.routes import (
    EXCEL_OPEN_EXTENSIONS,
    PAGE_KA_TAM,
    PAGE_MENU,
    PAGE_PP30,
    TOPIC_PAYMENT_JOURNAL,
    UI_TEXT,
)
from constants.topic_menu import TOPIC_MENU_ITEMS
from constants.version import __version__
from models.ka_tam_row import KaTamRow
from models.pp30_form_config import Pp30FormConfig
from models.run_config import ExcelSheetSummary, RunConfig
from models.topic_menu_item import TopicMenuItem
from services.automation_service import AutomationService
from services.excel_service import ExcelService
from services.hotkey_service import HotkeyService
from services.pp30_folder_service import Pp30FolderService
from ui.app_icon import apply_window_icon, load_title_photo
from ui.entry_excel_paste import bind_excel_cell_paste

WIN_W = 560
MENU_WIN_H = 500
KA_TAM_WIN_H = 620
PP30_WIN_H = 600


class MainWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(f"{UI_TEXT['app_title']} v{__version__}")
        self.root.geometry(f"{WIN_W}x{MENU_WIN_H}")
        self.root.resizable(False, False)
        self._set_window_icon()

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

        defaults = self.automation_service.default_settings
        initial_pv_date = format_express_pv_date(
            str(defaults.get("pv_date", "")).strip() or default_work_date()
        )
        initial_start_from_no = str(defaults.get("start_from_no", 1) or 1).strip() or "1"
        self.excel_path = tk.StringVar(value="")
        self.pv_date = tk.StringVar(value=initial_pv_date)
        self.start_from_no = tk.StringVar(value=initial_start_from_no)
        self.description = tk.StringVar(value="")
        self.tax_payer_id = tk.StringVar(value="")
        self.status_text = tk.StringVar(value=UI_TEXT["ready"])
        self.progress_text = tk.StringVar(value="0 / 0")
        self.excel_summary = tk.StringVar(value=UI_TEXT["excel_summary_empty"])
        self.pp30_pdf_folder = tk.StringVar(value="")
        self.pp30_excel_path = tk.StringVar(value="")
        self.pp30_jv_date = tk.StringVar(value=initial_pv_date)
        self.pp30_jv_description = tk.StringVar(value="")
        self.pp30_pv_description = tk.StringVar(value="")
        self.pp30_report_dir = tk.StringVar(
            value=str(defaults.get("report_output_dir", "") or "").strip()
        )
        self.pp30_pdf_summary = tk.StringVar(value=UI_TEXT["pp30_pdf_summary_empty"])
        self.pp30_excel_summary = tk.StringVar(value=UI_TEXT["excel_summary_empty"])
        self.pp30_progress_text = tk.StringVar(value="0 / 0")
        self.pp30_pdf_files: list[Path] = []
        self.sheet_summaries: list[ExcelSheetSummary] = []
        self.sheet_rows: dict[str, list[KaTamRow]] = {}
        self._current_page = PAGE_MENU

        self._build_ui()
        self._bind_shortcuts()
        self._show_page(PAGE_MENU)
        self._load_excel()

    def _build_ui(self) -> None:
        self.menu_frame = ttk.Frame(self.root)
        self.ka_tam_frame = ttk.Frame(self.root)
        self.pp30_frame = ttk.Frame(self.root)
        self._build_menu_page(self.menu_frame)
        self._build_ka_tam_page(self.ka_tam_frame)
        self._build_pp30_page(self.pp30_frame)

    def _build_menu_page(self, page: ttk.Frame) -> None:
        header = ttk.Frame(page)
        header.pack(fill="x", padx=16, pady=(20, 0))
        self._menu_title_icon = load_title_photo(44)
        if self._menu_title_icon is not None:
            ttk.Label(header, image=self._menu_title_icon).pack(side="left", padx=(0, 10))
        ttk.Label(
            header,
            text=f"{UI_TEXT['app_title']} v{__version__}",
            font=("Tahoma", 13, "bold"),
        ).pack(side="left")

        ttk.Label(page, text=UI_TEXT["menu_title"], font=("Tahoma", 12, "bold")).pack(
            anchor="w", padx=20, pady=(24, 4)
        )
        ttk.Label(page, text=UI_TEXT["menu_hint"], foreground="#555555").pack(
            anchor="w", padx=20, pady=(0, 16)
        )

        for item in TOPIC_MENU_ITEMS:
            ttk.Button(
                page,
                text=item.title,
                command=lambda selected=item: self._open_topic(selected),
            ).pack(fill="x", padx=24, pady=(0, 4), ipady=16)
            ttk.Label(page, text=item.hint, foreground="#777777", font=("Tahoma", 9)).pack(
                anchor="w", padx=28, pady=(0, 12)
            )

    def _build_ka_tam_page(self, page: ttk.Frame) -> None:
        padding = {"padx": 12, "pady": 6}

        header = ttk.Frame(page)
        header.pack(fill="x", padx=12, pady=(10, 0))
        ttk.Button(header, text=f"← {UI_TEXT['back_to_menu']}", command=self._back_to_menu).pack(
            side="left"
        )
        self._title_icon = load_title_photo(44)
        if self._title_icon is not None:
            ttk.Label(header, image=self._title_icon).pack(side="left", padx=(8, 8))
        ttk.Label(
            header,
            text=UI_TEXT["menu_ka_tam"],
            font=("Tahoma", 12, "bold"),
        ).pack(side="left")

        form_frame = ttk.LabelFrame(page, text=UI_TEXT["settings_frame"])
        form_frame.pack(fill="x", **padding)

        ttk.Label(form_frame, text=UI_TEXT["excel_file"]).grid(row=0, column=0, sticky="w")
        self.excel_path_entry = ttk.Entry(form_frame, textvariable=self.excel_path, width=48)
        self.excel_path_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(form_frame, text=UI_TEXT["choose_file"], command=self._choose_excel).grid(row=0, column=2)

        ttk.Label(form_frame, textvariable=self.excel_summary, wraplength=500).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )

        ttk.Label(form_frame, text=UI_TEXT["pv_date"]).grid(row=2, column=0, sticky="w")
        self.pv_date_entry = ttk.Entry(form_frame, textvariable=self.pv_date, width=20)
        self.pv_date_entry.grid(row=2, column=1, sticky="w")
        self.pv_date_entry.bind("<FocusOut>", self._format_pv_date)
        ttk.Label(form_frame, text=UI_TEXT["pv_date_hint"], wraplength=500, foreground="#555555").grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(2, 0)
        )

        ttk.Label(form_frame, text=UI_TEXT["start_from_no"]).grid(row=4, column=0, sticky="w")
        self.start_from_no_entry = ttk.Entry(form_frame, textvariable=self.start_from_no, width=8)
        self.start_from_no_entry.grid(row=4, column=1, sticky="w")
        ttk.Label(form_frame, text=UI_TEXT["start_from_no_hint"], wraplength=500, foreground="#555555").grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(2, 0)
        )

        ttk.Label(form_frame, text=UI_TEXT["description"]).grid(row=6, column=0, sticky="nw")
        self.description_entry = ttk.Entry(form_frame, textvariable=self.description, width=48)
        self.description_entry.grid(row=6, column=1, columnspan=2, sticky="ew")
        ttk.Label(form_frame, text=UI_TEXT["description_hint"], wraplength=500, foreground="#555555").grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(2, 0)
        )

        ttk.Label(form_frame, text=UI_TEXT["tax_payer_id"]).grid(row=8, column=0, sticky="nw")
        self.tax_payer_id_entry = ttk.Entry(form_frame, textvariable=self.tax_payer_id, width=48)
        self.tax_payer_id_entry.grid(row=8, column=1, columnspan=2, sticky="ew")
        ttk.Label(form_frame, text=UI_TEXT["tax_payer_id_hint"], wraplength=500, foreground="#555555").grid(
            row=9, column=0, columnspan=3, sticky="w", pady=(2, 0)
        )
        form_frame.columnconfigure(1, weight=1)
        bind_excel_cell_paste(
            [
                self.excel_path_entry,
                self.pv_date_entry,
                self.start_from_no_entry,
                self.description_entry,
                self.tax_payer_id_entry,
            ],
        )

        action_frame = ttk.Frame(page)
        action_frame.pack(fill="x", **padding)
        ttk.Button(action_frame, text=f"▶ {UI_TEXT['start']}", command=self._start).pack(side="left", padx=4)
        self.stop_button = ttk.Button(
            action_frame,
            text=f"■ {UI_TEXT['stop'].format(hotkey=self.hotkey_label)}",
            command=self._stop,
        )
        self.stop_button.pack(side="left", padx=4)

        status_frame = ttk.LabelFrame(page, text=UI_TEXT["status_frame"])
        status_frame.pack(fill="both", expand=True, **padding)
        ttk.Label(status_frame, textvariable=self.progress_text).pack(anchor="w", padx=8, pady=4)

        log_toolbar = ttk.Frame(status_frame)
        log_toolbar.pack(fill="x", padx=8, pady=(0, 4))
        ttk.Button(log_toolbar, text=UI_TEXT["copy_log"], command=self._copy_all_log).pack(side="right")

        log_container = ttk.Frame(status_frame)
        log_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        log_container.rowconfigure(0, weight=1)
        log_container.columnconfigure(0, weight=1)

        self.log_box = tk.Text(
            log_container,
            height=12,
            wrap="word",
            exportselection=True,
            bg="#ffffff",
            fg="#000000",
            insertwidth=0,
            cursor="arrow",
        )
        log_scroll = ttk.Scrollbar(log_container, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_scroll.set)
        self.log_box.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")
        self._setup_log_box_bindings(self.log_box)

        welcome = UI_TEXT["welcome_log"]
        self._write_log(welcome + "\n", trim=False)
        self._set_log_readonly(True)

    def _build_pp30_page(self, page: ttk.Frame) -> None:
        padding = {"padx": 12, "pady": 6}

        header = ttk.Frame(page)
        header.pack(fill="x", padx=12, pady=(10, 0))
        ttk.Button(header, text=f"← {UI_TEXT['back_to_menu']}", command=self._back_to_menu).pack(
            side="left"
        )
        ttk.Label(
            header,
            text=UI_TEXT["menu_pp30"],
            font=("Tahoma", 12, "bold"),
        ).pack(side="left", padx=(12, 0))

        form_frame = ttk.LabelFrame(page, text=UI_TEXT["settings_frame"])
        form_frame.pack(fill="x", **padding)

        ttk.Label(form_frame, text=UI_TEXT["pp30_pdf_folder"]).grid(row=0, column=0, sticky="w")
        self.pp30_folder_entry = ttk.Entry(form_frame, textvariable=self.pp30_pdf_folder, width=48)
        self.pp30_folder_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(form_frame, text=UI_TEXT["choose_folder"], command=self._choose_pp30_folder).grid(
            row=0, column=2
        )
        ttk.Label(form_frame, textvariable=self.pp30_pdf_summary, wraplength=500).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(2, 0)
        )

        ttk.Label(form_frame, text=UI_TEXT["excel_file"]).grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.pp30_excel_path_entry = ttk.Entry(form_frame, textvariable=self.pp30_excel_path, width=48)
        self.pp30_excel_path_entry.grid(row=2, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(form_frame, text=UI_TEXT["choose_file"], command=self._choose_pp30_excel).grid(
            row=2, column=2, pady=(8, 0)
        )
        ttk.Label(form_frame, textvariable=self.pp30_excel_summary, wraplength=500).grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(2, 0)
        )

        ttk.Label(form_frame, text=UI_TEXT["pp30_jv_date"]).grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.pp30_jv_date_entry = ttk.Entry(form_frame, textvariable=self.pp30_jv_date, width=20)
        self.pp30_jv_date_entry.grid(row=4, column=1, sticky="w", pady=(8, 0))
        self.pp30_jv_date_entry.bind("<FocusOut>", self._format_pp30_jv_date)

        ttk.Label(form_frame, text=UI_TEXT["pp30_jv_description"]).grid(row=5, column=0, sticky="nw", pady=(8, 0))
        self.pp30_jv_description_entry = ttk.Entry(
            form_frame, textvariable=self.pp30_jv_description, width=48
        )
        self.pp30_jv_description_entry.grid(row=5, column=1, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Label(form_frame, text=UI_TEXT["pp30_pv_description"]).grid(row=6, column=0, sticky="nw", pady=(8, 0))
        self.pp30_pv_description_entry = ttk.Entry(
            form_frame, textvariable=self.pp30_pv_description, width=48
        )
        self.pp30_pv_description_entry.grid(row=6, column=1, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Label(form_frame, text=UI_TEXT["report_output_dir"]).grid(row=7, column=0, sticky="w", pady=(8, 0))
        self.pp30_report_dir_entry = ttk.Entry(form_frame, textvariable=self.pp30_report_dir, width=48)
        self.pp30_report_dir_entry.grid(row=7, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(form_frame, text=UI_TEXT["choose_folder"], command=self._choose_pp30_report_dir).grid(
            row=7, column=2, pady=(8, 0)
        )
        form_frame.columnconfigure(1, weight=1)
        bind_excel_cell_paste(
            [
                self.pp30_folder_entry,
                self.pp30_excel_path_entry,
                self.pp30_jv_date_entry,
                self.pp30_jv_description_entry,
                self.pp30_pv_description_entry,
                self.pp30_report_dir_entry,
            ],
        )

        action_frame = ttk.Frame(page)
        action_frame.pack(fill="x", **padding)
        ttk.Button(action_frame, text=f"▶ {UI_TEXT['start']}", command=self._start).pack(side="left", padx=4)
        self.pp30_stop_button = ttk.Button(
            action_frame,
            text=f"■ {UI_TEXT['stop'].format(hotkey=self.hotkey_label)}",
            command=self._stop,
        )
        self.pp30_stop_button.pack(side="left", padx=4)

        status_frame = ttk.LabelFrame(page, text=UI_TEXT["status_frame"])
        status_frame.pack(fill="both", expand=True, **padding)
        ttk.Label(status_frame, textvariable=self.pp30_progress_text).pack(anchor="w", padx=8, pady=4)

        log_toolbar = ttk.Frame(status_frame)
        log_toolbar.pack(fill="x", padx=8, pady=(0, 4))
        ttk.Button(log_toolbar, text=UI_TEXT["copy_log"], command=self._copy_all_log).pack(side="right")

        log_container = ttk.Frame(status_frame)
        log_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        log_container.rowconfigure(0, weight=1)
        log_container.columnconfigure(0, weight=1)

        self.pp30_log_box = tk.Text(
            log_container,
            height=8,
            wrap="word",
            exportselection=True,
            bg="#ffffff",
            fg="#000000",
            insertwidth=0,
            cursor="arrow",
        )
        log_scroll = ttk.Scrollbar(log_container, orient="vertical", command=self.pp30_log_box.yview)
        self.pp30_log_box.configure(yscrollcommand=log_scroll.set)
        self.pp30_log_box.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")
        self._setup_log_box_bindings(self.pp30_log_box)
        self.pp30_log_box.insert("end", UI_TEXT["pp30_welcome_log"] + "\n")
        self.pp30_log_box.config(state=tk.DISABLED)

    def _open_topic(self, item: TopicMenuItem) -> None:
        if not item.enabled:
            messagebox.showinfo(UI_TEXT["app_title"], UI_TEXT["menu_unavailable"])
            return
        self._show_page(item.page_route)

    def _back_to_menu(self) -> None:
        if self.is_running:
            return
        self._show_page(PAGE_MENU)

    def _show_page(self, page_route: str) -> None:
        if self.is_running and page_route == PAGE_MENU:
            return
        self._current_page = page_route
        self.menu_frame.pack_forget()
        self.ka_tam_frame.pack_forget()
        self.pp30_frame.pack_forget()
        heights = {PAGE_MENU: MENU_WIN_H, PAGE_KA_TAM: KA_TAM_WIN_H, PAGE_PP30: PP30_WIN_H}
        height = heights.get(page_route, MENU_WIN_H)
        self.root.geometry(f"{WIN_W}x{height}")
        if page_route == PAGE_MENU:
            self.root.title(f"{UI_TEXT['app_title']} v{__version__}")
            self.menu_frame.pack(fill="both", expand=True)
        elif page_route == PAGE_KA_TAM:
            self.root.title(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_ka_tam']} v{__version__}")
            self.ka_tam_frame.pack(fill="both", expand=True)
        elif page_route == PAGE_PP30:
            self.root.title(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_pp30']} v{__version__}")
            self.pp30_frame.pack(fill="both", expand=True)

    def _bind_shortcuts(self) -> None:
        self.hotkey_service.bind_tk_shortcuts(self.root, self._stop)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_window_icon(self) -> None:
        apply_window_icon(self.root)

    def _on_close(self) -> None:
        if self.is_running:
            self._stop()
        self.hotkey_service.stop_listening()
        self.root.destroy()

    def _load_excel(self) -> None:
        raw_path = self.excel_path.get().strip()
        if not raw_path:
            self.sheet_summaries = []
            self.sheet_rows = {}
            self.excel_summary.set(UI_TEXT["excel_summary_empty"])
            return

        excel_path = Path(raw_path).expanduser()
        if not excel_path.exists():
            self.sheet_summaries = []
            self.sheet_rows = {}
            self.excel_summary.set(UI_TEXT["excel_summary_empty"])
            return

        try:
            self.sheet_summaries, self.sheet_rows = ExcelService.load_workbook(excel_path)
        except Exception as exc:
            self.sheet_summaries = []
            self.sheet_rows = {}
            self.excel_summary.set(str(exc))
            return

        if not self.sheet_summaries:
            self.excel_summary.set(UI_TEXT["no_excel_data"])
            self._append_log(UI_TEXT["no_excel_data"])
            return

        total_rows = sum(summary.row_count for summary in self.sheet_summaries)
        self.excel_summary.set(UI_TEXT["excel_total"].format(rows=total_rows))

        self._append_log(UI_TEXT["excel_loaded"].format(path=excel_path.name))
        self._append_log(UI_TEXT["excel_total"].format(rows=total_rows))

    def _parse_start_from_no(self) -> int:
        raw = self.start_from_no.get().strip()
        if not raw:
            return 1
        try:
            return int(raw)
        except ValueError:
            return 0

    def _format_pv_date(self, _event=None) -> None:
        formatted = format_express_pv_date(self.pv_date.get())
        if formatted:
            self.pv_date.set(formatted)

    def _choose_excel(self) -> None:
        excel_types = " ".join(f"*.{ext}" for ext in EXCEL_OPEN_EXTENSIONS)
        selected = filedialog.askopenfilename(
            title=UI_TEXT["choose_file"],
            filetypes=[("Excel", excel_types), ("All files", "*.*")],
        )
        if selected:
            self.excel_path.set(selected)
            self._load_excel()

    def _choose_pp30_folder(self) -> None:
        selected = filedialog.askdirectory(title=UI_TEXT["choose_folder"])
        if selected:
            self.pp30_pdf_folder.set(selected)
            self._load_pp30_folder()

    def _choose_pp30_report_dir(self) -> None:
        selected = filedialog.askdirectory(title=UI_TEXT["choose_folder"])
        if selected:
            self.pp30_report_dir.set(selected)

    def _choose_pp30_excel(self) -> None:
        excel_types = " ".join(f"*.{ext}" for ext in EXCEL_OPEN_EXTENSIONS)
        selected = filedialog.askopenfilename(
            title=UI_TEXT["choose_file"],
            filetypes=[("Excel", excel_types), ("All files", "*.*")],
        )
        if selected:
            self.pp30_excel_path.set(selected)
            self._load_pp30_excel()

    def _load_pp30_folder(self) -> None:
        raw_path = self.pp30_pdf_folder.get().strip()
        if not raw_path:
            self.pp30_pdf_files = []
            self.pp30_pdf_summary.set(UI_TEXT["pp30_pdf_summary_empty"])
            return
        folder = Path(raw_path).expanduser()
        if not folder.exists() or not folder.is_dir():
            self.pp30_pdf_files = []
            self.pp30_pdf_summary.set(UI_TEXT["pp30_pdf_summary_empty"])
            return
        self.pp30_pdf_files = Pp30FolderService.list_pdfs(folder)
        self.pp30_pdf_summary.set(UI_TEXT["pp30_pdf_total"].format(count=len(self.pp30_pdf_files)))

    def _load_pp30_excel(self) -> None:
        raw_path = self.pp30_excel_path.get().strip()
        if not raw_path:
            self.pp30_excel_summary.set(UI_TEXT["excel_summary_empty"])
            return
        excel_path = Path(raw_path).expanduser()
        if not excel_path.exists():
            self.pp30_excel_summary.set(UI_TEXT["excel_summary_empty"])
            return
        self.pp30_excel_summary.set(UI_TEXT["excel_loaded"].format(path=excel_path.name))

    def _format_pp30_jv_date(self, _event=None) -> None:
        formatted = format_express_pv_date(self.pp30_jv_date.get())
        if formatted:
            self.pp30_jv_date.set(formatted)

    def _pp30_form_config(self) -> Pp30FormConfig:
        return Pp30FormConfig(
            pdf_folder=Path(self.pp30_pdf_folder.get().strip()).expanduser(),
            excel_path=Path(self.pp30_excel_path.get().strip()).expanduser(),
            jv_date=format_express_pv_date(self.pp30_jv_date.get()),
            jv_description=self.pp30_jv_description.get().strip(),
            pv_description=self.pp30_pv_description.get().strip(),
            report_output_dir=Path(self.pp30_report_dir.get().strip()).expanduser(),
            pdf_files=list(self.pp30_pdf_files),
        )

    def _start_pp30(self) -> None:
        self._load_pp30_folder()
        config = self._pp30_form_config()
        if config.jv_date:
            self.pp30_jv_date.set(config.jv_date)
        errors = config.validate()
        if errors:
            messagebox.showwarning("AutoKey", "\n".join(errors))
            return
        self._append_log(UI_TEXT["pp30_pdf_total"].format(count=len(config.pdf_files)))
        self._append_log(UI_TEXT["excel_loaded"].format(path=config.excel_path.name))
        if not messagebox.askyesno(
            UI_TEXT["confirm_title"],
            f"{UI_TEXT['pp30_confirm_message']}\n\nจะค้นหา {len(config.pdf_files)} ห้าง",
        ):
            return

        self.is_running = True
        self._total_rows = len(config.pdf_files)
        if self.clear_log_on_start:
            self._clear_log()
        self._append_log(UI_TEXT["cancel_hotkey_hint"].format(hotkey=self.hotkey_label))
        self.hotkey_service.start_listening(self._stop)
        if self.hide_on_start:
            self.root.withdraw()

        self.automation_service.run_pp30_async(
            form_config=config,
            on_status=self._set_status,
            on_progress=self._set_progress,
            on_step=self._set_step,
            on_finished=self._on_finished,
            verbose_log=self.verbose_log,
        )

    def _start(self) -> None:
        if self.is_running:
            return
        if self._current_page == PAGE_PP30:
            self._start_pp30()
            return
        if self._current_page != PAGE_KA_TAM:
            return

        if not self.sheet_summaries:
            self._load_excel()
        if not self.sheet_summaries:
            messagebox.showwarning("AutoKey", UI_TEXT["no_excel_loaded"])
            return

        pv_date = format_express_pv_date(self.pv_date.get())
        if pv_date:
            self.pv_date.set(pv_date)

        run_config = RunConfig(
            topic=TOPIC_PAYMENT_JOURNAL,
            excel_path=Path(self.excel_path.get()).expanduser(),
            pv_date=pv_date,
            description=self.description.get().strip(),
            tax_payer_id=self.tax_payer_id.get().strip(),
            start_from_no=self._parse_start_from_no(),
            sheet_summaries=self.sheet_summaries,
            sheet_rows=self.sheet_rows,
        )
        errors = run_config.validate()
        if errors:
            messagebox.showwarning("AutoKey", "\n".join(errors))
            return

        confirm_rows = run_config.planned_row_count()
        start_label = f"เริ่มที่ No. {run_config.start_from_no}"
        if not messagebox.askyesno(
            UI_TEXT["confirm_title"],
            f"{UI_TEXT['confirm_message']}\n\n{start_label} — จะทำ {confirm_rows} รายการ",
        ):
            return

        self.is_running = True
        self._total_rows = confirm_rows
        if self.clear_log_on_start:
            self._clear_log()
        self._append_log(UI_TEXT["cancel_hotkey_hint"].format(hotkey=self.hotkey_label))
        self.hotkey_service.start_listening(self._stop)
        if self.hide_on_start:
            self.root.withdraw()

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
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(200, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
            self._append_log(UI_TEXT["window_restored"])
        self._active_log_box().see("end")
        self.root.update_idletasks()

    def _cleanup_run(self) -> None:
        self.is_running = False
        self.hotkey_service.stop_listening()

    def _set_status(self, message: str) -> None:
        self.root.after(0, lambda: self._append_log(message))

    def _set_progress(self, current: int, total: int) -> None:
        progress = f"{current} / {total}"
        if self._current_page == PAGE_PP30:
            self.root.after(0, lambda: self.pp30_progress_text.set(progress))
            return
        self.root.after(0, lambda: self.progress_text.set(progress))

    def _set_step(self, step_index: int, step_label: str, detail: str) -> None:
        del step_index, step_label, detail
        # ขั้นตอน log แล้วใน _set_status จาก workflow._step — ไม่เขียนซ้ำ

    def _on_finished(self, success: bool, message: str) -> None:
        def update() -> None:
            self._cleanup_run()
            self._restore_window()
            self.status_text.set(message)
            self._append_log(message, trim=success)
            if success:
                messagebox.showinfo("AutoKey", message)
            else:
                messagebox.showerror("AutoKey — หยุดทำงาน", message)

        self.root.after(0, update)

    def _active_log_box(self) -> tk.Text:
        if self._current_page == PAGE_PP30:
            return self.pp30_log_box
        return self.log_box

    def _set_log_readonly(self, readonly: bool) -> None:
        self._active_log_box().config(state=tk.DISABLED if readonly else tk.NORMAL)

    def _write_log(self, text: str, *, trim: bool = True) -> None:
        log_box = self._active_log_box()
        was_disabled = str(log_box.cget("state")) == tk.DISABLED
        if was_disabled:
            self._set_log_readonly(False)
        log_box.insert("end", text)
        if trim:
            self._trim_log()
        log_box.see("end")
        if was_disabled or self.is_running:
            self._set_log_readonly(True)

    def _append_log(self, message: str, *, trim: bool = True) -> None:
        self._write_log(message + "\n", trim=trim)
        self.status_text.set(message)

    def _clear_log(self) -> None:
        log_box = self._active_log_box()
        self._set_log_readonly(False)
        log_box.delete("1.0", "end")
        self._set_log_readonly(True)

    def _trim_log(self) -> None:
        if self.is_running or self.log_max_lines <= 0:
            return
        log_box = self._active_log_box()
        line_count = int(log_box.index("end-1c").split(".")[0])
        if line_count <= self.log_max_lines:
            return
        overflow = line_count - self.log_max_lines
        self._set_log_readonly(False)
        log_box.delete("1.0", f"{overflow + 1}.0")
        self._set_log_readonly(True)

    def _setup_log_box_bindings(self, log_box: tk.Text) -> None:
        for sequence in (
            "<Command-c>",
            "<Control-c>",
            "<Command-C>",
            "<Control-C>",
        ):
            log_box.bind(sequence, self._copy_log_selection, add="+")
        for sequence in (
            "<Command-a>",
            "<Control-a>",
            "<Command-A>",
            "<Control-A>",
        ):
            log_box.bind(sequence, self._select_all_log, add="+")

        menu = tk.Menu(log_box, tearoff=0)
        menu.add_command(label=UI_TEXT["copy_log"], command=self._copy_log_selection)
        menu.add_command(label=UI_TEXT["select_all_log"], command=self._select_all_log)
        menu.add_command(label=UI_TEXT["copy_all_log"], command=self._copy_all_log)

        def show_menu(event: tk.Event) -> str:
            log_box.focus_set()
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
            return "break"

        log_box.bind("<Button-2>", show_menu, add="+")
        log_box.bind("<Button-3>", show_menu, add="+")
        log_box.bind("<Control-Button-1>", show_menu, add="+")

    def _with_log_edit(self, callback):
        log_box = self._active_log_box()
        was_disabled = str(log_box.cget("state")) == tk.DISABLED
        if was_disabled:
            self._set_log_readonly(False)
        try:
            return callback()
        finally:
            if was_disabled or self.is_running:
                self._set_log_readonly(True)

    def _copy_log_selection(self, _event: tk.Event | None = None) -> str:
        def copy() -> str:
            log_box = self._active_log_box()
            try:
                text = log_box.get(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                return "break"
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            return "break"

        return self._with_log_edit(copy)

    def _select_all_log(self, _event: tk.Event | None = None) -> str:
        def select_all() -> str:
            log_box = self._active_log_box()
            log_box.tag_add(tk.SEL, "1.0", "end-1c")
            log_box.mark_set(tk.INSERT, "1.0")
            log_box.see(tk.INSERT)
            return "break"

        return self._with_log_edit(select_all)

    def _copy_all_log(self) -> None:
        def copy_all() -> None:
            text = self._active_log_box().get("1.0", "end-1c")
            if not text.strip():
                return
            self.root.clipboard_clear()
            self.root.clipboard_append(text)

        self._with_log_edit(copy_all)

    def run(self) -> None:
        self.root.mainloop()

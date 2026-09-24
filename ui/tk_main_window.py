from __future__ import annotations

from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from constants.date_utils import format_express_pv_date, is_complete_express_date
from constants.routes import (
    MENU_BUTTON_IPADY,
    PAGE_CONFIG,
    PAGE_MENU,
    PAGE_PP30,
    PP30_MODE_NORMAL,
    PP30_MODE_SPECIAL,
    UI_TEXT,
)
from constants.topic_menu import TOPIC_MENU_ITEMS
from constants.version import __version__
from models.app_config import AppConfig
from models.pp30_form_config import Pp30FormConfig
from models.pp30_run_mode import Pp30RunMode
from models.topic_menu_item import TopicMenuItem
from services.app_config_service import AppConfigService
from services.express_shop_index_service import ExpressShopIndexService
from services.pp30_folder_service import Pp30FolderService
from services.pp30_match_run_service import Pp30MatchRunService
from ui.app_icon import apply_window_icon, load_title_photo

WIN_W = 560
MENU_WIN_H = 540
CONFIG_WIN_H = 320
PP30_WIN_H = 660


class MainWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(f"{UI_TEXT['app_title']} v{__version__}")
        self.root.geometry(f"{WIN_W}x{MENU_WIN_H}")
        self.root.resizable(False, False)
        apply_window_icon(self.root)
        self.app_config_service = AppConfigService()
        self.app_config = self.app_config_service.load()
        self.express_data_dir = tk.StringVar(value=str(self.app_config.express_data_dir).strip())
        self.express_data_summary = tk.StringVar(value=UI_TEXT["express_data_dir_empty"])
        self.pp30_run_mode = tk.StringVar(value=PP30_MODE_NORMAL)
        self.pp30_pdf_folder = tk.StringVar(value="")
        self.pp30_pdf_summary = tk.StringVar(value=UI_TEXT["pp30_pdf_summary_empty"])
        self.pp30_jv_date = tk.StringVar(value="")
        self.pp30_jv_description = tk.StringVar(value="")
        self.pp30_pv_description = tk.StringVar(value="")
        self.pp30_progress_text = tk.StringVar(value=UI_TEXT["pp30_progress"].format(done=0, total=0, percent=0))
        self.pp30_pdf_files: list[Path] = []
        self._pp30_running = False
        self._current_page = PAGE_MENU
        self._build_ui()
        self._show_page(PAGE_MENU)

    def _build_ui(self) -> None:
        self.menu_frame = ttk.Frame(self.root)
        self.config_frame = ttk.Frame(self.root)
        self.pp30_frame = ttk.Frame(self.root)
        self._build_menu_page(self.menu_frame)
        self._build_config_page(self.config_frame)
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
        ttk.Button(
            header,
            text=UI_TEXT["menu_config"],
            command=lambda: self._show_page(PAGE_CONFIG),
        ).pack(side="right")

        ttk.Label(page, text=UI_TEXT["menu_title"], font=("Tahoma", 12, "bold")).pack(
            anchor="w", padx=20, pady=(24, 16)
        )

        for item in TOPIC_MENU_ITEMS:
            ttk.Button(
                page,
                text=item.title,
                command=lambda selected=item: self._open_topic(selected),
            ).pack(fill="x", padx=24, pady=(0, 12), ipady=MENU_BUTTON_IPADY)

    def _build_config_page(self, page: ttk.Frame) -> None:
        header = ttk.Frame(page)
        header.pack(fill="x", padx=12, pady=(10, 0))
        ttk.Button(header, text=f"← {UI_TEXT['back_to_menu']}", command=lambda: self._show_page(PAGE_MENU)).pack(
            side="left"
        )
        ttk.Label(header, text=UI_TEXT["config_title"], font=("Tahoma", 12, "bold")).pack(side="left", padx=12)

        form = ttk.Frame(page)
        form.pack(fill="x", padx=20, pady=(24, 0))
        ttk.Label(form, text=UI_TEXT["express_data_dir"]).grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.express_data_dir, width=42).grid(row=0, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(form, text=UI_TEXT["choose_folder"], command=self._choose_express_data_dir).grid(row=0, column=2)
        ttk.Label(form, text=UI_TEXT["express_data_dir_hint"], foreground="#555555").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(6, 0)
        )
        ttk.Label(form, textvariable=self.express_data_summary, wraplength=500).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )
        form.columnconfigure(1, weight=1)
        ttk.Button(page, text=UI_TEXT["save"], command=self._save_config).pack(anchor="w", padx=20, pady=16)

    def _build_pp30_page(self, page: ttk.Frame) -> None:
        header = ttk.Frame(page)
        header.pack(fill="x", padx=12, pady=(10, 0))
        ttk.Button(header, text=f"← {UI_TEXT['back_to_menu']}", command=lambda: self._show_page(PAGE_MENU)).pack(
            side="left"
        )
        ttk.Label(header, text=UI_TEXT["menu_pp30"], font=("Tahoma", 12, "bold")).pack(side="left", padx=12)

        form = ttk.Frame(page)
        form.pack(fill="x", padx=20, pady=(16, 0))
        ttk.Label(form, text=UI_TEXT["pp30_run_mode"]).grid(row=0, column=0, sticky="w")
        mode_row = ttk.Frame(form)
        mode_row.grid(row=0, column=1, columnspan=2, sticky="w")
        ttk.Radiobutton(
            mode_row, text=UI_TEXT["pp30_mode_normal"], variable=self.pp30_run_mode, value=PP30_MODE_NORMAL
        ).pack(side="left")
        ttk.Radiobutton(
            mode_row, text=UI_TEXT["pp30_mode_special"], variable=self.pp30_run_mode, value=PP30_MODE_SPECIAL
        ).pack(side="left", padx=(16, 0))

        ttk.Label(form, text=UI_TEXT["pp30_pdf_folder"]).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(form, textvariable=self.pp30_pdf_folder, width=42).grid(
            row=1, column=1, sticky="ew", padx=(8, 8), pady=(8, 0)
        )
        ttk.Button(form, text=UI_TEXT["choose_folder"], command=self._choose_pp30_folder).grid(
            row=1, column=2, pady=(8, 0)
        )
        ttk.Label(form, textvariable=self.pp30_pdf_summary, wraplength=500).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )
        ttk.Label(form, text=UI_TEXT["pp30_jv_date"]).grid(row=3, column=0, sticky="w", pady=(8, 0))
        jv_date_entry = ttk.Entry(form, textvariable=self.pp30_jv_date, width=14)
        jv_date_entry.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        jv_date_entry.bind("<FocusOut>", self._format_pp30_jv_date)
        ttk.Label(form, text=UI_TEXT["pp30_jv_description"]).grid(row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(form, textvariable=self.pp30_jv_description, width=42).grid(
            row=4, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=(8, 0)
        )
        ttk.Label(form, text=UI_TEXT["pp30_pv_description"]).grid(row=5, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(form, textvariable=self.pp30_pv_description, width=42).grid(
            row=5, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=(8, 0)
        )
        form.columnconfigure(1, weight=1)

        ttk.Button(page, text=f"▶ {UI_TEXT['start']}", command=self._start_pp30).pack(anchor="w", padx=20, pady=12)

        status = ttk.LabelFrame(page, text=UI_TEXT["status_frame"])
        status.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        progress_row = ttk.Frame(status)
        progress_row.pack(fill="x", padx=8, pady=(8, 4))
        self.pp30_progress = ttk.Progressbar(progress_row, maximum=100)
        self.pp30_progress.pack(side="left", fill="x", expand=True)
        ttk.Label(progress_row, textvariable=self.pp30_progress_text, width=16).pack(side="left", padx=(8, 0))
        ttk.Button(status, text=UI_TEXT["copy_log"], command=self._copy_pp30_log).pack(anchor="e", padx=8)
        log_row = ttk.Frame(status)
        log_row.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        log_row.rowconfigure(0, weight=1)
        log_row.columnconfigure(0, weight=1)
        self.pp30_log_box = tk.Text(log_row, height=10, wrap="word")
        scroll = ttk.Scrollbar(log_row, orient="vertical", command=self.pp30_log_box.yview)
        self.pp30_log_box.configure(yscrollcommand=scroll.set)
        self.pp30_log_box.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.pp30_log_box.insert("end", UI_TEXT["pp30_welcome_log"] + "\n")

    def _open_topic(self, item: TopicMenuItem) -> None:
        if item.page_route == PAGE_PP30:
            self._show_page(PAGE_PP30)
            return
        messagebox.showinfo(UI_TEXT["app_title"], UI_TEXT["menu_unavailable"])

    def _choose_express_data_dir(self) -> None:
        selected = filedialog.askdirectory(title=UI_TEXT["express_data_dir"])
        if not selected:
            return
        self.express_data_dir.set(selected)
        self._save_config()

    def _choose_pp30_folder(self) -> None:
        selected = filedialog.askdirectory(title=UI_TEXT["pp30_pdf_folder"])
        if not selected:
            return
        self.pp30_pdf_folder.set(selected)
        self._load_pp30_folder()

    def _load_pp30_folder(self) -> None:
        folder = Path(self.pp30_pdf_folder.get().strip()).expanduser()
        self.pp30_pdf_files = Pp30FolderService.list_pdfs(folder)
        if self.pp30_pdf_files:
            self.pp30_pdf_summary.set(UI_TEXT["pp30_pdf_total"].format(count=len(self.pp30_pdf_files)))
        else:
            self.pp30_pdf_summary.set(UI_TEXT["pp30_pdf_summary_empty"])

    def _pp30_form_config(self) -> Pp30FormConfig:
        return Pp30FormConfig(
            pdf_folder=Path(self.pp30_pdf_folder.get().strip()).expanduser(),
            jv_description=self.pp30_jv_description.get().strip(),
            pv_description=self.pp30_pv_description.get().strip(),
            jv_date=format_express_pv_date(self.pp30_jv_date.get()),
            pdf_files=list(self.pp30_pdf_files),
            run_mode=Pp30RunMode.parse(self.pp30_run_mode.get()),
        )

    def _format_pp30_jv_date(self, _event=None) -> None:
        current = self.pp30_jv_date.get()
        if is_complete_express_date(current):
            self.pp30_jv_date.set(format_express_pv_date(current))

    def _start_pp30(self) -> None:
        if self._pp30_running:
            return
        self.app_config = self.app_config_service.load()
        errors = self.app_config.validate()
        self._load_pp30_folder()
        errors.extend(self._pp30_form_config().validate())
        if errors:
            messagebox.showwarning(UI_TEXT["app_title"], "\n".join(errors))
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
                on_status=lambda message: self.root.after(0, lambda m=message: self._append_pp30_log(m)),
                on_progress=lambda done, total: self.root.after(
                    0, lambda d=done, t=total: self._set_pp30_progress(d, t)
                ),
            )
        except ValueError as exc:
            self.root.after(0, lambda text=str(exc): messagebox.showwarning(UI_TEXT["app_title"], text))
        except Exception as exc:
            self.root.after(0, lambda text=str(exc): messagebox.showerror(UI_TEXT["app_title"], text))
        finally:
            self.root.after(0, self._pp30_match_finished)

    def _pp30_match_finished(self) -> None:
        self._pp30_running = False

    def _set_pp30_progress(self, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(round(done * 100 / total))
        self.pp30_progress["value"] = percent
        self.pp30_progress_text.set(UI_TEXT["pp30_progress"].format(done=done, total=total, percent=percent))

    def _append_pp30_log(self, message: str) -> None:
        self.pp30_log_box.insert("end", message + "\n")
        self.pp30_log_box.see("end")

    def _copy_pp30_log(self) -> None:
        text = self.pp30_log_box.get("1.0", "end-1c")
        if not text.strip():
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _save_config(self) -> None:
        config = AppConfig(express_data_dir=Path(self.express_data_dir.get().strip()).expanduser())
        errors = config.validate()
        if errors:
            messagebox.showwarning(UI_TEXT["app_title"], "\n".join(errors))
            return
        self.app_config_service.save(config)
        self.app_config = config
        count = len(ExpressShopIndexService().write_from_dir(config.express_data_dir))
        self._refresh_config_summary()
        if count:
            messagebox.showinfo(
                UI_TEXT["app_title"],
                UI_TEXT["express_data_dir_saved"].format(count=count),
            )
        else:
            messagebox.showinfo(UI_TEXT["app_title"], UI_TEXT["express_data_dir_none"])

    def _refresh_config_summary(self) -> None:
        path = self.express_data_dir.get().strip()
        if not path:
            self.express_data_summary.set(UI_TEXT["express_data_dir_empty"])
            return
        count = ExpressShopIndexService().count()
        if count:
            self.express_data_summary.set(UI_TEXT["express_data_dir_saved"].format(count=count))
        else:
            self.express_data_summary.set(UI_TEXT["express_data_dir_none"])

    def _show_page(self, page_route: str) -> None:
        self._current_page = page_route
        self.menu_frame.pack_forget()
        self.config_frame.pack_forget()
        self.pp30_frame.pack_forget()
        if page_route == PAGE_CONFIG:
            self.root.geometry(f"{WIN_W}x{CONFIG_WIN_H}")
            self.root.title(f"{UI_TEXT['app_title']} — {UI_TEXT['config_title']} v{__version__}")
            self.express_data_dir.set(str(self.app_config.express_data_dir).strip())
            self._refresh_config_summary()
            self.config_frame.pack(fill="both", expand=True)
            return
        if page_route == PAGE_PP30:
            self.root.geometry(f"{WIN_W}x{PP30_WIN_H}")
            self.root.title(f"{UI_TEXT['app_title']} — {UI_TEXT['menu_pp30']} v{__version__}")
            self.pp30_frame.pack(fill="both", expand=True)
            return
        self.root.geometry(f"{WIN_W}x{MENU_WIN_H}")
        self.root.title(f"{UI_TEXT['app_title']} v{__version__}")
        self.menu_frame.pack(fill="both", expand=True)

    def run(self) -> None:
        self.root.mainloop()

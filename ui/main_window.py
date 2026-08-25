from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from constants.date_utils import default_work_date
from constants.routes import PROJECT_ROOT, TOPIC_PAYMENT_JOURNAL, UI_TEXT
from constants.version import __version__
from models.run_config import ExcelSheetSummary, RunConfig
from models.screen_region import ScreenRegion
from services.automation_service import AutomationService
from services.excel_service import ExcelService
from services.hotkey_service import HotkeyService
from ui.demo_background import DemoBackground
from ui.region_highlight import RegionHighlight
from ui.status_overlay import StatusOverlay


class MainWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(f"{UI_TEXT['app_title']} v{__version__}")
        self.root.geometry("560x540")
        self.root.resizable(False, False)
        self._set_window_icon()

        self.automation_service = AutomationService()
        ui_settings = self.automation_service.ui_settings
        self.hide_on_start = bool(ui_settings.get("hide_on_start", True))
        self.show_status_overlay = bool(ui_settings.get("show_status_overlay", True))
        self.show_region_highlight = bool(ui_settings.get("show_region_highlight", True))
        cancel_hotkeys = ui_settings.get("cancel_hotkeys") or ui_settings.get("cancel_hotkey", "esc")
        self.hotkey_service = HotkeyService(cancel_hotkeys)
        self.hotkey_label = self.hotkey_service.display_label
        self.status_overlay = StatusOverlay(self.root)
        screen_settings = self.automation_service.config.get("screen", {})
        self.region_highlight = RegionHighlight(
            self.root,
            base_width=int(screen_settings.get("width", 1920)),
            base_height=int(screen_settings.get("height", 1080)),
        )
        self.demo_background: DemoBackground | None = None
        demo_path: Path | None = None
        if self.automation_service.dry_run:
            ref = self.automation_service.template_click_settings.dry_run_reference
            candidate = Path(ref)
            if not candidate.is_absolute():
                candidate = PROJECT_ROOT / candidate
            if candidate.exists():
                demo_path = candidate
        if demo_path is None:
            demo_image = ui_settings.get("demo_reference_image", "")
            if demo_image:
                candidate = Path(demo_image)
                if not candidate.is_absolute():
                    candidate = PROJECT_ROOT / candidate
                if candidate.exists():
                    demo_path = candidate
        if demo_path is not None:
            self.demo_background = DemoBackground(
                self.root,
                demo_path,
                base_width=int(screen_settings.get("width", 1920)),
                base_height=int(screen_settings.get("height", 1080)),
            )
        self.is_running = False
        self._total_rows = 0

        defaults = self.automation_service.default_settings
        initial_pv_date = str(defaults.get("pv_date", "")).strip() or default_work_date()
        self.excel_path = tk.StringVar(value="")
        self.pv_date = tk.StringVar(value=initial_pv_date)
        self.description = tk.StringVar(value="")
        self.tax_payer_id = tk.StringVar(value="")
        self.status_text = tk.StringVar(value=UI_TEXT["ready"])
        self.progress_text = tk.StringVar(value="0 / 0")
        self.excel_summary = tk.StringVar(value=UI_TEXT["excel_summary_empty"])
        self.sheet_summaries: list[ExcelSheetSummary] = []

        self._build_ui()
        self._bind_shortcuts()
        self._load_excel()

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        form_frame = ttk.LabelFrame(self.root, text=UI_TEXT["settings_frame"])
        form_frame.pack(fill="x", **padding)

        ttk.Label(form_frame, text=UI_TEXT["excel_file"]).grid(row=0, column=0, sticky="w")
        ttk.Entry(form_frame, textvariable=self.excel_path, width=48).grid(row=0, column=1, sticky="ew")
        ttk.Button(form_frame, text=UI_TEXT["choose_file"], command=self._choose_excel).grid(row=0, column=2)

        ttk.Label(form_frame, textvariable=self.excel_summary, wraplength=500).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )

        ttk.Label(form_frame, text=UI_TEXT["pv_date"]).grid(row=2, column=0, sticky="w")
        ttk.Entry(form_frame, textvariable=self.pv_date, width=20).grid(row=2, column=1, sticky="w")
        ttk.Label(form_frame, text=UI_TEXT["pv_date_hint"], wraplength=500, foreground="#555555").grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(2, 0)
        )

        ttk.Label(form_frame, text=UI_TEXT["description"]).grid(row=4, column=0, sticky="nw")
        ttk.Entry(form_frame, textvariable=self.description, width=48).grid(row=4, column=1, columnspan=2, sticky="ew")
        ttk.Label(form_frame, text=UI_TEXT["description_hint"], wraplength=500, foreground="#555555").grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(2, 0)
        )

        ttk.Label(form_frame, text=UI_TEXT["tax_payer_id"]).grid(row=6, column=0, sticky="nw")
        ttk.Entry(form_frame, textvariable=self.tax_payer_id, width=48).grid(row=6, column=1, columnspan=2, sticky="ew")
        ttk.Label(form_frame, text=UI_TEXT["tax_payer_id_hint"], wraplength=500, foreground="#555555").grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(2, 0)
        )
        form_frame.columnconfigure(1, weight=1)

        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill="x", **padding)
        ttk.Button(action_frame, text=f"▶ {UI_TEXT['start']}", command=self._start).pack(side="left", padx=4)
        self.stop_button = ttk.Button(
            action_frame,
            text=f"■ {UI_TEXT['stop'].format(hotkey=self.hotkey_label)}",
            command=self._stop,
        )
        self.stop_button.pack(side="left", padx=4)

        status_frame = ttk.LabelFrame(self.root, text=UI_TEXT["status_frame"])
        status_frame.pack(fill="both", expand=True, **padding)
        ttk.Label(status_frame, textvariable=self.progress_text).pack(anchor="w", padx=8, pady=4)
        self.log_box = tk.Text(status_frame, height=12, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=8, pady=8)
        welcome = UI_TEXT["welcome_log"] + "\n"
        if self.automation_service.dry_run:
            welcome += (
                "\nโหมดทดสอบบน Mac: รัน flow จริง + จับภาพปุ่มจากรูป reference "
                "+ กรอบสีทองบนตำแหน่งที่เจอ (ไม่กด Express จริง)"
            )
        self.log_box.insert("1.0", welcome + "\n")

    def _bind_shortcuts(self) -> None:
        self.hotkey_service.bind_tk_shortcuts(self.root, self._stop)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_window_icon(self) -> None:
        icon_png = PROJECT_ROOT / "assets" / "icon" / "app_icon.png"
        if not icon_png.exists():
            return
        try:
            self._icon_image = tk.PhotoImage(file=str(icon_png))
            self.root.iconphoto(True, self._icon_image)
        except tk.TclError:
            pass

    def _on_close(self) -> None:
        if self.is_running:
            self._stop()
        self.hotkey_service.stop_listening()
        self.root.destroy()

    def _load_excel(self) -> None:
        raw_path = self.excel_path.get().strip()
        if not raw_path:
            self.sheet_summaries = []
            self.excel_summary.set(UI_TEXT["excel_summary_empty"])
            return

        excel_path = Path(raw_path).expanduser()
        if not excel_path.exists():
            self.sheet_summaries = []
            self.excel_summary.set(UI_TEXT["excel_summary_empty"])
            return

        try:
            self.sheet_summaries = ExcelService.load_sheet_summaries(excel_path)
        except Exception as exc:
            self.sheet_summaries = []
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

    def _choose_excel(self) -> None:
        selected = filedialog.askopenfilename(
            title=UI_TEXT["choose_file"],
            filetypes=[("Excel", "*.xlsx"), ("All files", "*.*")],
        )
        if selected:
            self.excel_path.set(selected)
            self._load_excel()

    def _start(self) -> None:
        if self.is_running:
            return

        if not self.sheet_summaries:
            self._load_excel()
        if not self.sheet_summaries:
            messagebox.showwarning("AutoKey", UI_TEXT["no_excel_loaded"])
            return

        run_config = RunConfig(
            topic=TOPIC_PAYMENT_JOURNAL,
            excel_path=Path(self.excel_path.get()).expanduser(),
            pv_date=self.pv_date.get().strip(),
            description=self.description.get().strip(),
            tax_payer_id=self.tax_payer_id.get().strip(),
            sheet_summaries=self.sheet_summaries,
        )
        errors = run_config.validate()
        if errors:
            messagebox.showwarning("AutoKey", "\n".join(errors))
            return

        confirm_rows = run_config.total_rows
        if not messagebox.askyesno(
            UI_TEXT["confirm_title"],
            f"{UI_TEXT['confirm_message']}\n\nจะทำ {confirm_rows} รายการ",
        ):
            return

        self.is_running = True
        self._total_rows = confirm_rows
        self._append_log(UI_TEXT["cancel_hotkey_hint"].format(hotkey=self.hotkey_label))
        self.hotkey_service.start_listening(self._stop)
        if self.show_status_overlay:
            self.status_overlay.show(
                UI_TEXT["cancel_hotkey_hint"].format(hotkey=self.hotkey_label)
            )
        if self.hide_on_start:
            self.root.withdraw()
        if self.demo_background is not None:
            self.demo_background.show_sync()

        self.automation_service.run_async(
            run_config=run_config,
            on_status=self._set_status,
            on_progress=self._set_progress,
            on_step=self._set_step,
            on_highlight=self._set_highlight,
            on_finished=self._on_finished,
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

    def _cleanup_run(self) -> None:
        self.is_running = False
        self.hotkey_service.stop_listening()
        if self.show_status_overlay:
            self.status_overlay.hide()
        if self.show_region_highlight:
            self.region_highlight.hide()
        if self.demo_background is not None:
            self.demo_background.hide()

    def _set_status(self, message: str) -> None:
        self.root.after(0, lambda: self._append_log(message))

    def _set_progress(self, current: int, total: int) -> None:
        progress = f"{current} / {total}"
        self.root.after(0, lambda: self.progress_text.set(progress))
        if self.show_status_overlay:
            self.status_overlay.update(0, "กำลังทำรายการ", progress=progress)

    def _set_step(self, step_index: int, step_label: str, detail: str) -> None:
        if not self.show_status_overlay:
            return
        progress = self.progress_text.get()
        self.status_overlay.update(step_index, step_label, detail, progress)

    def _set_highlight(self, region: ScreenRegion) -> None:
        if not self.show_region_highlight:
            return
        if self.demo_background is not None and self.demo_background.is_ready:
            self.demo_background.highlight(region)
            return
        mapper = self.demo_background if self.demo_background is not None else None
        self.region_highlight.show(region, mapper=mapper)

    def _on_finished(self, success: bool, message: str) -> None:
        def update() -> None:
            self._cleanup_run()
            self._restore_window()
            self.status_text.set(message)
            self._append_log(message)
            if success:
                messagebox.showinfo("AutoKey", message)
            else:
                messagebox.showerror("AutoKey", message)

        self.root.after(0, update)

    def _append_log(self, message: str) -> None:
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.status_text.set(message)

    def run(self) -> None:
        self.root.mainloop()

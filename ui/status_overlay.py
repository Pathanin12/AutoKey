from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class StatusOverlay:
    STEPS = [
        "เปิดเมนูสมุดรายวันจ่าย",
        "สร้างรายการใหม่",
        "กรอกหัวเรื่อง",
        "กรอกบัญชีค่าบริการ",
        "กรอกบัญชีภาษีซื้อ",
        "กรอกใบกำกับภาษีซื้อ",
        "กรอกบัญชีเงินสด",
        "ปิด Dialog WT (ยกเลิก)",
        "บันทึกรายการ",
    ]

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.window: tk.Toplevel | None = None
        self.title_var = tk.StringVar(value="AutoKey — สมุดรายวันจ่าย")
        self.step_var = tk.StringVar(value="รอเริ่มงาน...")
        self.detail_var = tk.StringVar(value="")
        self.progress_var = tk.StringVar(value="0 / 0")
        self.hint_var = tk.StringVar(value="")
        self._step_labels: list[ttk.Label] = []

    def show(self, cancel_hint: str) -> None:
        self.root.after(0, lambda: self._show_window(cancel_hint))

    def hide(self) -> None:
        self.root.after(0, self._hide_window)

    def update(
        self,
        step_index: int,
        step_label: str,
        detail: str = "",
        progress: str = "",
    ) -> None:
        self.root.after(0, lambda: self._apply_update(step_index, step_label, detail, progress))

    def _show_window(self, cancel_hint: str) -> None:
        if self.window is not None:
            return

        self.hint_var.set(cancel_hint)
        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#1f2937")
        self.window.geometry("320x420")

        screen_w = self.window.winfo_screenwidth()
        self.window.geometry(f"320x420+{max(screen_w - 340, 20)}+20")

        frame = tk.Frame(self.window, bg="#1f2937", padx=14, pady=12)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            textvariable=self.title_var,
            bg="#1f2937",
            fg="#f9fafb",
            font=("Tahoma", 12, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            frame,
            textvariable=self.progress_var,
            bg="#1f2937",
            fg="#93c5fd",
            font=("Tahoma", 10),
            anchor="w",
        ).pack(fill="x", pady=(4, 8))

        tk.Label(
            frame,
            textvariable=self.step_var,
            bg="#1f2937",
            fg="#fbbf24",
            font=("Tahoma", 11, "bold"),
            anchor="w",
            wraplength=290,
            justify="left",
        ).pack(fill="x")

        tk.Label(
            frame,
            textvariable=self.detail_var,
            bg="#1f2937",
            fg="#e5e7eb",
            font=("Tahoma", 10),
            anchor="w",
            wraplength=290,
            justify="left",
        ).pack(fill="x", pady=(6, 10))

        tk.Label(
            frame,
            text="ขั้นตอน",
            bg="#1f2937",
            fg="#9ca3af",
            font=("Tahoma", 9, "bold"),
            anchor="w",
        ).pack(fill="x")

        self._step_labels = []
        for index, label in enumerate(self.STEPS, start=1):
            step_label = tk.Label(
                frame,
                text=f"{index}. {label}",
                bg="#1f2937",
                fg="#6b7280",
                font=("Tahoma", 9),
                anchor="w",
            )
            step_label.pack(fill="x", pady=1)
            self._step_labels.append(step_label)

        tk.Label(
            frame,
            textvariable=self.hint_var,
            bg="#1f2937",
            fg="#fca5a5",
            font=("Tahoma", 9),
            anchor="w",
            wraplength=290,
            justify="left",
        ).pack(fill="x", pady=(10, 0))

    def _apply_update(
        self,
        step_index: int,
        step_label: str,
        detail: str,
        progress: str,
    ) -> None:
        self.step_var.set(step_label)
        self.detail_var.set(detail)
        if progress:
            self.progress_var.set(progress)

        for index, label_widget in enumerate(self._step_labels, start=1):
            if index < step_index:
                label_widget.configure(fg="#34d399")
            elif index == step_index:
                label_widget.configure(fg="#fbbf24")
            else:
                label_widget.configure(fg="#6b7280")

    def _hide_window(self) -> None:
        if self.window is not None:
            self.window.destroy()
            self.window = None
            self._step_labels = []

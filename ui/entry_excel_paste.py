"""วางเซลล์ Excel ลงช่องบรรทัดเดียว — ตัด CR/LF ท้ายเซลล์ ไม่บล็อก Ctrl+V ของ Windows"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from services.clipboard_service import normalize_pasted_cell, read_text

_PASTE_SEQUENCES = (
    "<<Paste>>",
    "<Control-v>",
    "<Control-V>",
    "<Control-อ>",
    "<Control-Thai_fofan>",
    "<Shift-Insert>",
)


def bind_excel_cell_paste(entries: list[ttk.Entry | tk.Entry]) -> None:
    for entry in entries:
        for sequence in _PASTE_SEQUENCES:
            entry.bind(sequence, _paste_excel_cell, add="+")


def _paste_excel_cell(event: tk.Event) -> str | None:
    widget = event.widget
    text = normalize_pasted_cell(_read_clipboard(widget))
    if not text:
        return None

    try:
        widget.delete("sel.first", "sel.last")
    except tk.TclError:
        pass
    widget.insert("insert", text)
    return "break"


def _read_clipboard(widget: tk.Misc) -> str:
    try:
        text = read_text()
        if text:
            return text
    except Exception:
        pass

    try:
        return str(widget.clipboard_get())
    except tk.TclError:
        return ""

"""วางเซลล์ Excel / ข้อความจากที่อื่นลงช่องบรรทัดเดียวบน Windows"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from services.clipboard_service import normalize_pasted_cell, read_text


def bind_excel_cell_paste(entries: list[ttk.Entry | tk.Entry]) -> None:
    for entry in entries:
        entry.bind("<<Paste>>", _paste_into_entry, add="+")
        entry.bind("<Control-v>", _paste_into_entry, add="+")
        entry.bind("<Control-V>", _paste_into_entry, add="+")
        entry.bind("<Shift-Insert>", _paste_into_entry, add="+")


def _paste_into_entry(event: tk.Event) -> str | None:
    widget = event.widget
    raw = read_text()
    if not raw:
        try:
            raw = str(widget.clipboard_get())
        except tk.TclError:
            return None

    text = normalize_pasted_cell(raw)
    if not text:
        return None

    try:
        widget.delete("sel.first", "sel.last")
    except tk.TclError:
        pass
    widget.insert("insert", text)
    return "break"

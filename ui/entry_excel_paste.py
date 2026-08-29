"""วางเซลล์ Excel ลงช่องบรรทัดเดียว — ตัด CR/LF ท้ายเซลล์"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from services.clipboard_service import normalize_pasted_cell, read_text


def bind_excel_cell_paste(entries: list[ttk.Entry | tk.Entry]) -> None:
    for entry in entries:
        entry.bind("<<Paste>>", _paste_excel_cell, add="+")
        entry.bind("<Control-v>", _paste_excel_cell, add="+")
        entry.bind("<Control-V>", _paste_excel_cell, add="+")


def _paste_excel_cell(event: tk.Event) -> str:
    widget = event.widget
    text = normalize_pasted_cell(read_text())
    if not text:
        return "break"
    try:
        widget.delete("sel.first", "sel.last")
    except tk.TclError:
        pass
    widget.insert("insert", text)
    return "break"

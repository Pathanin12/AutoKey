"""Ctrl+V / Cmd+V สำหรับช่องกรอก — รองรับภาษาไทยจาก clipboard Windows"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def bind_entry_clipboard(entry: ttk.Entry) -> None:
    for sequence in ("<Control-v>", "<Control-V>", "<Command-v>", "<Command-V>"):
        entry.bind(sequence, _paste, add="+")
    for sequence in ("<Control-c>", "<Control-C>", "<Command-c>", "<Command-C>"):
        entry.bind(sequence, _copy, add="+")
    for sequence in ("<Control-x>", "<Control-X>", "<Command-x>", "<Command-X>"):
        entry.bind(sequence, _cut, add="+")
    for sequence in ("<Control-a>", "<Control-A>", "<Command-a>", "<Command-A>"):
        entry.bind(sequence, _select_all, add="+")

    menu = tk.Menu(entry, tearoff=0)
    menu.add_command(label="วาง", command=lambda: _paste_into_entry(entry))
    menu.add_command(label="คัดลอก", command=lambda: _copy_from_entry(entry))
    menu.add_command(label="ตัด", command=lambda: _cut_from_entry(entry))
    menu.add_separator()
    menu.add_command(label="เลือกทั้งหมด", command=lambda: _select_all_in_entry(entry))

    def show_menu(event: tk.Event) -> str:
        entry.focus_set()
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    entry.bind("<Button-3>", show_menu, add="+")
    entry.bind("<Control-Button-1>", show_menu, add="+")


def _read_clipboard(entry: ttk.Entry) -> str:
    try:
        from services.clipboard_service import read_text

        text = read_text()
        if text:
            return text
    except Exception:
        pass
    try:
        return entry.clipboard_get()
    except tk.TclError:
        return ""


def _paste(_event: tk.Event | None = None) -> str:
    entry = _event.widget if _event is not None else None
    if entry is None:
        return "break"
    _paste_into_entry(entry)
    return "break"


def _paste_into_entry(entry: ttk.Entry) -> None:
    text = _read_clipboard(entry)
    if not text:
        return
    try:
        start = entry.index("sel.first")
        end = entry.index("sel.last")
        entry.delete(start, end)
        entry.insert(start, text)
    except tk.TclError:
        entry.insert(entry.index(tk.INSERT), text)


def _copy(_event: tk.Event | None = None) -> str:
    if _event is not None:
        _copy_from_entry(_event.widget)
    return "break"


def _copy_from_entry(entry: ttk.Entry) -> None:
    try:
        text = entry.selection_get()
    except tk.TclError:
        return
    entry.clipboard_clear()
    entry.clipboard_append(text)


def _cut(_event: tk.Event | None = None) -> str:
    if _event is not None:
        _cut_from_entry(_event.widget)
    return "break"


def _cut_from_entry(entry: ttk.Entry) -> None:
    try:
        text = entry.selection_get()
    except tk.TclError:
        return
    entry.clipboard_clear()
    entry.clipboard_append(text)
    try:
        entry.delete("sel.first", "sel.last")
    except tk.TclError:
        pass


def _select_all(_event: tk.Event | None = None) -> str:
    if _event is not None:
        _select_all_in_entry(_event.widget)
    return "break"


def _select_all_in_entry(entry: ttk.Entry) -> None:
    entry.selection_range(0, tk.END)
    entry.icursor(tk.END)


def bind_entries_clipboard(entries: list[ttk.Entry]) -> None:
    for entry in entries:
        bind_entry_clipboard(entry)

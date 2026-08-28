"""Ctrl+V / Cmd+V สำหรับช่องกรอก — รองรับวางจาก Excel / Notepad / ที่อื่น"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

PASTE_SEQUENCES = (
    "<Control-v>",
    "<Control-V>",
    "<Control-Key-v>",
    "<Control-Key-V>",
    "<Shift-Insert>",
    "<Command-v>",
    "<Command-V>",
)
COPY_SEQUENCES = (
    "<Control-c>",
    "<Control-C>",
    "<Control-Key-c>",
    "<Control-Key-C>",
    "<Control-Insert>",
    "<Command-c>",
    "<Command-C>",
)
CUT_SEQUENCES = (
    "<Control-x>",
    "<Control-X>",
    "<Control-Key-x>",
    "<Control-Key-X>",
    "<Shift-Delete>",
    "<Command-x>",
    "<Command-X>",
)
SELECT_ALL_SEQUENCES = (
    "<Control-a>",
    "<Control-A>",
    "<Control-Key-a>",
    "<Control-Key-A>",
    "<Command-a>",
    "<Command-A>",
)


def bind_entries_clipboard(root: tk.Misc, entries: list[ttk.Entry | tk.Entry]) -> None:
    for entry in entries:
        _bind_entry_context_menu(entry)

    for sequence in PASTE_SEQUENCES:
        root.bind_class("TEntry", sequence, _paste_event)
        root.bind_class("Entry", sequence, _paste_event)
    for sequence in COPY_SEQUENCES:
        root.bind_class("TEntry", sequence, _copy_event)
        root.bind_class("Entry", sequence, _copy_event)
    for sequence in CUT_SEQUENCES:
        root.bind_class("TEntry", sequence, _cut_event)
        root.bind_class("Entry", sequence, _cut_event)
    for sequence in SELECT_ALL_SEQUENCES:
        root.bind_class("TEntry", sequence, _select_all_event)
        root.bind_class("Entry", sequence, _select_all_event)

    # fallback เมื่อ class binding ไม่ทำงาน (พบบ่อยบน Windows + ttk)
    for sequence in PASTE_SEQUENCES:
        root.bind_all(sequence, _paste_all, add="+")
    for sequence in COPY_SEQUENCES:
        root.bind_all(sequence, _copy_all, add="+")
    for sequence in CUT_SEQUENCES:
        root.bind_all(sequence, _cut_all, add="+")
    for sequence in SELECT_ALL_SEQUENCES:
        root.bind_all(sequence, _select_all_all, add="+")


def _focused_entry(root: tk.Misc, event: tk.Event | None = None) -> ttk.Entry | tk.Entry | None:
    widget = event.widget if event is not None else None
    if widget is not None and widget.winfo_class() in {"TEntry", "Entry"}:
        return widget  # type: ignore[return-value]

    focus = root.focus_get()
    if focus is not None and focus.winfo_class() in {"TEntry", "Entry"}:
        return focus  # type: ignore[return-value]
    return None


def _paste_event(event: tk.Event) -> str:
    _paste_into_entry(event.widget)
    return "break"


def _paste_all(event: tk.Event) -> str | None:
    entry = _focused_entry(event.widget.winfo_toplevel(), event)
    if entry is None:
        return None
    _paste_into_entry(entry)
    return "break"


def _copy_event(event: tk.Event) -> str:
    _copy_from_entry(event.widget)
    return "break"


def _copy_all(event: tk.Event) -> str | None:
    entry = _focused_entry(event.widget.winfo_toplevel(), event)
    if entry is None:
        return None
    _copy_from_entry(entry)
    return "break"


def _cut_event(event: tk.Event) -> str:
    _cut_from_entry(event.widget)
    return "break"


def _cut_all(event: tk.Event) -> str | None:
    entry = _focused_entry(event.widget.winfo_toplevel(), event)
    if entry is None:
        return None
    _cut_from_entry(entry)
    return "break"


def _select_all_event(event: tk.Event) -> str:
    _select_all_in_entry(event.widget)
    return "break"


def _select_all_all(event: tk.Event) -> str | None:
    entry = _focused_entry(event.widget.winfo_toplevel(), event)
    if entry is None:
        return None
    _select_all_in_entry(entry)
    return "break"


def _read_clipboard(entry: tk.Entry | ttk.Entry) -> str:
    root = entry.winfo_toplevel()

    for source in (entry, root):
        try:
            text = source.clipboard_get()
            if text:
                return text
        except tk.TclError:
            pass

    if sys.platform == "win32":
        try:
            from services.clipboard_service import read_text

            text = read_text()
            if text:
                return text
        except Exception:
            pass

    try:
        import pyperclip

        text = pyperclip.paste()
        if text:
            return text
    except Exception:
        pass

    return ""


def _write_clipboard(entry: tk.Entry | ttk.Entry, text: str) -> None:
    if not text:
        return

    root = entry.winfo_toplevel()
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update_idletasks()
    except tk.TclError:
        pass

    if sys.platform == "win32":
        try:
            from services.clipboard_service import copy_text

            copy_text(text)
            return
        except Exception:
            pass

    try:
        import pyperclip

        pyperclip.copy(text)
    except Exception:
        pass


def _paste_into_entry(entry: tk.Entry | ttk.Entry) -> None:
    text = _read_clipboard(entry)
    if not text:
        return

    entry.focus_set()
    try:
        if entry.selection_present():
            entry.delete("sel.first", "sel.last")
    except tk.TclError:
        pass

    entry.insert("insert", text)
    entry.icursor(entry.index("insert"))
    entry.selection_clear()


def _copy_from_entry(entry: tk.Entry | ttk.Entry) -> None:
    try:
        text = entry.selection_get()
    except tk.TclError:
        return
    _write_clipboard(entry, text)


def _cut_from_entry(entry: tk.Entry | ttk.Entry) -> None:
    try:
        text = entry.selection_get()
    except tk.TclError:
        return
    _write_clipboard(entry, text)
    try:
        entry.delete("sel.first", "sel.last")
    except tk.TclError:
        pass


def _select_all_in_entry(entry: tk.Entry | ttk.Entry) -> None:
    entry.selection_range(0, tk.END)
    entry.icursor(tk.END)


def _bind_entry_context_menu(entry: tk.Entry | ttk.Entry) -> None:
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

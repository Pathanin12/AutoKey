"""Ctrl+V สำหรับช่องกรอก AutoKey — รองรับ ttk.Entry + StringVar บน Windows"""

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


def bind_entries_clipboard(entries: list[ttk.Entry | tk.Entry]) -> None:
    for entry in entries:
        _bind_entry_keys(entry)
        _bind_entry_context_menu(entry)


def _bind_entry_keys(entry: tk.Entry | ttk.Entry) -> None:
    entry.bind("<Control-v>", lambda _event: _handle_paste(entry), add="+")
    entry.bind("<Control-V>", lambda _event: _handle_paste(entry), add="+")
    entry.bind("<Control-Key-v>", lambda _event: _handle_paste(entry), add="+")
    entry.bind("<Control-Key-V>", lambda _event: _handle_paste(entry), add="+")
    entry.bind("<Shift-Insert>", lambda _event: _handle_paste(entry), add="+")
    entry.bind("<Command-v>", lambda _event: _handle_paste(entry), add="+")
    entry.bind("<Command-V>", lambda _event: _handle_paste(entry), add="+")

    entry.bind("<Control-c>", lambda _event: _handle_copy(entry), add="+")
    entry.bind("<Control-C>", lambda _event: _handle_copy(entry), add="+")
    entry.bind("<Control-Key-c>", lambda _event: _handle_copy(entry), add="+")
    entry.bind("<Control-Key-C>", lambda _event: _handle_copy(entry), add="+")
    entry.bind("<Control-Insert>", lambda _event: _handle_copy(entry), add="+")
    entry.bind("<Command-c>", lambda _event: _handle_copy(entry), add="+")
    entry.bind("<Command-C>", lambda _event: _handle_copy(entry), add="+")

    entry.bind("<Control-x>", lambda _event: _handle_cut(entry), add="+")
    entry.bind("<Control-X>", lambda _event: _handle_cut(entry), add="+")
    entry.bind("<Control-Key-x>", lambda _event: _handle_cut(entry), add="+")
    entry.bind("<Control-Key-X>", lambda _event: _handle_cut(entry), add="+")
    entry.bind("<Shift-Delete>", lambda _event: _handle_cut(entry), add="+")
    entry.bind("<Command-x>", lambda _event: _handle_cut(entry), add="+")
    entry.bind("<Command-X>", lambda _event: _handle_cut(entry), add="+")

    entry.bind("<Control-a>", lambda _event: _handle_select_all(entry), add="+")
    entry.bind("<Control-A>", lambda _event: _handle_select_all(entry), add="+")
    entry.bind("<Control-Key-a>", lambda _event: _handle_select_all(entry), add="+")
    entry.bind("<Control-Key-A>", lambda _event: _handle_select_all(entry), add="+")
    entry.bind("<Command-a>", lambda _event: _handle_select_all(entry), add="+")
    entry.bind("<Command-A>", lambda _event: _handle_select_all(entry), add="+")


def _handle_paste(entry: tk.Entry | ttk.Entry) -> str:
    _paste_into_entry(entry)
    return "break"


def _handle_copy(entry: tk.Entry | ttk.Entry) -> str:
    _copy_from_entry(entry)
    return "break"


def _handle_cut(entry: tk.Entry | ttk.Entry) -> str:
    _cut_from_entry(entry)
    return "break"


def _handle_select_all(entry: tk.Entry | ttk.Entry) -> str:
    _select_all_in_entry(entry)
    return "break"


def _read_clipboard(entry: tk.Entry | ttk.Entry) -> str:
    try:
        text = entry.clipboard_get()
        if text:
            return text
    except tk.TclError:
        pass

    try:
        text = entry.winfo_toplevel().clipboard_get()
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

        return pyperclip.paste() or ""
    except Exception:
        return ""


def _write_clipboard(text: str) -> None:
    if not text:
        return

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


def _set_entry_text(entry: tk.Entry | ttk.Entry, value: str, *, cursor: int | None = None) -> None:
    var_name = str(entry.cget("textvariable") or "")
    if var_name:
        entry.setvar(var_name, value)
    else:
        entry.delete(0, tk.END)
        entry.insert(0, value)

    if cursor is None:
        entry.icursor(tk.END)
    else:
        entry.icursor(cursor)


def _paste_into_entry(entry: tk.Entry | ttk.Entry) -> None:
    text = _read_clipboard(entry)
    if not text:
        return

    entry.focus_set()
    current = entry.get()

    try:
        if entry.selection_present():
            start = int(entry.index("sel.first"))
            end = int(entry.index("sel.last"))
        else:
            start = end = int(entry.index("insert"))
    except tk.TclError:
        start = end = len(current)

    new_text = current[:start] + text + current[end:]
    _set_entry_text(entry, new_text, cursor=start + len(text))


def _copy_from_entry(entry: tk.Entry | ttk.Entry) -> None:
    try:
        text = entry.selection_get()
    except tk.TclError:
        return
    _write_clipboard(text)


def _cut_from_entry(entry: tk.Entry | ttk.Entry) -> None:
    try:
        text = entry.selection_get()
    except tk.TclError:
        return
    _write_clipboard(text)
    try:
        start = int(entry.index("sel.first"))
        end = int(entry.index("sel.last"))
    except tk.TclError:
        return
    new_text = entry.get()[:start] + entry.get()[end:]
    _set_entry_text(entry, new_text, cursor=start)


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

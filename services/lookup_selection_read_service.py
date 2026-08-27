"""อ่านชื่อแถวที่เลือกใน dialog เลือกข้อมูล Express — grid ไม่ copy ลง clipboard ได้"""

from __future__ import annotations

import sys


def read_selected_row_text(*, name_subitems: tuple[int, ...] = (1, 0, 2, 3)) -> str:
    if sys.platform != "win32":
        return ""

    target = _get_target_window()

    for hwnd in _find_listview_handles(target):
        selected_index = _listview_selected_index(hwnd)
        if selected_index < 0:
            continue
        for subitem in name_subitems:
            text = _listview_subitem_text(hwnd, selected_index, subitem)
            if text:
                return text

    focused = _read_focused_control_text()
    if focused:
        return focused

    for hwnd in _find_edit_handles(target):
        text = _read_window_text(hwnd)
        if text:
            return text

    return ""


def _get_target_window() -> int:
    import ctypes

    user32 = ctypes.windll.user32
    return int(user32.GetForegroundWindow())


def _read_focused_control_text() -> str:
    import ctypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    foreground = user32.GetForegroundWindow()
    if not foreground:
        return ""

    foreground_thread = user32.GetWindowThreadProcessId(foreground, None)
    current_thread = kernel32.GetCurrentThreadId()
    attached = False
    try:
        if foreground_thread and foreground_thread != current_thread:
            user32.AttachThreadInput(current_thread, foreground_thread, True)
            attached = True
        focused = user32.GetFocus()
    finally:
        if attached:
            user32.AttachThreadInput(current_thread, foreground_thread, False)

    if not focused:
        return ""

    return _read_window_text(int(focused))


def _read_window_text(hwnd: int) -> str:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    WM_GETTEXT = 0x000D
    WM_GETTEXTLENGTH = 0x000E

    length = int(user32.SendMessageW(hwnd, WM_GETTEXTLENGTH, 0, 0))
    if length > 0:
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.SendMessageW(
            hwnd,
            WM_GETTEXT,
            length + 1,
            ctypes.cast(buffer, wintypes.LPARAM),
        )
        text = buffer.value.strip()
        if text:
            return text

    title_length = user32.GetWindowTextLengthW(hwnd)
    if title_length > 0:
        buffer = ctypes.create_unicode_buffer(title_length + 1)
        user32.GetWindowTextW(hwnd, buffer, title_length + 1)
        return buffer.value.strip()

    return ""


def _find_listview_handles(parent: int) -> list[int]:
    return _find_child_class_handles(parent, "SysListView32")


def _find_edit_handles(parent: int) -> list[int]:
    return _find_child_class_handles(parent, "Edit")


def _find_child_class_handles(parent: int, class_name: str) -> list[int]:
    if not parent:
        return []

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    handles: list[int] = []

    EnumChildProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @EnumChildProc
    def callback(hwnd, _lparam):
        class_buffer = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buffer, 256)
        if class_buffer.value == class_name:
            handles.append(int(hwnd))
        handles.extend(_find_child_class_handles(int(hwnd), class_name))
        return True

    user32.EnumChildWindows(parent, callback, 0)
    return handles


def _listview_selected_index(hwnd: int) -> int:
    import ctypes

    user32 = ctypes.windll.user32
    LVM_GETNEXTITEM = 0x100C
    LVNI_SELECTED = 0x0002
    return int(user32.SendMessageW(hwnd, LVM_GETNEXTITEM, -1, LVNI_SELECTED))


def _listview_subitem_text(hwnd: int, item_index: int, subitem: int) -> str:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    LVM_GETITEMTEXTW = 0x1073
    LVIF_TEXT = 0x0001

    class LVITEMW(ctypes.Structure):
        _fields_ = [
            ("mask", wintypes.UINT),
            ("iItem", ctypes.c_int),
            ("iSubItem", ctypes.c_int),
            ("state", wintypes.UINT),
            ("stateMask", wintypes.UINT),
            ("pszText", wintypes.LPWSTR),
            ("cchTextMax", ctypes.c_int),
            ("iImage", ctypes.c_int),
            ("lParam", wintypes.LPARAM),
            ("iIndent", ctypes.c_int),
            ("iGroupId", ctypes.c_int),
            ("cColumns", wintypes.UINT),
            ("puColumns", wintypes.LPVOID),
        ]

    buffer = ctypes.create_unicode_buffer(1024)
    item = LVITEMW()
    item.mask = LVIF_TEXT
    item.iItem = item_index
    item.iSubItem = subitem
    item.pszText = ctypes.cast(buffer, wintypes.LPWSTR)
    item.cchTextMax = 1024
    user32.SendMessageW(hwnd, LVM_GETITEMTEXTW, item_index, ctypes.byref(item))
    return buffer.value.strip()

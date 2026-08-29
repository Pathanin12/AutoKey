"""ใส่ชื่อลงช่องค้นหาของ Express โดยตรง — ไม่พึ่ง control ที่โฟกัสอยู่ (ปุ่ม/AutoKey)"""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes

from models.express_edit_target import ExpressEditTarget
from services.clipboard_service import copy_text
from services.window_focus_service import focus_window_by_title

WM_PASTE = 0x0302
WM_COMMAND = 0x0111
EM_SETSEL = 0x00B1
EM_REPLACESEL = 0x00C2
EN_CHANGE = 0x0300
GW_OWNER = 4

_AUTOKEY_TITLE = "autokey"
_EDIT_HINTS = ("edit", "tedit", "tmemo", "textbox", "thunder")


def paste_vendor_into_search(
    name: str,
    *,
    express_title_contains: str,
    button_rect: tuple[int, int, int, int] | None = None,
) -> bool:
    if sys.platform != "win32":
        return False

    text = name.strip()
    if not text:
        return False

    focus_window_by_title(express_title_contains, wait_after_focus_seconds=0.05)
    target = find_search_edit(express_title_contains, button_rect=button_rect)
    if target is None:
        return False

    _focus_hwnd(target.hwnd)
    time.sleep(0.05)
    return _put_text(target.hwnd, text)


def find_search_edit(
    express_title_contains: str,
    *,
    button_rect: tuple[int, int, int, int] | None = None,
) -> ExpressEditTarget | None:
    if sys.platform != "win32":
        return None

    roots = _express_root_hwnds(express_title_contains)
    edits = [edit for root in roots for edit in _collect_edits(root)]
    if not edits:
        return None

    if button_rect is not None:
        scored = [( _score_against_button(edit, button_rect), edit) for edit in edits]
        scored = [(score, edit) for score, edit in scored if score >= 0]
        if scored:
            scored.sort(key=lambda item: item[0], reverse=True)
            return scored[0][1]

    focused = _focused_edit(edits)
    if focused is not None:
        return focused

    edits.sort(key=lambda edit: (edit.top, -edit.width))
    return edits[-1]


def _put_text(hwnd: int, text: str) -> bool:
    user32 = ctypes.windll.user32
    copy_text(text)
    buffer = ctypes.c_wchar_p(text)
    text_lparam = ctypes.cast(buffer, ctypes.c_void_p).value or 0

    user32.SendMessageW(hwnd, EM_SETSEL, 0, -1)
    user32.SendMessageW(hwnd, EM_REPLACESEL, 1, text_lparam)
    if _window_text(hwnd).strip():
        _notify_change(hwnd)
        return True

    user32.SendMessageW(hwnd, WM_PASTE, 0, 0)
    if _window_text(hwnd).strip():
        _notify_change(hwnd)
        return True

    user32.SetWindowTextW(hwnd, text)
    _notify_change(hwnd)
    return bool(_window_text(hwnd).strip())


def _notify_change(hwnd: int) -> None:
    user32 = ctypes.windll.user32
    parent = int(user32.GetParent(hwnd) or 0)
    if not parent:
        return
    control_id = int(user32.GetDlgCtrlID(hwnd) or 0)
    wparam = (EN_CHANGE << 16) | (control_id & 0xFFFF)
    user32.SendMessageW(parent, WM_COMMAND, wparam, hwnd)


def _window_text(hwnd: int) -> str:
    user32 = ctypes.windll.user32
    length = int(user32.GetWindowTextLengthW(hwnd) or 0)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _score_against_button(edit: ExpressEditTarget, button_rect: tuple[int, int, int, int]) -> float:
    bx, by, bw, bh = button_rect
    button_cy = by + bh / 2
    if abs(edit.center_y - button_cy) > 36:
        return -1
    if edit.right > bx + 12:
        return -1
    if edit.width < 40:
        return -1
    gap = max(0, bx - edit.right)
    return edit.width - gap


def _focused_edit(edits: list[ExpressEditTarget]) -> ExpressEditTarget | None:
    user32 = ctypes.windll.user32
    foreground = int(user32.GetForegroundWindow() or 0)
    focused = 0
    if foreground:
        thread_id = user32.GetWindowThreadProcessId(foreground, None)
        focused = _gui_thread_info(thread_id)
    if not focused:
        return None
    for edit in edits:
        if edit.hwnd == focused:
            return edit
    return None


def _gui_thread_info(thread_id: int) -> int:
    class _GUITHREADINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hwndActive", wintypes.HWND),
            ("hwndFocus", wintypes.HWND),
            ("hwndCapture", wintypes.HWND),
            ("hwndMenuOwner", wintypes.HWND),
            ("hwndMoveSize", wintypes.HWND),
            ("hwndCaret", wintypes.HWND),
            ("rcCaret", wintypes.RECT),
        ]

    user32 = ctypes.windll.user32
    info = _GUITHREADINFO()
    info.cbSize = ctypes.sizeof(_GUITHREADINFO)
    if user32.GetGUIThreadInfo(thread_id, ctypes.byref(info)) and info.hwndFocus:
        return int(info.hwndFocus)
    return 0


def _express_root_hwnds(title_contains: str) -> list[int]:
    user32 = ctypes.windll.user32
    needle = title_contains.casefold()
    matches: list[int] = []

    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @EnumWindowsProc
    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _get_title(int(hwnd)).casefold()
        if _AUTOKEY_TITLE in title:
            return True
        if needle in title:
            matches.append(int(hwnd))
        return True

    user32.EnumWindows(callback, 0)
    roots: list[int] = []
    for hwnd in matches:
        roots.append(hwnd)
        roots.extend(_owned_windows(hwnd))
    return roots


def _owned_windows(owner: int) -> list[int]:
    user32 = ctypes.windll.user32
    found: list[int] = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @EnumWindowsProc
    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        if int(user32.GetWindow(hwnd, GW_OWNER) or 0) == owner:
            found.append(int(hwnd))
        return True

    user32.EnumWindows(callback, 0)
    return found


def _collect_edits(root: int) -> list[ExpressEditTarget]:
    user32 = ctypes.windll.user32
    found: list[ExpressEditTarget] = []
    EnumChildProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @EnumChildProc
    def callback(hwnd, _lparam):
        child = int(hwnd)
        if not user32.IsWindowVisible(child) or not user32.IsWindowEnabled(child):
            return True
        if not _is_edit_class(_get_class_name(child)):
            return True
        rect = wintypes.RECT()
        if not user32.GetWindowRect(child, ctypes.byref(rect)):
            return True
        found.append(
            ExpressEditTarget(
                hwnd=child,
                left=int(rect.left),
                top=int(rect.top),
                right=int(rect.right),
                bottom=int(rect.bottom),
            )
        )
        return True

    user32.EnumChildWindows(root, callback, 0)
    if _is_edit_class(_get_class_name(root)) and user32.IsWindowVisible(root):
        rect = wintypes.RECT()
        if user32.GetWindowRect(root, ctypes.byref(rect)):
            found.append(
                ExpressEditTarget(
                    hwnd=int(root),
                    left=int(rect.left),
                    top=int(rect.top),
                    right=int(rect.right),
                    bottom=int(rect.bottom),
                )
            )
    return found


def _is_edit_class(class_name: str) -> bool:
    lowered = class_name.lower()
    return any(hint in lowered for hint in _EDIT_HINTS)


def _get_class_name(hwnd: int) -> str:
    user32 = ctypes.windll.user32
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, 256)
    return buffer.value


def _get_title(hwnd: int) -> str:
    user32 = ctypes.windll.user32
    length = int(user32.GetWindowTextLengthW(hwnd) or 0)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _focus_hwnd(hwnd: int) -> None:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    foreground = int(user32.GetForegroundWindow() or 0)
    foreground_thread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0
    target_thread = user32.GetWindowThreadProcessId(hwnd, None)
    current_thread = kernel32.GetCurrentThreadId()

    attached_foreground = False
    attached_current = False
    try:
        if foreground_thread and foreground_thread != target_thread:
            user32.AttachThreadInput(foreground_thread, target_thread, True)
            attached_foreground = True
        if current_thread and current_thread != target_thread:
            user32.AttachThreadInput(current_thread, target_thread, True)
            attached_current = True
        user32.SetFocus(hwnd)
    finally:
        if attached_current:
            user32.AttachThreadInput(current_thread, target_thread, False)
        if attached_foreground:
            user32.AttachThreadInput(foreground_thread, target_thread, False)

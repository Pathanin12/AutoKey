"""โฟกัสหน้าต่าง Express Accounting บน Windows ก่อนส่งคีย์"""

from __future__ import annotations

import sys
import time
from typing import Callable

from models.window_focus_settings import WindowFocusSettings


def focus_express_window(
    settings: WindowFocusSettings,
    *,
    on_status: Callable[[str], None] | None = None,
) -> bool:
    title = settings.title_contains.strip()
    if not settings.enabled:
        return True

    if sys.platform != "win32":
        _status(on_status, "ข้ามโฟกัส Express (รองรับบน Windows เท่านั้น)")
        return True

    if not title:
        _status(on_status, "ข้ามโฟกัส Express (ไม่ได้ตั้งชื่อหน้าต่าง)")
        return True

    if settings.prepare_seconds > 0:
        time.sleep(settings.prepare_seconds)

    return focus_window_by_title(
        title,
        on_status=on_status,
        required=settings.required,
        wait_after_focus_seconds=settings.wait_after_focus_seconds,
        success_label=f"โฟกัส Express แล้ว: {{title}}",
        missing_label=f'ไม่พบหน้าต่าง Express ที่มีคำว่า "{title}"',
    )


def focus_window_by_title(
    title_contains: str,
    *,
    on_status: Callable[[str], None] | None = None,
    required: bool = False,
    wait_after_focus_seconds: float = 0.0,
    success_label: str = "โฟกัสหน้าต่างแล้ว: {title}",
    missing_label: str | None = None,
) -> bool:
    if sys.platform != "win32":
        return True

    needle = title_contains.strip()
    if not needle:
        return False

    hwnd = _find_visible_window(needle)
    if hwnd is None:
        message = missing_label or f'ไม่พบหน้าต่างที่มีคำว่า "{needle}"'
        if required:
            raise RuntimeError(message)
        _status(on_status, message)
        return False

    window_title = _get_window_title(hwnd)
    _activate_window(hwnd)
    if wait_after_focus_seconds > 0:
        time.sleep(wait_after_focus_seconds)
    _status(on_status, success_label.format(title=window_title))
    return True


def _status(on_status: Callable[[str], None] | None, message: str) -> None:
    if on_status:
        on_status(message)


def _find_visible_window(title_contains: str) -> int | None:
    if sys.platform != "win32":
        return None

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    matches: list[int] = []
    needle = title_contains.casefold()

    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @EnumWindowsProc
    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _get_window_title(hwnd)
        if needle in title.casefold():
            matches.append(int(hwnd))
        return True

    user32.EnumWindows(callback, 0)
    return matches[0] if matches else None


def _get_window_title(hwnd: int) -> str:
    if sys.platform != "win32":
        return ""

    import ctypes

    user32 = ctypes.windll.user32
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _activate_window(hwnd: int) -> None:
    if sys.platform != "win32":
        return

    import ctypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    SW_RESTORE = 9
    user32.ShowWindow(hwnd, SW_RESTORE)

    foreground = user32.GetForegroundWindow()
    foreground_thread = user32.GetWindowThreadProcessId(foreground, None)
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

        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
    finally:
        if attached_current:
            user32.AttachThreadInput(current_thread, target_thread, False)
        if attached_foreground:
            user32.AttachThreadInput(foreground_thread, target_thread, False)

from __future__ import annotations

import sys


def copy_text(text: str) -> None:
    if sys.platform == "win32":
        _copy_windows_unicode(text)
        return

    import pyperclip

    pyperclip.copy(text)


def _copy_windows_unicode(text: str) -> None:
    import ctypes
    from ctypes import wintypes

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL

    if not user32.OpenClipboard(None):
        raise RuntimeError("เปิด clipboard ไม่ได้")

    handle = None
    try:
        user32.EmptyClipboard()
        encoded = text.encode("utf-16-le") + b"\x00\x00"
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        if not handle:
            raise RuntimeError("จอง memory สำหรับ clipboard ไม่ได้")
        locked = kernel32.GlobalLock(handle)
        if not locked:
            raise RuntimeError("ล็อก memory สำหรับ clipboard ไม่ได้")
        ctypes.memmove(locked, encoded, len(encoded))
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise RuntimeError("ตั้งค่า clipboard ไม่ได้")
        handle = None
    finally:
        if handle is not None:
            kernel32.GlobalFree(handle)
        user32.CloseClipboard()

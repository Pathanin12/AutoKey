from __future__ import annotations

import ctypes
import sys

CF_TEXT = 1
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
THAI_ANSI_ENCODING = "cp874"


def copy_text(text: str) -> None:
    if sys.platform == "win32":
        _copy_windows_express(text)
        return

    import pyperclip

    pyperclip.copy(text)


def _copy_windows_express(text: str) -> None:
    """Express Accounting อ่าน CF_TEXT (TIS-620/cp874) — ใส่ทั้ง ANSI และ Unicode"""
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.restype = wintypes.BOOL

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL

    if not user32.OpenClipboard(None):
        raise RuntimeError("เปิด clipboard ไม่ได้")

    pending_handles: list[wintypes.HGLOBAL] = []
    try:
        user32.EmptyClipboard()

        unicode_bytes = text.encode("utf-16-le") + b"\x00\x00"
        _put_clipboard_format(
            user32,
            kernel32,
            CF_UNICODETEXT,
            unicode_bytes,
            pending_handles,
        )

        ansi_bytes = text.encode(THAI_ANSI_ENCODING, errors="replace") + b"\x00"
        _put_clipboard_format(
            user32,
            kernel32,
            CF_TEXT,
            ansi_bytes,
            pending_handles,
        )
        pending_handles.clear()
    except Exception:
        for handle in pending_handles:
            kernel32.GlobalFree(handle)
        raise
    finally:
        user32.CloseClipboard()


def _put_clipboard_format(
    user32,
    kernel32,
    format_id: int,
    data: bytes,
    pending_handles: list,
) -> None:
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not handle:
        raise RuntimeError("จอง memory สำหรับ clipboard ไม่ได้")

    locked = kernel32.GlobalLock(handle)
    if not locked:
        kernel32.GlobalFree(handle)
        raise RuntimeError("ล็อก memory สำหรับ clipboard ไม่ได้")

    ctypes.memmove(locked, data, len(data))
    kernel32.GlobalUnlock(handle)

    if not user32.SetClipboardData(format_id, handle):
        kernel32.GlobalFree(handle)
        raise RuntimeError("ตั้งค่า clipboard ไม่ได้")

    pending_handles.append(handle)

"""วาง clipboard ไป control ที่โฟกัส — รองรับ Express (legacy Win32)"""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes

WM_PASTE = 0x0302
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_V = 0x56
VK_A = 0x41
VK_INSERT = 0x2D


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


def paste_to_foreground(*, clear_first: bool = False) -> None:
    if sys.platform != "win32":
        _paste_pyautogui(clear_first=clear_first)
        return

    if clear_first:
        _send_ctrl_a()
        time.sleep(0.05)

    _paste_wm_paste()


def _get_focus_hwnd() -> int:
    user32 = ctypes.windll.user32
    foreground = user32.GetForegroundWindow()
    if not foreground:
        return 0

    thread_id = user32.GetWindowThreadProcessId(foreground, None)
    info = _GUITHREADINFO()
    info.cbSize = ctypes.sizeof(_GUITHREADINFO)
    if user32.GetGUIThreadInfo(thread_id, ctypes.byref(info)) and info.hwndFocus:
        return int(info.hwndFocus)
    return int(foreground)


def _paste_wm_paste() -> None:
    target = _get_focus_hwnd()
    if not target:
        return
    ctypes.windll.user32.SendMessageW(target, WM_PASTE, 0, 0)


def _paste_shift_insert() -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(VK_SHIFT, 0, 0, 0)
    user32.keybd_event(VK_INSERT, 0, 0, 0)
    user32.keybd_event(VK_INSERT, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)


def _send_ctrl_v() -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def _send_ctrl_a() -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_A, 0, 0, 0)
    user32.keybd_event(VK_A, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def _paste_pyautogui(*, clear_first: bool = False) -> None:
    try:
        import pyautogui
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("ต้องติดตั้ง pyautogui") from exc

    if clear_first:
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.04)
    pyautogui.hotkey("ctrl", "v")

"""ส่งคีย์แบบ virtual-key บน Windows — ไม่ตามแป้นไทย และไม่ให้หน้า Tk กิน Alt"""

from __future__ import annotations

import sys
import time

_VK = {
    "alt": 0x12,
    "ctrl": 0x11,
    "control": 0x11,
    "shift": 0x10,
    "enter": 0x0D,
    "tab": 0x09,
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "down": 0x28,
    "up": 0x26,
    "left": 0x25,
    "right": 0x27,
    "f2": 0x71,
    "f8": 0x77,
    "f9": 0x78,
    "f11": 0x7A,
}


def send_hotkey(*keys: str) -> None:
    if sys.platform != "win32":
        return

    from services.window_focus_service import focus_window_by_title

    focus_window_by_title(
        "Express",
        on_status=None,
        required=False,
        wait_after_focus_seconds=0.12,
    )
    _send_virtual_keys([_vk_code(key) for key in keys])
    time.sleep(0.03)


def _vk_code(key: str) -> int:
    token = key.strip().lower()
    if token in _VK:
        return _VK[token]
    if len(token) == 1:
        char = token.upper()
        if "A" <= char <= "Z" or "0" <= char <= "9":
            return ord(char)
    if token.startswith("f") and token[1:].isdigit():
        number = int(token[1:])
        if 1 <= number <= 24:
            return 0x70 + number - 1
    raise ValueError(f"ไม่รู้จักปุ่ม: {key}")


def _send_virtual_keys(virtual_keys: list[int]) -> None:
    import ctypes
    from ctypes import wintypes

    ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class INPUTUNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("union", INPUTUNION)]

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    events: list[INPUT] = []

    def _event(vk: int, flags: int) -> INPUT:
        item = INPUT()
        item.type = INPUT_KEYBOARD
        item.union.ki.wVk = vk
        item.union.ki.wScan = 0
        item.union.ki.dwFlags = flags
        item.union.ki.time = 0
        item.union.ki.dwExtraInfo = 0
        return item

    for vk in virtual_keys:
        events.append(_event(vk, 0))
    for vk in reversed(virtual_keys):
        events.append(_event(vk, KEYEVENTF_KEYUP))

    array_type = INPUT * len(events)
    payload = array_type(*events)
    sent = ctypes.windll.user32.SendInput(len(events), ctypes.byref(payload), ctypes.sizeof(INPUT))
    if sent != len(events):
        raise RuntimeError("ส่งคีย์ไป Express ไม่ครบ")

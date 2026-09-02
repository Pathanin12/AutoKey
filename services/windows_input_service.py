"""ส่งคีย์แบบ virtual-key / Unicode บน Windows — ไม่ตามแป้นไทย"""

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

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
SM_CXSCREEN = 0
SM_CYSCREEN = 1


def send_hotkey(*keys: str) -> None:
    """Alt+A เปิดไฟล์ใหม่ — โฟกัส Express ก่อน แล้วส่ง virtual key"""
    if sys.platform != "win32":
        return

    from services.window_focus_service import focus_window_by_title

    focus_window_by_title(
        "Express",
        on_status=None,
        required=False,
        wait_after_focus_seconds=0.12,
    )
    send_combo(*keys)


def send_combo(*keys: str) -> None:
    """ส่งคีย์ค้าง (เช่น Ctrl+A) โดยไม่โฟกัส Express ใหม่"""
    if sys.platform != "win32":
        return
    _send_virtual_keys([_vk_code(key) for key in keys])
    time.sleep(0.03)


def text_is_ascii_keys(text: str) -> bool:
    """ตัวเลข วันที่ รหัสบัญชี ยอดเงิน — ส่ง Unicode ได้โดยไม่ตามแป้นไทย/อังกฤษ"""
    return all(32 <= ord(character) <= 126 for character in text)


def send_ascii_text(text: str, *, interval: float = 0.03) -> None:
    """พิมพ์ ASCII ทีละตัวด้วย Unicode — รีโมตกับนั่งเครื่องได้ค่าเดียวกัน"""
    if sys.platform != "win32" or not text:
        return
    if not text_is_ascii_keys(text):
        raise ValueError(f"รองรับเฉพาะ ASCII: {text!r}")
    send_unicode_text(text, interval=interval)


def send_unicode_text(text: str, *, interval: float = 0.03) -> None:
    """พิมพ์ตัวอักษรจริงลงช่องที่โฟกัส — ไม่ตามแป้นไทย และไม่ใช้ clipboard"""
    if sys.platform != "win32" or not text:
        return
    for char in text:
        for unit in _utf16_units(char):
            _send_unicode_unit(unit)
        if interval:
            time.sleep(interval)


def move_to(x: int, y: int) -> None:
    if sys.platform != "win32":
        return
    ax, ay = _absolute_point(x, y)
    _send_mouse_events([(ax, ay, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE)])


def click_at(x: int, y: int) -> None:
    if sys.platform != "win32":
        return
    move_to(x, y)
    _send_mouse_events(
        [
            (0, 0, MOUSEEVENTF_LEFTDOWN),
            (0, 0, MOUSEEVENTF_LEFTUP),
        ]
    )
    time.sleep(0.03)


def cursor_position() -> tuple[int, int]:
    if sys.platform != "win32":
        return (0, 0)
    import ctypes
    from ctypes import wintypes

    point = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return int(point.x), int(point.y)


def _utf16_units(char: str) -> tuple[int, ...]:
    code = ord(char)
    if code <= 0xFFFF:
        return (code,)
    extra = code - 0x10000
    return (0xD800 + (extra >> 10), 0xDC00 + (extra & 0x3FF))


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
    events = []
    for vk in virtual_keys:
        events.append((vk, 0, 0))
    for vk in reversed(virtual_keys):
        events.append((vk, 0, KEYEVENTF_KEYUP))
    _send_key_events(events)


def _send_unicode_unit(unit: int) -> None:
    _send_key_events(
        [
            (0, unit, KEYEVENTF_UNICODE),
            (0, unit, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP),
        ]
    )


def _absolute_point(x: int, y: int) -> tuple[int, int]:
    import ctypes

    width = max(int(ctypes.windll.user32.GetSystemMetrics(SM_CXSCREEN)), 1)
    height = max(int(ctypes.windll.user32.GetSystemMetrics(SM_CYSCREEN)), 1)
    norm_x = int(round(x * 65535 / max(width - 1, 1)))
    norm_y = int(round(y * 65535 / max(height - 1, 1)))
    return norm_x, norm_y


_INPUT_TYPE = None


def _input_structs():
    global _INPUT_TYPE
    if _INPUT_TYPE is not None:
        return _INPUT_TYPE

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

    _INPUT_TYPE = INPUT
    return INPUT


def _send_inputs(payload_events) -> None:
    import ctypes

    if not payload_events:
        return
    INPUT = payload_events[0].__class__
    array_type = INPUT * len(payload_events)
    payload = array_type(*payload_events)
    sent = ctypes.windll.user32.SendInput(
        len(payload_events), ctypes.byref(payload), ctypes.sizeof(INPUT)
    )
    if sent != len(payload_events):
        raise RuntimeError("ส่ง input ไป Express ไม่ครบ")


def _send_mouse_events(events: list[tuple[int, int, int]]) -> None:
    INPUT = _input_structs()
    payload_events = []
    for dx, dy, flags in events:
        item = INPUT()
        item.type = INPUT_MOUSE
        item.union.mi.dx = dx
        item.union.mi.dy = dy
        item.union.mi.mouseData = 0
        item.union.mi.dwFlags = flags
        item.union.mi.time = 0
        item.union.mi.dwExtraInfo = 0
        payload_events.append(item)
    _send_inputs(payload_events)


def _send_key_events(events: list[tuple[int, int, int]]) -> None:
    INPUT = _input_structs()
    payload_events = []
    for vk, scan, flags in events:
        item = INPUT()
        item.type = INPUT_KEYBOARD
        item.union.ki.wVk = vk
        item.union.ki.wScan = scan
        item.union.ki.dwFlags = flags
        item.union.ki.time = 0
        item.union.ki.dwExtraInfo = 0
        payload_events.append(item)
    _send_inputs(payload_events)

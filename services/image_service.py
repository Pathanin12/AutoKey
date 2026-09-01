from __future__ import annotations

import sys
import time
from pathlib import Path

try:
    import pyautogui
except ImportError:  # pragma: no cover - dev on non-runtime env
    pyautogui = None

from services.clipboard_service import clear_clipboard, copy_text
from services.window_paste_service import paste_to_foreground

_SETTLE_KEYS = frozenset({"enter", "return", "tab"})


class ImageService:
    """ส่งคีย์/คลิก/จับภาพหน้าจอผ่าน pyautogui"""

    def __init__(
        self,
        action_delay: float = 0.05,
        type_interval: float = 0.02,
        key_settle_wait: float = 0.08,
        fail_safe: bool = True,
        screen_width: int = 1920,
        screen_height: int = 1080,
    ) -> None:
        self.action_delay = action_delay
        self.type_interval = type_interval
        self.key_settle_wait = key_settle_wait
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._ensure_runtime()
        pyautogui.FAILSAFE = fail_safe
        pyautogui.PAUSE = 0

    def _ensure_runtime(self) -> None:
        if pyautogui is None:
            raise RuntimeError("ต้องติดตั้ง pyautogui บน Windows ก่อนรัน automation")

    def wait(self, seconds: float | None = None) -> None:
        time.sleep(seconds if seconds is not None else self.action_delay)

    def screenshot(self):
        self._ensure_runtime()
        shot = pyautogui.screenshot()
        image = shot.convert("RGBA")
        if image.size != (self.screen_width, self.screen_height):
            image = image.resize((self.screen_width, self.screen_height))
        return image

    def save_screenshot(self, path: Path) -> Path:
        self._ensure_runtime()
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shot = pyautogui.screenshot()
        shot.save(dest)
        return dest

    def copy_selection(self) -> None:
        self._ensure_runtime()
        self._send_combo("ctrl", "c")
        self.wait(0.1)

    def click_at(self, x: int, y: int) -> None:
        self._ensure_runtime()
        pyautogui.click(x, y)
        self.wait(0.03)

    def move_to(self, x: int, y: int) -> None:
        self._ensure_runtime()
        pyautogui.moveTo(x, y)
        self.wait(0.03)

    def press(self, *keys: str, presses: int = 1) -> None:
        self._ensure_runtime()
        for _ in range(presses):
            if sys.platform == "win32":
                if any(key.lower() == "alt" for key in keys):
                    from services.windows_input_service import send_hotkey

                    send_hotkey(*keys)
                else:
                    self._send_combo(*keys)
            elif len(keys) > 1:
                pyautogui.hotkey(*keys)
            else:
                pyautogui.press(keys[0])
            self.wait(self._wait_after_keys(keys))

    def _wait_after_keys(self, keys: tuple[str, ...]) -> float:
        if any(key.lower() in _SETTLE_KEYS for key in keys):
            return self.key_settle_wait
        return self.action_delay

    def _send_combo(self, *keys: str) -> None:
        from services.windows_input_service import send_combo

        send_combo(*keys)

    def type_text(self, text: str, clear_first: bool = True) -> None:
        if sys.platform == "win32":
            from services.windows_input_service import send_ascii_text, text_is_ascii_keys

            if text_is_ascii_keys(text):
                self._type_ascii(text, clear_first=clear_first)
                return
        self._paste_text(text, clear_first=clear_first)

    def type_thai(self, text: str, clear_first: bool = True) -> None:
        self._paste_text(text, clear_first=clear_first)

    def type_keys(self, text: str, *, clear_first: bool = False) -> None:
        """พิมพ์ทีละตัว — รหัสบัญชี/วันที่ ไม่ตามแป้นไทย"""
        if not text:
            return
        self._ensure_runtime()
        if sys.platform == "win32":
            self._type_ascii(text, clear_first=clear_first)
            return
        if clear_first:
            pyautogui.hotkey("ctrl", "a")
            self.wait()
        pyautogui.typewrite(text, interval=self.type_interval)
        self.wait()

    def _type_ascii(self, text: str, *, clear_first: bool) -> None:
        from services.windows_input_service import send_ascii_text

        if clear_first:
            self._send_combo("ctrl", "a")
            self.wait()
        send_ascii_text(text, interval=self.type_interval)
        self.wait()

    def paste_clipboard(self, *, clear_first: bool = False) -> None:
        """วางจาก clipboard — ช่องค้นหา Express หลังคลิก ค้นหา"""
        self.paste_from_clipboard(clear_first=clear_first)

    def paste_from_clipboard(self, clear_first: bool = False) -> None:
        self._ensure_runtime()
        paste_to_foreground(clear_first=clear_first)
        self.wait()

    def _paste_text(self, text: str, clear_first: bool = True) -> None:
        if not text:
            return
        self._ensure_runtime()
        if clear_first:
            self._send_combo("ctrl", "a") if sys.platform == "win32" else pyautogui.hotkey("ctrl", "a")
            self.wait()
        copy_text(text)
        time.sleep(0.1 if sys.platform == "win32" else 0.04)
        if sys.platform == "win32":
            self._send_combo("ctrl", "v")
        else:
            pyautogui.hotkey("ctrl", "v")
        self.wait()
        clear_clipboard()

from __future__ import annotations

import sys
import time

try:
    import pyautogui
except ImportError:  # pragma: no cover - dev on non-runtime env
    pyautogui = None


class ImageService:
    """ส่งคีย์/คลิก/จับภาพหน้าจอผ่าน pyautogui"""

    def __init__(
        self,
        action_delay: float = 0.05,
        type_interval: float = 0.02,
        fail_safe: bool = True,
        screen_width: int = 1920,
        screen_height: int = 1080,
    ) -> None:
        self.action_delay = action_delay
        self.type_interval = type_interval
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

    def copy_selection(self) -> None:
        self._ensure_runtime()
        pyautogui.hotkey("ctrl", "c")
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
        if len(keys) > 1:
            for _ in range(presses):
                if sys.platform == "win32" and any(key.lower() == "alt" for key in keys):
                    from services.windows_input_service import send_hotkey

                    send_hotkey(*keys)
                else:
                    pyautogui.hotkey(*keys)
                self.wait(0.03)
            return
        pyautogui.press(keys[0], presses=presses, interval=0.03)
        self.wait(0.03)

    def type_text(self, text: str, clear_first: bool = True) -> None:
        self.type_keys(text, clear_first=clear_first)

    def type_thai(self, text: str, clear_first: bool = True) -> None:
        self.type_keys(text, clear_first=clear_first)

    def type_keys(self, text: str, *, clear_first: bool = False) -> None:
        """พิมพ์ทีละตัวลง Express — Unicode ไม่ตามแป้นไทย ไม่ใช้ clipboard"""
        if not text:
            return
        self._ensure_runtime()
        if clear_first:
            if sys.platform == "win32":
                from services.windows_input_service import send_combo

                send_combo("ctrl", "a")
            else:
                pyautogui.hotkey("ctrl", "a")
            time.sleep(0.04)
        if sys.platform == "win32":
            from services.windows_input_service import send_unicode_text

            send_unicode_text(text, interval=self.type_interval)
        else:
            pyautogui.typewrite(text, interval=self.type_interval)
        self.wait(0.05)

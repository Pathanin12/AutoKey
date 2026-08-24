from __future__ import annotations

import time

try:
    import pyautogui
except ImportError:  # pragma: no cover - dev on non-runtime env
    pyautogui = None


class ImageService:
    """ส่งคีย์/พิมพ์ข้อความผ่าน pyautogui — ไม่ใช้จับภาพปุ่ม"""

    def __init__(
        self,
        action_delay: float = 0.4,
        type_interval: float = 0.03,
        fail_safe: bool = True,
    ) -> None:
        self.action_delay = action_delay
        self.type_interval = type_interval
        self._ensure_runtime()
        pyautogui.FAILSAFE = fail_safe
        pyautogui.PAUSE = action_delay

    def _ensure_runtime(self) -> None:
        if pyautogui is None:
            raise RuntimeError("ต้องติดตั้ง pyautogui บน Windows ก่อนรัน automation")

    def wait(self, seconds: float | None = None) -> None:
        time.sleep(seconds if seconds is not None else self.action_delay)

    def press(self, *keys: str, presses: int = 1) -> None:
        if len(keys) > 1:
            for _ in range(presses):
                pyautogui.hotkey(*keys)
                self.wait(0.15)
            return
        pyautogui.press(keys[0], presses=presses, interval=0.15)
        if presses == 1:
            self.wait(0.15)

    def type_text(self, text: str, clear_first: bool = True) -> None:
        if clear_first:
            pyautogui.hotkey("ctrl", "a")
            self.wait(0.1)
        pyautogui.typewrite(text, interval=self.type_interval)
        self.wait()

    def type_thai(self, text: str, clear_first: bool = True) -> None:
        if clear_first:
            pyautogui.hotkey("ctrl", "a")
            self.wait(0.1)
        try:
            import pyperclip

            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
        except ImportError:
            pyautogui.typewrite(text, interval=self.type_interval)
        self.wait()

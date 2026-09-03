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
    """ส่งคีย์/คลิกด้วย Windows SendInput — จับภาพหน้าจอผ่าน pyautogui"""

    def __init__(
        self,
        action_delay: float = 0.05,
        type_interval: float = 0.02,
        key_settle_wait: float = 0.03,
        fail_safe: bool = True,
        screen_width: int = 1920,
        screen_height: int = 1080,
    ) -> None:
        self.action_delay = action_delay
        self.type_interval = type_interval
        self.key_settle_wait = key_settle_wait
        self.fail_safe = fail_safe
        self.screen_width = screen_width
        self.screen_height = screen_height
        if sys.platform != "win32":
            self._ensure_runtime()
        if pyautogui is not None:
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

    def _check_failsafe(self) -> None:
        if not self.fail_safe:
            return
        if sys.platform == "win32":
            from services.windows_input_service import cursor_position

            x, y = cursor_position()
            if x <= 1 and y <= 1:
                raise RuntimeError("หยุดแล้ว — เลื่อนเมาส์ไปมุมซ้ายบน")
            return
        self._ensure_runtime()

    def copy_selection(self) -> None:
        self._check_failsafe()
        self._send_combo("ctrl", "c")
        self.wait(0.1)

    def click_at(self, x: int, y: int) -> None:
        self._check_failsafe()
        if sys.platform == "win32":
            from services.windows_input_service import click_at as send_click

            send_click(x, y)
            self.wait(0.03)
            return
        self._ensure_runtime()
        pyautogui.click(x, y)
        self.wait(0.03)

    def move_to(self, x: int, y: int) -> None:
        self._check_failsafe()
        if sys.platform == "win32":
            from services.windows_input_service import move_to as send_move

            send_move(x, y)
            self.wait(0.03)
            return
        self._ensure_runtime()
        pyautogui.moveTo(x, y)
        self.wait(0.03)

    def press(self, *keys: str, presses: int = 1) -> None:
        self._check_failsafe()
        for _ in range(presses):
            if sys.platform == "win32":
                if any(key.lower() == "alt" for key in keys):
                    from services.windows_input_service import send_hotkey

                    send_hotkey(*keys)
                else:
                    self._send_combo(*keys)
            else:
                self._ensure_runtime()
                if len(keys) > 1:
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
            self._type_unicode(text, clear_first=clear_first)
            return
        self._paste_text(text, clear_first=clear_first)

    def type_thai(self, text: str, clear_first: bool = True) -> None:
        if sys.platform == "win32":
            self._type_unicode(text, clear_first=clear_first)
            return
        self._paste_text(text, clear_first=clear_first)

    def type_keys(self, text: str, *, clear_first: bool = False) -> None:
        """พิมพ์ทีละตัว — รหัสบัญชี/วันที่ ไม่ตามแป้นไทย"""
        if not text:
            return
        if sys.platform == "win32":
            self._type_ascii(text, clear_first=clear_first)
            return
        self._ensure_runtime()
        if clear_first:
            pyautogui.hotkey("ctrl", "a")
            self.wait()
        pyautogui.typewrite(text, interval=self.type_interval)
        self.wait()

    def _type_ascii(self, text: str, *, clear_first: bool) -> None:
        from services.windows_input_service import send_ascii_text

        self._check_failsafe()
        if clear_first:
            self._send_combo("ctrl", "a")
            self.wait()
        send_ascii_text(text, interval=self.type_interval)
        self.wait()

    def _type_unicode(self, text: str, *, clear_first: bool) -> None:
        from services.windows_input_service import send_unicode_text

        if not text:
            return
        self._check_failsafe()
        if clear_first:
            self._send_combo("ctrl", "a")
            self.wait()
        send_unicode_text(text, interval=self.type_interval)
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

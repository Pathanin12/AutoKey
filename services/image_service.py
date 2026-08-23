from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

try:
    import cv2
    import numpy as np
    import pyautogui
except ImportError:  # pragma: no cover - dev on non-runtime env
    cv2 = None
    np = None
    pyautogui = None


@dataclass
class MatchResult:
    x: int
    y: int
    width: int
    height: int
    confidence: float

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2


class ImageService:
    def __init__(
        self,
        templates_dir: Path,
        confidence: float = 0.85,
        action_delay: float = 0.4,
        type_interval: float = 0.03,
        fail_safe: bool = True,
    ) -> None:
        self.templates_dir = templates_dir
        self.confidence = confidence
        self.action_delay = action_delay
        self.type_interval = type_interval
        self._ensure_runtime()
        pyautogui.FAILSAFE = fail_safe
        pyautogui.PAUSE = action_delay

    def _ensure_runtime(self) -> None:
        if pyautogui is None or cv2 is None:
            raise RuntimeError(
                "ต้องติดตั้ง pyautogui และ opencv-python บน Windows ก่อนรัน automation"
            )

    def wait(self, seconds: float | None = None) -> None:
        time.sleep(seconds if seconds is not None else self.action_delay)

    def press(self, *keys: str, presses: int = 1) -> None:
        for _ in range(presses):
            pyautogui.hotkey(*keys) if len(keys) > 1 else pyautogui.press(keys[0])
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

    def click(self, x: int, y: int) -> None:
        pyautogui.click(x, y)
        self.wait()

    def click_center(self, match: MatchResult) -> None:
        self.click(*match.center)

    def locate(self, template_name: str, confidence: float | None = None) -> MatchResult | None:
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            return None

        screenshot = pyautogui.screenshot()
        screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(str(template_path))
        if template is None:
            return None

        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        threshold = confidence if confidence is not None else self.confidence
        if max_val < threshold:
            return None

        height, width = template.shape[:2]
        x, y = max_loc
        return MatchResult(x=x, y=y, width=width, height=height, confidence=float(max_val))

    def wait_and_click(
        self,
        template_name: str,
        timeout: float = 10.0,
        confidence: float | None = None,
    ) -> MatchResult:
        deadline = time.time() + timeout
        while time.time() < deadline:
            match = self.locate(template_name, confidence=confidence)
            if match:
                self.click_center(match)
                return match
            self.wait(0.3)
        raise TimeoutError(f"ไม่พบภาพ template: {template_name}")

    def click_if_found(self, template_name: str) -> bool:
        match = self.locate(template_name)
        if not match:
            return False
        self.click_center(match)
        return True

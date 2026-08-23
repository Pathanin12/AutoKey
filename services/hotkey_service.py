from __future__ import annotations

import re
import threading
from typing import Callable

try:
    from pynput import keyboard
except ImportError:  # pragma: no cover
    keyboard = None  # type: ignore[assignment]

MODIFIER_ALIASES = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "cmd": "cmd",
    "command": "cmd",
    "super": "cmd",
    "win": "cmd",
    "alt": "alt",
    "option": "alt",
    "shift": "shift",
}

SPECIAL_KEYS = {
    "esc": "esc",
    "escape": "esc",
    "enter": "enter",
    "return": "enter",
    "space": "space",
    "tab": "tab",
}


def normalize_hotkey_list(hotkeys: str | list[str]) -> list[str]:
    if isinstance(hotkeys, str):
        items = re.split(r"[;,]", hotkeys)
    else:
        items = hotkeys
    return [item.strip().lower() for item in items if item.strip()]


def format_hotkey_label(hotkey: str) -> str:
    parts = [part.strip().lower() for part in hotkey.split("+") if part.strip()]
    labels: list[str] = []
    for part in parts[:-1]:
        modifier = MODIFIER_ALIASES.get(part, part)
        labels.append(
            {
                "ctrl": "Ctrl",
                "cmd": "Cmd",
                "alt": "Alt",
                "shift": "Shift",
            }.get(modifier, modifier.capitalize())
        )
    key = parts[-1] if parts else hotkey
    key = SPECIAL_KEYS.get(key, key)
    if key.startswith("f") and key[1:].isdigit():
        labels.append(key.upper())
    elif key == "esc":
        labels.append("Esc")
    else:
        labels.append(key.upper() if len(key) == 1 else key.capitalize())
    return "+".join(labels)


def format_hotkey_hint(hotkeys: str | list[str]) -> str:
    normalized = normalize_hotkey_list(hotkeys)
    if not normalized:
        return "Esc"
    return " / ".join(format_hotkey_label(item) for item in normalized)


class HotkeyService:
    def __init__(self, hotkeys: str | list[str] | None = None) -> None:
        self.hotkeys = normalize_hotkey_list(hotkeys or ["esc"])
        self._listener: keyboard.GlobalHotKeys | None = None
        self._lock = threading.Lock()

    @property
    def display_label(self) -> str:
        return format_hotkey_hint(self.hotkeys)

    def start_listening(self, on_cancel: Callable[[], None]) -> None:
        if keyboard is None:
            return

        self.stop_listening()
        mapping = {self._to_pynput(spec): on_cancel for spec in self.hotkeys}
        self._listener = keyboard.GlobalHotKeys(mapping)
        self._listener.start()

    def stop_listening(self) -> None:
        with self._lock:
            if self._listener is not None:
                self._listener.stop()
                self._listener = None

    def bind_tk_shortcuts(self, widget, callback: Callable[[], None]) -> None:
        for spec in self.hotkeys:
            sequence = self._to_tk_bind(spec)
            if sequence:
                widget.bind(sequence, lambda _event: callback(), add="+")

    def _to_pynput(self, spec: str) -> str:
        parts = [part.strip().lower() for part in spec.split("+") if part.strip()]
        if not parts:
            raise ValueError(f"รูปแบบ hotkey ไม่ถูกต้อง: {spec}")

        modifiers: list[str] = []
        key_part = parts[-1]
        for part in parts[:-1]:
            modifier = MODIFIER_ALIASES.get(part)
            if not modifier:
                raise ValueError(f"ไม่รู้จัก modifier: {part}")
            pynput_modifier = {
                "ctrl": "<ctrl>",
                "cmd": "<cmd>",
                "alt": "<alt>",
                "shift": "<shift>",
            }[modifier]
            if pynput_modifier not in modifiers:
                modifiers.append(pynput_modifier)

        key = SPECIAL_KEYS.get(key_part, key_part)
        if key == "esc":
            key_token = "<esc>"
        elif key.startswith("f") and key[1:].isdigit():
            key_token = key
        elif len(key) == 1:
            key_token = key
        else:
            key_token = f"<{key}>"

        if modifiers:
            return "+".join(modifiers + [key_token])
        return key_token

    def _to_tk_bind(self, spec: str) -> str | None:
        parts = [part.strip().lower() for part in spec.split("+") if part.strip()]
        if not parts:
            return None

        tk_modifiers: list[str] = []
        key_part = parts[-1]
        for part in parts[:-1]:
            modifier = MODIFIER_ALIASES.get(part)
            if modifier == "ctrl":
                tk_modifiers.append("Control")
            elif modifier == "cmd":
                tk_modifiers.append("Command")
            elif modifier == "alt":
                tk_modifiers.append("Alt")
            elif modifier == "shift":
                tk_modifiers.append("Shift")

        key = SPECIAL_KEYS.get(key_part, key_part)
        if key == "esc":
            tk_key = "Escape"
        elif key.startswith("f") and key[1:].isdigit():
            tk_key = key.upper()
        elif len(key) == 1:
            tk_key = key.lower()
        else:
            tk_key = key.capitalize()

        prefix = "-".join(tk_modifiers)
        return f"<{prefix}-{tk_key}>" if prefix else f"<{tk_key}>"

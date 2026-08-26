"""ตั้งไอคอนหน้าต่าง AutoKey — รองรับ Mac/Windows และ PyInstaller"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

from constants.routes import PROJECT_ROOT

_ICON_PHOTO_ATTR = "_autokey_icon_photo"


def assets_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
    return PROJECT_ROOT


def icon_dir() -> Path:
    return assets_root() / "assets" / "icon"


def apply_window_icon(window: tk.Misc) -> bool:
    icon_path = icon_dir()
    ico = icon_path / "app_icon.ico"
    png = icon_path / "app_icon.png"

    if sys.platform == "win32" and ico.exists():
        try:
            window.iconbitmap(default=str(ico))
            return True
        except tk.TclError:
            pass

    if not png.exists():
        return False

    try:
        from PIL import Image, ImageTk

        image = Image.open(png).convert("RGBA")
        image.thumbnail((128, 128), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        window.iconphoto(True, photo)
        setattr(window, _ICON_PHOTO_ATTR, photo)
        return True
    except Exception:
        return False


def load_title_photo(max_size: int = 48) -> tk.PhotoImage | None:
    png = icon_dir() / "app_icon.png"
    if not png.exists():
        return None
    try:
        from PIL import Image, ImageTk

        image = Image.open(png).convert("RGBA")
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)
    except Exception:
        return None

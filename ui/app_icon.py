"""ตั้งไอคอนหน้าต่าง AutoKey — Cocoa ใช้ path, Tk ใช้ apply_window_icon"""

from __future__ import annotations

import sys
from pathlib import Path

from constants.routes import PROJECT_ROOT

_ICON_PHOTO_ATTR = "_autokey_icon_photo"


def assets_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
    return PROJECT_ROOT


def icon_dir() -> Path:
    return assets_root() / "assets" / "icon"


def png_icon_path() -> Path:
    return icon_dir() / "app_icon.png"


def ico_icon_path() -> Path:
    return icon_dir() / "app_icon.ico"


def apply_window_icon(window) -> bool:
    import tkinter as tk

    ico = ico_icon_path()
    png = png_icon_path()

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


def load_title_photo(max_size: int = 48):
    png = png_icon_path()
    if not png.exists():
        return None
    try:
        from PIL import Image, ImageTk

        image = Image.open(png).convert("RGBA")
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)
    except Exception:
        return None

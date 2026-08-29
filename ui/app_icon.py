"""ตั้งไอคอนและ path ของไฟล์ไอคอน — ไม่ใช้ Tk"""

from __future__ import annotations

import sys
from pathlib import Path

from constants.routes import PROJECT_ROOT


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

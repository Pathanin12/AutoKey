from __future__ import annotations

import sys

if sys.platform == "darwin":
    from ui.cocoa_main_window import MainWindow
elif sys.platform == "win32":
    from ui.tk_main_window import MainWindow
else:
    raise RuntimeError("AutoKey รองรับเฉพาะ Windows และ macOS")

__all__ = ["MainWindow"]

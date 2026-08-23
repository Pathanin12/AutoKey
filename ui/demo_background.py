from __future__ import annotations

import tkinter as tk
from pathlib import Path

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover
    Image = None
    ImageTk = None

from models.screen_region import ScreenRegion


class DemoBackground:
    def __init__(
        self,
        root: tk.Tk,
        image_path: Path,
        base_width: int = 1920,
        base_height: int = 1080,
    ) -> None:
        self.root = root
        self.image_path = image_path
        self.base_width = base_width
        self.base_height = base_height
        self.window: tk.Toplevel | None = None
        self.offset_x = 0
        self.offset_y = 0
        self.display_width = base_width
        self.display_height = base_height
        self._photo = None

    def show(self) -> None:
        self.root.after(0, self._show_window)

    def hide(self) -> None:
        self.root.after(0, self._hide_window)

    def map_region(self, region: ScreenRegion) -> ScreenRegion:
        scale_x = self.display_width / self.base_width
        scale_y = self.display_height / self.base_height
        return ScreenRegion(
            x=int(self.offset_x + region.x * scale_x),
            y=int(self.offset_y + region.y * scale_y),
            width=max(int(region.width * scale_x), 40),
            height=max(int(region.height * scale_y), 24),
            label=region.label,
        )

    def _show_window(self) -> None:
        if Image is None or not self.image_path.exists():
            return
        if self.window is not None:
            return

        image = Image.open(self.image_path)
        image_width, image_height = image.size
        if image_width > self.base_width or image_height > self.base_height:
            self.base_width = image_width
            self.base_height = image_height

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        scale = min(screen_width / self.base_width, screen_height / self.base_height)
        self.display_width = int(self.base_width * scale)
        self.display_height = int(self.base_height * scale)
        self.offset_x = (screen_width - self.display_width) // 2
        self.offset_y = (screen_height - self.display_height) // 2

        resized = image.resize((self.display_width, self.display_height), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(resized)

        self.window = tk.Toplevel(self.root)
        self.window.title("AutoKey Demo")
        self.window.configure(bg="#000000")
        self.window.geometry(f"{screen_width}x{screen_height}+0+0")
        self.window.attributes("-topmost", False)

        canvas = tk.Canvas(self.window, width=screen_width, height=screen_height, highlightthickness=0, bg="#000000")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self._photo)

        tk.Label(
            self.window,
            text="โหมดทดสอบบน Mac — กรอบสีทองอิงจากรูป Express Accounting (ไม่ใช่หน้าจอจริงบน Windows)",
            bg="#111827",
            fg="#f9fafb",
            font=("Tahoma", 10, "bold"),
            padx=10,
            pady=6,
        ).place(x=12, y=12)

    def _hide_window(self) -> None:
        if self.window is not None:
            self.window.destroy()
            self.window = None
            self._photo = None

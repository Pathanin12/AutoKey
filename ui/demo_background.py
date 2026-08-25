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
    HIGHLIGHT_COLOR = "#FFD700"

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
        self.coord_base_width = base_width
        self.coord_base_height = base_height
        self.window: tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self.offset_x = 0
        self.offset_y = 0
        self.display_width = base_width
        self.display_height = base_height
        self._photo = None
        self._highlight_items: list[int | str] = []

    @property
    def is_ready(self) -> bool:
        return self._window_alive() and self.canvas is not None

    def _window_alive(self) -> bool:
        if self.window is None:
            return False
        try:
            return bool(self.window.winfo_exists())
        except tk.TclError:
            return False

    def show(self) -> None:
        self.root.after(0, self._show_window)

    def show_sync(self) -> None:
        self._show_window()
        if self.window is not None:
            self.window.update_idletasks()

    def hide(self) -> None:
        self.root.after(0, self._hide_window)

    def map_region(self, region: ScreenRegion) -> ScreenRegion:
        scaled = region.scaled(
            self.display_width,
            self.display_height,
            self.coord_base_width,
            self.coord_base_height,
        )
        return ScreenRegion(
            x=int(self.offset_x + scaled.x),
            y=int(self.offset_y + scaled.y),
            width=scaled.width,
            height=scaled.height,
            label=region.label,
        )

    def highlight(self, region: ScreenRegion) -> None:
        if not self.is_ready or self.canvas is None:
            return
        self.clear_highlight()
        scaled = region.scaled(
            self.display_width,
            self.display_height,
            self.coord_base_width,
            self.coord_base_height,
        )
        left = self.offset_x + scaled.x
        top = self.offset_y + scaled.y
        right = left + scaled.width
        bottom = top + scaled.height
        rect = self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            outline=self.HIGHLIGHT_COLOR,
            width=3,
            dash=(8, 4),
        )
        self._highlight_items.append(rect)
        if region.label:
            label_y = max(top - 18, self.offset_y + 4)
            text = self.canvas.create_text(
                left + 4,
                label_y,
                text=region.label,
                anchor="nw",
                fill="#FFFFFF",
                font=("Tahoma", 10, "bold"),
            )
            self._highlight_items.append(text)
        self.window.lift()

    def clear_highlight(self) -> None:
        if not self._window_alive() or self.canvas is None:
            self._highlight_items.clear()
            return
        for item in self._highlight_items:
            try:
                self.canvas.delete(item)
            except tk.TclError:
                pass
        self._highlight_items.clear()

    def _show_window(self) -> None:
        if Image is None or not self.image_path.exists():
            return
        if self._window_alive():
            self.window.deiconify()
            self.window.lift()
            return
        self.window = None
        self.canvas = None
        self._photo = None
        self._highlight_items.clear()

        image = Image.open(self.image_path)
        self.coord_base_width = self.base_width
        self.coord_base_height = self.base_height

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
        self.window.attributes("-topmost", True)

        self.canvas = tk.Canvas(self.window, width=screen_width, height=screen_height, highlightthickness=0, bg="#000000")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self._photo)

        tk.Label(
            self.window,
            text="โหมดทดสอบ — กรอบสีทอง = ตำแหน่งที่จับภาพเจอบนรูปนี้",
            bg="#111827",
            fg="#f9fafb",
            font=("Tahoma", 10, "bold"),
            padx=10,
            pady=6,
        ).place(x=12, y=12)

    def _hide_window(self) -> None:
        if not self._window_alive():
            self.window = None
            self.canvas = None
            self._photo = None
            self._highlight_items.clear()
            return
        self.clear_highlight()
        self.window.destroy()
        self.window = None
        self.canvas = None
        self._photo = None

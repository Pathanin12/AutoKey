from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from models.screen_region import ScreenRegion

if TYPE_CHECKING:
    from ui.demo_background import DemoBackground


class RegionHighlight:
    BORDER_COLOR = "#FFD700"
    FILL_COLOR = "#FFD700"

    def __init__(self, root: tk.Tk, base_width: int = 1920, base_height: int = 1080) -> None:
        self.root = root
        self.base_width = base_width
        self.base_height = base_height
        self.window: tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self.label_var = tk.StringVar(value="")

    def show(self, region: ScreenRegion, mapper: DemoBackground | None = None) -> None:
        self.root.after(0, lambda: self._draw(region, mapper))

    def hide(self) -> None:
        self.root.after(0, self._hide_window)

    def _draw(self, region: ScreenRegion, mapper: DemoBackground | None = None) -> None:
        if mapper is not None:
            scaled = mapper.map_region(region)
        else:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            scaled = region.scaled(screen_w, screen_h, self.base_width, self.base_height)
        label_height = 24 if scaled.label else 0
        total_height = scaled.height + label_height

        if self.window is None:
            self.window = tk.Toplevel(self.root)
            self.window.overrideredirect(True)
            self.window.attributes("-topmost", True)
            self.window.configure(bg=self.BORDER_COLOR)
            self.canvas = tk.Canvas(
                self.window,
                highlightthickness=0,
                bg="#111827",
            )
            self.canvas.pack(fill="both", expand=True, padx=3, pady=3)

            tk.Label(
                self.window,
                textvariable=self.label_var,
                bg=self.BORDER_COLOR,
                fg="#111827",
                font=("Tahoma", 9, "bold"),
                anchor="w",
                padx=6,
            ).pack(fill="x")

        self.label_var.set(scaled.label)
        self.window.geometry(f"{scaled.width + 6}x{total_height + 6}+{scaled.x}+{scaled.y}")
        self.window.deiconify()
        self.window.lift()

        if self.canvas is None:
            return

        self.canvas.configure(width=scaled.width, height=scaled.height)
        self.canvas.delete("all")
        self.canvas.create_rectangle(
            2,
            2,
            scaled.width - 2,
            scaled.height - 2,
            outline=self.BORDER_COLOR,
            width=3,
            dash=(8, 4),
        )

    def _hide_window(self) -> None:
        if self.window is not None:
            self.window.destroy()
            self.window = None
            self.canvas = None

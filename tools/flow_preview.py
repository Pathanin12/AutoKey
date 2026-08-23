#!/usr/bin/env python3
"""
ไล่ดู Flow สมุดรายวันจ่าย — แสดงทีละ action (Tab / Enter / พิมพ์ / กดปุ่ม)

ใช้งาน:
  python tools/flow_preview.py              # เปิดหน้าต่าง demo ไล่ทีละ action
  python tools/flow_preview.py --export     # บันทึกภาพ crop ตาม phase
  python tools/flow_preview.py --markdown   # บันทึก checklist ละเอียดเป็น Markdown
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError as exc:  # pragma: no cover
    raise SystemExit("ติดตั้ง Pillow ก่อน: pip install Pillow") from exc

import tkinter as tk
from tkinter import ttk

from constants.routes import PROJECT_ROOT as ROOT
from constants.step_regions import STEP_REGIONS
from models.workflow_action import WorkflowAction
from constants.flow_model import FULL_SEQUENCE_NOTE, PHASE_TITLES
from topics.ka_tam.workflow_actions import SAMPLE_VALUES, build_workflow_actions

REFERENCE_DIR = ROOT / "assets" / "reference"
EXPORT_DIR = ROOT / "assets" / "flow_preview"
DEFAULT_REFERENCE = REFERENCE_DIR / "11-3945f8bc-e840-4695-bfda-d310e4004dde.png"

IMAGE_PATHS: dict[str, Path] = {
    "menu": REFERENCE_DIR / "7-863dbbb2-42f7-4439-85c5-b1049836d310.png",
    "pv_main": DEFAULT_REFERENCE,
    "tax_dialog": REFERENCE_DIR / "14-c5a3186f-074c-4711-9354-a9852be04f12.png",
    "wt_dialog": REFERENCE_DIR / "wt_dialog_auto.png",
    "company_select": REFERENCE_DIR / "company_select_dialog.png",
}

KIND_COLORS = {
    "section": "#a855f7",
    "enter": "#ef4444",
    "key": "#3b82f6",
    "fkey": "#2563eb",
    "tab": "#8b5cf6",
    "type": "#16a34a",
    "click": "#d97706",
    "wait": "#6b7280",
}


def crop_with_highlight(image: Image.Image, region, padding: int = 12) -> Image.Image:
    left = max(region.x - padding, 0)
    top = max(region.y - padding, 0)
    right = min(region.x + region.width + padding, image.width)
    bottom = min(region.y + region.height + padding, image.height)
    cropped = image.crop((left, top, right, bottom)).convert("RGBA")

    overlay = Image.new("RGBA", cropped.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    box_left = region.x - left
    box_top = region.y - top
    draw.rectangle(
        (box_left, box_top, box_left + region.width, box_top + region.height),
        outline=(255, 215, 0, 255),
        width=4,
    )
    return Image.alpha_composite(cropped, overlay)


def export_phase_images() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for phase, title in PHASE_TITLES.items():
        image_path = IMAGE_PATHS.get("pv_main")
        if phase == 1:
            image_path = IMAGE_PATHS["menu"]
        elif phase == 6:
            image_path = IMAGE_PATHS["tax_dialog"]
        elif phase == 8:
            image_path = IMAGE_PATHS["wt_dialog"]

        region = STEP_REGIONS.get(phase)
        if region is None or not image_path.exists():
            print(f"ข้าม phase {phase}: ไม่พบรูปหรือ region")
            continue

        image = Image.open(image_path).convert("RGBA")
        highlighted = crop_with_highlight(image, region)
        safe_title = title.replace(" ", "_")
        output = EXPORT_DIR / f"phase_{phase:02d}_{safe_title}.png"
        highlighted.save(output)
        print(f"บันทึก {output.relative_to(ROOT)}")
    print(f"\nเสร็จ — ดูภาพใน {EXPORT_DIR}")


def export_markdown(actions: list[WorkflowAction]) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    output = EXPORT_DIR / "FLOW_DETAILED.md"
    lines = [
        "# AutoKey — Flow สมุดรายวันจ่าย (ละเอียด)",
        "",
        "ตัวอย่างค่าที่ใช้ demo:",
        "",
    ]
    for key, value in SAMPLE_VALUES.items():
        lines.append(f"- `{key}` = `{value}`")
    lines.extend(["", "---", ""])

    current_phase = 0
    for action in actions:
        if action.kind == "section":
            lines.extend(["", f"### {action.label}", ""])
            if action.note:
                lines.append(f"_{action.note}_")
            continue
        if action.phase != current_phase:
            current_phase = action.phase
            lines.extend(
                [
                    "",
                    f"## Phase {current_phase}: {action.phase_title}",
                    "",
                ]
            )
        line = f"{action.index}. **{action.kind_label_th}** — {action.label}"
        if action.value:
            line += f" → `{action.value}`"
        if action.note:
            line += f"  \n   _{action.note}_"
        lines.append(line)

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"บันทึก {output.relative_to(ROOT)} ({len(actions)} actions)")


class FlowPreviewApp:
    AUTOPLAY_MS = 2200

    def __init__(self, actions: list[WorkflowAction]) -> None:
        self.actions = actions
        self.root = tk.Tk()
        self.root.title(f"AutoKey — {FULL_SEQUENCE_NOTE}")
        self.root.geometry("1280x820")
        self.root.minsize(1080, 700)

        self.current_index = 0
        self.autoplay_job: str | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._full_image: Image.Image | None = None

        self.phase_text = tk.StringVar()
        self.action_counter = tk.StringVar()
        self.kind_text = tk.StringVar()
        self.action_title = tk.StringVar()
        self.action_value = tk.StringVar()
        self.action_note = tk.StringVar()

        self._build_ui()
        self._show_action(0)

    def _build_ui(self) -> None:
        header = ttk.Label(
            self.root,
            text=FULL_SEQUENCE_NOTE,
            font=("Tahoma", 11, "bold"),
        )
        header.pack(fill="x", padx=12, pady=(12, 6))

        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=12, pady=6)

        self.canvas = tk.Canvas(body, bg="#111827", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        side = ttk.Frame(body, width=420)
        side.pack(side="right", fill="y", padx=(12, 0))
        side.pack_propagate(False)

        ttk.Label(side, textvariable=self.phase_text, font=("Tahoma", 10, "bold")).pack(anchor="w")
        ttk.Label(side, textvariable=self.action_counter, font=("Tahoma", 10)).pack(anchor="w", pady=(2, 8))

        detail_box = ttk.LabelFrame(side, text="Action ปัจจุบัน")
        detail_box.pack(fill="x", pady=(0, 8))

        self.kind_label = tk.Label(
            detail_box,
            textvariable=self.kind_text,
            font=("Tahoma", 14, "bold"),
            fg="#fbbf24",
            anchor="w",
            padx=8,
            pady=4,
        )
        self.kind_label.pack(fill="x")

        ttk.Label(
            detail_box,
            textvariable=self.action_title,
            wraplength=380,
            font=("Tahoma", 11, "bold"),
        ).pack(anchor="w", padx=8, pady=(4, 2))

        ttk.Label(detail_box, textvariable=self.action_value, wraplength=380, foreground="#166534").pack(
            anchor="w", padx=8
        )
        ttk.Label(detail_box, textvariable=self.action_note, wraplength=380, foreground="#555555").pack(
            anchor="w", padx=8, pady=(2, 8)
        )

        ttk.Separator(side).pack(fill="x", pady=6)
        ttk.Label(side, text="รายการ action ทั้งหมด", font=("Tahoma", 10, "bold")).pack(anchor="w")

        list_frame = ttk.Frame(side)
        list_frame.pack(fill="both", expand=True, pady=(4, 8))
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.action_list = tk.Listbox(
            list_frame,
            height=22,
            exportselection=False,
            yscrollcommand=scrollbar.set,
            font=("Menlo", 9),
        )
        self.action_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.action_list.yview)

        for action in actions:
            if action.kind == "section":
                self.action_list.insert("end", f"── {action.label}")
            else:
                prefix = f"P{action.phase} "
                self.action_list.insert("end", prefix + action.display_line[4:])
        self.action_list.bind("<<ListboxSelect>>", self._on_list_select)

        buttons = ttk.Frame(side)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="◀ ก่อนหน้า", command=self._prev_action).pack(side="left")
        ttk.Button(buttons, text="ถัดไป ▶", command=self._next_action).pack(side="left", padx=6)
        ttk.Button(buttons, text="▶ เล่นอัตโนมัติ", command=self._toggle_autoplay).pack(side="left")

        phase_buttons = ttk.Frame(side)
        phase_buttons.pack(fill="x", pady=(8, 0))
        ttk.Label(phase_buttons, text="กระโดด Phase:").pack(side="left")
        for phase in sorted(PHASE_TITLES):
            ttk.Button(
                phase_buttons,
                text=str(phase),
                width=3,
                command=lambda p=phase: self._jump_phase(p),
            ).pack(side="left", padx=1)

        footer = ttk.Frame(self.root)
        footer.pack(fill="x", padx=12, pady=12)
        ttk.Label(
            footer,
            text=(
                "Enter = ยืนยันแถวตาราง / ปิด Dialog | "
                "Tab = ขยับช่อง | ค่าตัวอย่างจาก topics/ka_tam/workflow_actions.py"
            ),
        ).pack(side="left")

    def _show_action(self, index: int) -> None:
        self.current_index = max(0, min(index, len(self.actions) - 1))
        action = self.actions[self.current_index]

        self.phase_text.set(f"Phase {action.phase}/10 — {action.phase_title}")
        self.action_counter.set(f"Action {action.index} / {len(self.actions)}")
        self.kind_text.set(action.kind_label_th.upper())
        self.action_title.set(action.label)
        self.action_value.set(f"ค่า: {action.value}" if action.value else "")
        self.action_note.set(action.note)

        color = KIND_COLORS.get(action.kind, "#fbbf24")
        self.kind_label.configure(fg=color)
        if action.kind == "section":
            self.kind_text.set("—")
            self.action_value.set("")
            self.action_note.set(action.note or action.label)

        self.action_list.selection_clear(0, "end")
        self.action_list.selection_set(self.current_index)
        self.action_list.see(self.current_index)

        if action.kind == "section":
            self.canvas.delete("all")
            self.canvas.create_text(
                40,
                40,
                anchor="nw",
                fill="#c4b5fd",
                text=action.label,
                font=("Tahoma", 16, "bold"),
                width=max(self.canvas.winfo_width() - 80, 400),
            )
            if action.note:
                self.canvas.create_text(
                    40,
                    100,
                    anchor="nw",
                    fill="#9ca3af",
                    text=action.note,
                    font=("Tahoma", 12),
                    width=max(self.canvas.winfo_width() - 80, 400),
                )
            return

        image_path = IMAGE_PATHS.get(action.image_key, IMAGE_PATHS["pv_main"])
        region = STEP_REGIONS.get(action.region_step)

        if not image_path.exists() or region is None:
            self.canvas.delete("all")
            missing = []
            if not image_path.exists():
                missing.append(f"ไม่พบรูป: {image_path.name}")
            if region is None:
                missing.append(f"ไม่พบ region step {action.region_step}")
            self.canvas.create_text(
                40,
                40,
                anchor="nw",
                fill="#f87171",
                text="\n".join(missing),
                font=("Tahoma", 12),
            )
            return

        self._full_image = Image.open(image_path).convert("RGBA")
        self._render_canvas(region, action.phase_title)

    def _render_canvas(self, region, label: str) -> None:
        assert self._full_image is not None
        canvas_w = max(self.canvas.winfo_width(), 640)
        canvas_h = max(self.canvas.winfo_height(), 480)
        image = self._full_image.copy()

        scale = min(canvas_w / image.width, canvas_h / image.height)
        display_w = int(image.width * scale)
        display_h = int(image.height * scale)
        offset_x = (canvas_w - display_w) // 2
        offset_y = (canvas_h - display_h) // 2

        resized = image.resize((display_w, display_h), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(resized)
        rx = int(region.x * scale)
        ry = int(region.y * scale)
        rw = int(region.width * scale)
        rh = int(region.height * scale)
        draw.rectangle((rx, ry, rx + rw, ry + rh), outline=(255, 215, 0), width=4)

        self._photo = ImageTk.PhotoImage(resized)
        self.canvas.delete("all")
        self.canvas.create_image(offset_x, offset_y, anchor="nw", image=self._photo)
        self.canvas.create_text(
            offset_x + 8,
            offset_y + 8,
            anchor="nw",
            text=label,
            fill="#FFD700",
            font=("Tahoma", 11, "bold"),
        )

    def _prev_action(self) -> None:
        self._stop_autoplay()
        self._show_action(self.current_index - 1)

    def _next_action(self) -> None:
        self._stop_autoplay()
        if self.current_index >= len(self.actions) - 1:
            self._show_action(0)
            return
        self._show_action(self.current_index + 1)

    def _jump_phase(self, phase: int) -> None:
        self._stop_autoplay()
        for index, action in enumerate(self.actions):
            if action.phase == phase:
                self._show_action(index)
                return

    def _toggle_autoplay(self) -> None:
        if self.autoplay_job:
            self._stop_autoplay()
            return
        self._autoplay_tick()

    def _autoplay_tick(self) -> None:
        if self.current_index >= len(self.actions) - 1:
            self._stop_autoplay()
            return
        self._show_action(self.current_index + 1)
        self.autoplay_job = self.root.after(self.AUTOPLAY_MS, self._autoplay_tick)

    def _stop_autoplay(self) -> None:
        if self.autoplay_job:
            self.root.after_cancel(self.autoplay_job)
            self.autoplay_job = None

    def _on_list_select(self, _event) -> None:
        selection = self.action_list.curselection()
        if not selection:
            return
        self._stop_autoplay()
        self._show_action(selection[0])

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    actions = build_workflow_actions(use_work_date=True)

    if "--export" in sys.argv:
        export_phase_images()
        return
    if "--markdown" in sys.argv:
        export_markdown(actions)
        return

    app = FlowPreviewApp(actions)
    app.run()


if __name__ == "__main__":
    main()

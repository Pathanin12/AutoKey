from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowAction:
    index: int
    phase: int
    phase_title: str
    kind: str
    label: str
    value: str = ""
    note: str = ""
    region_step: int = 1
    image_key: str = "pv_main"

    @property
    def display_line(self) -> str:
        if self.value:
            return f"{self.index:03d}. [{self.kind.upper()}] {self.label} → {self.value}"
        return f"{self.index:03d}. [{self.kind.upper()}] {self.label}"

    @property
    def kind_label_th(self) -> str:
        labels = {
            "key": "กดปุ่ม",
            "fkey": "ฟังก์ชันคีย์",
            "tab": "Tab",
            "enter": "Enter",
            "type": "พิมพ์",
            "click": "คลิก",
            "wait": "รอ",
            "section": "—",
        }
        return labels.get(self.kind, self.kind)

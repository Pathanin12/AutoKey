from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunFailureError(RuntimeError):
    """หยุด automation พร้อมสรุปความคืบหน้า"""

    message: str
    completed_count: int
    failed_no: int
    failed_name: str
    sheet_name: str = ""

    def __str__(self) -> str:
        return self.format_summary()

    def with_completed_offset(self, offset: int) -> RunFailureError:
        return RunFailureError(
            message=self.message,
            completed_count=self.completed_count + offset,
            failed_no=self.failed_no,
            failed_name=self.failed_name,
            sheet_name=self.sheet_name,
        )

    def format_summary(self) -> str:
        lines = [
            "⚠ หยุดทำงาน — ค้นหา vendor ไม่พบหรือไม่ตรง",
            self.message,
            f"ทำสำเร็จแล้ว {self.completed_count} บริษัท",
            f"หยุดที่ No {self.failed_no} — {self.failed_name}",
        ]
        if self.sheet_name:
            lines.append(f"ชีต: {self.sheet_name}")
        return "\n".join(lines)

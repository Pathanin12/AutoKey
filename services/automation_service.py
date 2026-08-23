from __future__ import annotations

import threading
from dataclasses import replace
from pathlib import Path
from typing import Callable

import yaml

from constants.flow_model import FLOW_1_END_LABEL, FLOW_1_LABEL
from constants.routes import CONFIG_PATH, TEMPLATES_DIR, TOPIC_LABEL
from models.run_config import RunConfig
from services.company_switch_service import CompanySwitchSettings
from services.excel_service import ExcelService
from services.image_service import ImageService
from topics.ka_tam.workflow import KaTamWorkflow


class AutomationService:
    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self.config_path = config_path
        self.config = self._load_config()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def _load_config(self) -> dict:
        if not self.config_path.exists():
            return {}
        with self.config_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    @property
    def automation_settings(self) -> dict:
        return self.config.get("automation", {})

    @property
    def ui_settings(self) -> dict:
        return self.config.get("ui", {})

    @property
    def dry_run(self) -> bool:
        return bool(self.automation_settings.get("dry_run", False))

    @property
    def company_switch_settings(self) -> CompanySwitchSettings:
        raw = self.config.get("company_switch", {})
        submenu = raw.get("submenu_keys")
        if submenu is None:
            submenu = []
        return CompanySwitchSettings(
            menu_others=str(raw.get("menu_others", "8")),
            submenu_keys=[str(key) for key in submenu],
            menu_wait=float(raw.get("menu_wait", 0.8)),
            use_search_button=bool(raw.get("use_search_button", True)),
            search_enter_count=int(raw.get("search_enter_count", 2)),
            dismiss_work_date=bool(raw.get("dismiss_work_date", True)),
        )

    def create_image_service(self) -> ImageService:
        settings = self.automation_settings
        return ImageService(
            templates_dir=TEMPLATES_DIR,
            confidence=float(settings.get("confidence", 0.85)),
            action_delay=float(settings.get("action_delay", 0.4)),
            type_interval=float(settings.get("type_interval", 0.03)),
            fail_safe=bool(settings.get("fail_safe", True)),
        )

    def request_stop(self) -> None:
        self._stop_event.set()

    def reset_stop(self) -> None:
        self._stop_event.clear()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def run_async(
        self,
        run_config: RunConfig,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        on_finished: Callable[[bool, str], None],
        on_step: Callable[[int, str, str], None] | None = None,
        on_highlight: Callable[[object], None] | None = None,
    ) -> None:
        if self.is_running():
            on_finished(False, "ระบบกำลังทำงานอยู่")
            return

        errors = run_config.validate()
        if errors:
            on_finished(False, "\n".join(errors))
            return

        self.reset_stop()

        def worker() -> None:
            try:
                sheet_summaries = run_config.sheet_summaries or ExcelService.load_sheet_summaries(
                    run_config.excel_path
                )
                if not sheet_summaries:
                    on_finished(False, "ไม่พบข้อมูลในไฟล์ Excel")
                    return

                image = self.create_image_service()
                workflow = KaTamWorkflow(
                    image_service=image,
                    stop_event=self._stop_event,
                    on_status=on_status,
                    on_progress=on_progress,
                    on_step=on_step,
                    on_highlight=on_highlight,
                    dry_run=self.dry_run,
                    company_switch_settings=self.company_switch_settings,
                )

                total_rows = sum(summary.row_count for summary in sheet_summaries)
                processed_rows = 0

                # โฟล์แรก — อยู่หน้าเลือกข้อมูลแล้ว → กด ค้นหา ให้เลย (ไม่กด 8)
                on_status(f"{FLOW_1_LABEL}: {run_config.company_name.strip()}")
                workflow.select_company_flow(
                    run_config.company_name.strip(),
                    is_final=False,
                )

                for sheet_index, summary in enumerate(sheet_summaries):
                    self._check_stop()
                    on_status(f"ชีต {summary.name}: {summary.row_count} รายการ")
                    rows = ExcelService.load_ka_tam_rows(run_config.excel_path, summary.name)
                    if not rows:
                        continue

                    sheet_config = replace(run_config, switch_company=False)

                    def progress_callback(current: int, total: int) -> None:
                        on_progress(processed_rows + current, total_rows)
                        if on_step:
                            on_step(
                                0,
                                "กำลังทำรายการ",
                                f"{processed_rows + current} / {total_rows} — {rows[current - 1].legal_name}",
                            )

                    workflow.run(sheet_config, rows, progress_callback=progress_callback)
                    processed_rows += len(rows)

                if run_config.switch_company and run_config.next_company_name.strip():
                    on_status(
                        f"{FLOW_1_END_LABEL}: {run_config.next_company_name.strip()}"
                    )
                    workflow.select_company_flow(
                        run_config.next_company_name.strip(),
                        is_final=True,
                    )

                mode = " (โหมดทดสอบ)" if self.dry_run else ""
                if self._stop_event.is_set():
                    on_finished(False, "หยุดโดยผู้ใช้")
                else:
                    on_finished(True, f"เสร็จสิ้น {processed_rows} รายการ ({TOPIC_LABEL}){mode}")
            except InterruptedError:
                on_finished(False, "หยุดโดยผู้ใช้")
            except Exception as exc:  # pragma: no cover
                on_finished(False, str(exc))

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def _check_stop(self) -> None:
        if self._stop_event.is_set():
            raise InterruptedError("หยุดโดยผู้ใช้")

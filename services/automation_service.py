from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import yaml

from constants.routes import CONFIG_PATH, SCREEN_HEIGHT, SCREEN_WIDTH, TOPIC_LABEL
from constants.template_actions import DEFAULT_TEMPLATE_CLICK_ACTIONS
from models.run_config import RunConfig
from models.template_click_settings import TemplateClickAction, TemplateClickSettings
from models.template_target import TemplateTarget
from models.window_focus_settings import WindowFocusSettings
from services.company_switch_service import CompanySwitchSettings
from services.excel_service import ExcelService
from services.image_service import ImageService
from services.lookup_search_service import LookupSearchSettings
from services.template_click_service import TemplateClickService
from services.window_focus_service import focus_express_window
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
    def default_settings(self) -> dict:
        return self.config.get("defaults", {})

    @property
    def ui_settings(self) -> dict:
        return self.config.get("ui", {})

    @property
    def dry_run(self) -> bool:
        return bool(self.automation_settings.get("dry_run", False))

    @property
    def screen_settings(self) -> dict:
        return self.config.get("screen", {})

    @property
    def template_click_settings(self) -> TemplateClickSettings:
        raw = self.config.get("template_click", {})
        actions_raw = raw.get("actions") or {}
        if actions_raw:
            actions = tuple(self._parse_template_click_action(action_id, item) for action_id, item in actions_raw.items())
        else:
            actions = DEFAULT_TEMPLATE_CLICK_ACTIONS
        return TemplateClickSettings(
            enabled=bool(raw.get("enabled", True)),
            fallback_to_keyboard=bool(raw.get("fallback_to_keyboard", True)),
            dry_run_reference=str(raw.get("dry_run_reference", "assets/reference/2.png")),
            actions=actions,
        )

    def _parse_template_click_action(self, action_id: str, item: dict) -> TemplateClickAction:
        region = item.get("search_region")
        search_region = tuple(int(value) for value in region) if region else None
        target = TemplateTarget(
            step_id=str(action_id),
            label=str(item.get("label", action_id)),
            template_file=str(item["template_file"]),
            match_threshold=float(item.get("match_threshold", 0.88)),
            crop_x=int(item.get("crop_x", 0)),
            crop_y=int(item.get("crop_y", 0)),
            crop_width=int(item["crop_width"]) if item.get("crop_width") is not None else None,
            crop_height=int(item["crop_height"]) if item.get("crop_height") is not None else None,
        )
        return TemplateClickAction(
            action_id=str(action_id),
            target=target,
            search_region=search_region,  # type: ignore[arg-type]
        )

    @property
    def lookup_search_settings(self) -> LookupSearchSettings:
        raw = self.config.get("lookup_search", {})
        return LookupSearchSettings(
            button_tabs=int(raw.get("button_tabs", 2)),
            field_tabs=int(raw.get("field_tabs", 0)),
            confirm_enter_count=int(raw.get("confirm_enter_count", 1)),
        )

    @property
    def company_switch_settings(self) -> CompanySwitchSettings:
        raw = self.config.get("company_switch", {})
        submenu = raw.get("submenu_keys")
        if submenu is None:
            submenu = ["8"]
        lookup = self.lookup_search_settings
        return CompanySwitchSettings(
            menu_others=str(raw.get("menu_others", "8")),
            submenu_keys=[str(key) for key in submenu],
            menu_wait=float(raw.get("menu_wait", 0.8)),
            lookup_search=lookup,
            search_enter_count=int(raw.get("search_enter_count", 2)),
            exit_pv_esc_count=int(raw.get("exit_pv_esc_count", 2)),
        )

    @property
    def window_focus_settings(self) -> WindowFocusSettings:
        raw = self.config.get("window_focus", {})
        return WindowFocusSettings(
            enabled=bool(raw.get("enabled", True)),
            title_contains=str(raw.get("title_contains", "Express")),
            prepare_seconds=float(raw.get("prepare_seconds", 0.3)),
            wait_after_focus_seconds=float(raw.get("wait_after_focus_seconds", 0.5)),
            required=bool(raw.get("required", True)),
        )

    def create_image_service(self) -> ImageService:
        settings = self.automation_settings
        screen = self.screen_settings
        return ImageService(
            action_delay=float(settings.get("action_delay", 0.4)),
            type_interval=float(settings.get("type_interval", 0.03)),
            fail_safe=bool(settings.get("fail_safe", True)),
            screen_width=int(screen.get("width", SCREEN_WIDTH)),
            screen_height=int(screen.get("height", SCREEN_HEIGHT)),
            dry_run=self.dry_run,
            dry_run_delay=float(settings.get("dry_run_step_delay", 0.8)),
        )

    def create_template_click_service(
        self,
        image: ImageService,
        *,
        on_status: Callable[[str], None],
    ) -> TemplateClickService:
        return TemplateClickService(
            image,
            self.template_click_settings,
            dry_run=self.dry_run,
            on_status=on_status,
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

                if not self.dry_run:
                    focus_express_window(self.window_focus_settings, on_status=on_status)
                    self._check_stop()

                image = self.create_image_service()
                template_click = self.create_template_click_service(
                    image,
                    on_status=on_status,
                )
                workflow = KaTamWorkflow(
                    image_service=image,
                    stop_event=self._stop_event,
                    on_status=on_status,
                    on_progress=on_progress,
                    on_step=on_step,
                    dry_run=self.dry_run,
                    dry_run_delay=float(self.automation_settings.get("dry_run_step_delay", 0.8)),
                    company_switch_settings=self.company_switch_settings,
                    lookup_search_settings=self.lookup_search_settings,
                    template_click_service=template_click,
                )

                total_rows = sum(summary.row_count for summary in sheet_summaries)
                processed_rows = 0

                for sheet_index, summary in enumerate(sheet_summaries):
                    self._check_stop()
                    on_status(f"ทำรายการ: {summary.row_count} แถว")
                    rows = ExcelService.load_ka_tam_rows(run_config.excel_path, summary.name)
                    if not rows:
                        continue

                    def progress_callback(current: int, total: int) -> None:
                        on_progress(processed_rows + current, total_rows)
                        if on_step:
                            on_step(
                                0,
                                "กำลังทำรายการ",
                                f"{processed_rows + current} / {total_rows} — {rows[current - 1].legal_name}",
                            )

                    workflow.run(run_config, rows, progress_callback=progress_callback)
                    processed_rows += len(rows)

                self._check_stop()
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

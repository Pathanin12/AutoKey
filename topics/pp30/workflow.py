from __future__ import annotations

import threading
from typing import Callable

from constants.routes import MENU_GENERAL_JOURNAL_PATH, UI_TEXT
from models.pp30_matched_job import Pp30MatchedJob
from services.company_switch_service import CompanySwitchSettings, open_change_company_menu
from services.image_service import ImageService
from services.lookup_search_service import LookupSearchSettings, search_and_select
from services.menu_navigation_service import open_general_journal_menu
from services.template_click_service import TemplateClickService


class Pp30Workflow:
    def __init__(
        self,
        image_service: ImageService,
        stop_event: threading.Event,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        lookup_search_settings: LookupSearchSettings,
        company_switch_settings: CompanySwitchSettings | None,
        template_click_service: TemplateClickService | None,
    ) -> None:
        self.image = image_service
        self.stop_event = stop_event
        self.on_status = on_status
        self.on_progress = on_progress
        self.lookup_search_settings = lookup_search_settings
        self.company_switch_settings = company_switch_settings
        self.template_click = template_click_service

    def search_companies(self, jobs: list[Pp30MatchedJob]) -> None:
        total = len(jobs)
        for index, job in enumerate(jobs, start=1):
            self._check_stop()
            self.on_progress(index, total)
            self.on_status(
                UI_TEXT["pp30_match_log"].format(pdf_name=job.pdf_name, excel_name=job.excel_name)
            )
            if index > 1:
                self._open_next_company_dialog()
            self._search_company(job.excel_name)
            self._open_general_journal()
            self.on_status(f"✓ [{index}/{total}] {job.excel_name}")

    def _open_next_company_dialog(self) -> None:
        if self.company_switch_settings is None:
            raise RuntimeError("ยังไม่ได้ตั้งค่าการเปลี่ยนบริษัท")
        open_change_company_menu(self.image, self.company_switch_settings)

    def _search_company(self, excel_name: str) -> None:
        name = excel_name.strip()
        if not name:
            raise RuntimeError("ไม่พบชื่อ Excel สำหรับค้นหา")
        self.on_status(UI_TEXT["pp30_search_log"].format(name=name))
        search_and_select(
            self.image,
            self.lookup_search_settings,
            name,
            template_click=self.template_click,
            on_status=self.on_status,
            should_stop=self.stop_event.is_set,
        )

    def _open_general_journal(self) -> None:
        if self.template_click is None:
            raise RuntimeError("ต้องเปิด template_click และจับภาพเมนู 5-1-1")
        self.on_status(f"เปิดเมนู {MENU_GENERAL_JOURNAL_PATH}")
        self.image.wait(0.8)
        open_general_journal_menu(
            self.image,
            self.template_click,
            on_status=self.on_status,
            template_retries=self.lookup_search_settings.template_retries,
            template_retry_delay=self.lookup_search_settings.template_retry_delay,
        )

    def _check_stop(self) -> None:
        if self.stop_event.is_set():
            raise InterruptedError("หยุดโดยผู้ใช้")

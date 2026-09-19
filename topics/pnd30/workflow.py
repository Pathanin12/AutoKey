from __future__ import annotations

import threading
from typing import Callable

from constants.routes import UI_TEXT
from models.pnd30_fill_context import Pnd30FillContext
from models.pnd30_form_config import Pnd30FormConfig
from models.pnd30_matched_job import Pnd30MatchedJob
from services.company_switch_service import CompanySwitchSettings
from services.image_service import ImageService
from services.lookup_search_service import LookupSearchSettings, search_and_select
from services.pnd30_fill_service import Pnd30FillService
from services.template_click_service import TemplateClickService


class Pnd30Workflow:
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

    def search_companies(self, jobs: list[Pnd30MatchedJob], form_config: Pnd30FormConfig) -> None:
        total = len(jobs)
        for index, job in enumerate(jobs, start=1):
            self._check_stop()
            self.on_progress(index, total)
            self.on_status(
                UI_TEXT["pp30_match_log"].format(pdf_name=job.pdf_name, excel_name=job.excel_name)
            )
            self._search_company(job.excel_name)
            Pnd30FillService.run(self._fill_context(form_config, job))
            self.on_status(f"✓ [{index}/{total}] {job.excel_name}")

    def _fill_context(self, form_config: Pnd30FormConfig, job: Pnd30MatchedJob) -> Pnd30FillContext:
        if self.template_click is None:
            raise RuntimeError("ต้องเปิด template_click และจับภาพเมนู")
        return Pnd30FillContext(
            image=self.image,
            template_click=self.template_click,
            form_config=form_config,
            job=job,
            on_status=self.on_status,
            should_stop=self.stop_event.is_set,
            template_retries=self.lookup_search_settings.template_retries,
            template_retry_delay=self.lookup_search_settings.template_retry_delay,
        )

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

    def _check_stop(self) -> None:
        if self.stop_event.is_set():
            raise InterruptedError("หยุดโดยผู้ใช้")

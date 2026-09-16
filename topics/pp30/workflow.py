from __future__ import annotations

import threading
from typing import Callable

from constants.routes import (
    MENU_GENERAL_JOURNAL_PATH,
    MENU_OPEN_PRE_WAIT,
    UI_TEXT,
)
from models.pp30_fill_context import Pp30FillContext
from models.pp30_form_config import Pp30FormConfig
from models.pp30_matched_job import Pp30MatchedJob
from services.company_switch_service import CompanySwitchSettings
from services.image_service import ImageService
from services.lookup_search_service import LookupSearchSettings, search_and_select
from services.menu_navigation_service import open_general_journal_menu
from services.pp30_classify_service import Pp30ClassifyService
from services.pp30_fill_new_shop_service import Pp30FillNewShopService
from services.pp30_fill_no_pay_normal_service import Pp30FillNoPayNormalService
from services.pp30_fill_normal_service import Pp30FillNormalService
from services.pp30_fill_pay_service import Pp30FillPayService
from services.pp30_fill_penalty_service import Pp30FillPenaltyService
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

    def search_companies(self, jobs: list[Pp30MatchedJob], form_config: Pp30FormConfig) -> None:
        total = len(jobs)
        self.on_status(UI_TEXT["pp30_mode_log"].format(mode=form_config.run_mode.label))
        for index, job in enumerate(jobs, start=1):
            self._check_stop()
            self.on_progress(index, total)
            self.on_status(
                UI_TEXT["pp30_match_log"].format(pdf_name=job.pdf_name, excel_name=job.excel_name)
            )
            if form_config.run_mode.is_special:
                ran = self._run_special(form_config, job)
            else:
                ran = self._run_normal(form_config, job)
            if ran:
                self.on_status(f"✓ [{index}/{total}] {job.excel_name}")

    def _run_normal(self, form_config: Pp30FormConfig, job: Pp30MatchedJob) -> bool:
        kind = Pp30ClassifyService.classify(job.form_values)
        self.on_status(UI_TEXT["pp30_kind_log"].format(kind=kind.label))
        if kind.is_skip:
            self.on_status(UI_TEXT["pp30_skip_zero_log"].format(name=job.excel_name))
            return False
        if not kind.runs_on_normal:
            self.on_status(
                UI_TEXT["pp30_skip_not_pay_log"].format(name=job.excel_name, kind=kind.label)
            )
            return False
        self._search_company(job.excel_name)
        if kind.is_penalty:
            Pp30FillPenaltyService.run(self._fill_context(form_config, job))
        elif kind.is_pay:
            Pp30FillPayService.run(self._fill_context(form_config, job))
        else:
            Pp30FillNormalService.run(self._fill_context(form_config, job))
        return True

    def _run_special(self, form_config: Pp30FormConfig, job: Pp30MatchedJob) -> bool:
        kind = Pp30ClassifyService.classify(job.form_values)
        self.on_status(UI_TEXT["pp30_kind_log"].format(kind=kind.label))
        if kind.is_skip:
            self.on_status(UI_TEXT["pp30_skip_zero_log"].format(name=job.excel_name))
            return False
        if not kind.runs_on_special:
            self.on_status(
                UI_TEXT["pp30_skip_pay_log"].format(name=job.excel_name, kind=kind.label)
            )
            return False
        self._search_company(job.excel_name)
        if kind.is_new_shop:
            Pp30FillNewShopService.run(self._fill_context(form_config, job))
        elif kind.is_no_pay_normal:
            Pp30FillNoPayNormalService.run(self._fill_context(form_config, job))
        else:
            self._open_general_journal()
        return True

    def _fill_context(self, form_config: Pp30FormConfig, job: Pp30MatchedJob) -> Pp30FillContext:
        if self.template_click is None:
            raise RuntimeError("ต้องเปิด template_click และจับภาพเมนู")
        return Pp30FillContext(
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

    def _open_general_journal(self) -> None:
        if self.template_click is None:
            raise RuntimeError("ต้องเปิด template_click และจับภาพเมนู 5-1-1")
        self.on_status(f"เปิดเมนู {MENU_GENERAL_JOURNAL_PATH}")
        self.image.wait(MENU_OPEN_PRE_WAIT)
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

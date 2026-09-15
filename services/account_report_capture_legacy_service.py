"""ชุดเรียกรายงานแบบจับภาพเมนู F12 — ไม่ถูกใช้ตอนรัน เก็บไว้ถ้าจะสลับกลับ"""

from __future__ import annotations

from typing import Callable

from constants.routes import (
    ACCOUNT_REPORT_CAPTURE_WAIT,
    ACCOUNT_REPORT_FIELD_WAIT,
    ACCOUNT_REPORT_MENU_WAIT,
    MENU_ACCOUNT_REPORT_LABEL,
    MENU_GENERAL_LEDGER_LABEL,
    MENU_LEDGER_REPORT_PATH,
    MENU_REPORT_NORMAL_LABEL,
)
from constants.template_actions import REPORT_NORMAL_ACTION_IDS
from models.account_report_capture_job import AccountReportCaptureJob
from services.image_service import ImageService
from services.template_click_service import TemplateClickService, TemplateNotFoundError


def should_expand_ledger_report_tree(job_index: int, *, tree_already_open: bool) -> bool:
    return not tree_already_open and job_index == 0


def capture_account_reports(
    image: ImageService,
    template_click: TemplateClickService,
    jobs: tuple[AccountReportCaptureJob, ...],
    *,
    expand_tree_first: bool = True,
    on_status: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
    template_retries: int = 4,
    template_retry_delay: float = 0.15,
    capture_wait: float = ACCOUNT_REPORT_CAPTURE_WAIT,
    field_wait: float = ACCOUNT_REPORT_FIELD_WAIT,
) -> None:
    for index, job in enumerate(jobs):
        if should_stop and should_stop():
            raise InterruptedError("หยุดโดยผู้ใช้")
        if on_status:
            on_status(f"แคปรายงาน {job.account_code}")
        open_ledger_normal_report_menu(
            image,
            template_click,
            expand_tree=should_expand_ledger_report_tree(
                index,
                tree_already_open=not expand_tree_first,
            ),
            on_status=on_status,
            template_retries=template_retries,
            template_retry_delay=template_retry_delay,
            menu_wait=ACCOUNT_REPORT_MENU_WAIT,
        )
        image.wait(field_wait)
        _type_report_field(image, job.account_code)
        _type_report_field(image, job.account_code)
        _type_report_field(image, job.start_date)
        _type_report_field(image, job.end_date)
        image.press("f5")
        image.press("enter")
        image.wait(capture_wait)
        saved = image.save_screenshot(job.output_file)
        if on_status:
            on_status(f"บันทึกแคป {job.account_code}: {saved}")


def open_ledger_normal_report_menu(
    image: ImageService,
    template_click: TemplateClickService,
    *,
    expand_tree: bool = True,
    on_status: Callable[[str], None] | None = None,
    template_retries: int = 4,
    template_retry_delay: float = 0.15,
    menu_wait: float = 0.35,
) -> None:
    if not template_click.enabled:
        raise RuntimeError("ต้องเปิด template_click และจับภาพเมนูรายงานบัญชี")

    image.press("f12")
    image.wait(menu_wait)

    if not expand_tree:
        try:
            _retry_action(
                lambda: template_click.click_first(REPORT_NORMAL_ACTION_IDS),
                image=image,
                retries=report_reopen_retries(template_retries),
                retry_delay=template_retry_delay,
            )
            image.wait(menu_wait)
            return
        except TemplateNotFoundError:
            _status(on_status, "ไม่เจอแบบปกติ — เปิดต้นไม้รายงานอีกครั้ง")

    _status(on_status, f"เปิดเมนู {MENU_LEDGER_REPORT_PATH}")
    _expand_ledger_report_tree(
        image,
        template_click,
        on_status=on_status,
        template_retries=template_retries,
        template_retry_delay=template_retry_delay,
        menu_wait=menu_wait,
    )
    _click_report_normal(
        image,
        template_click,
        None,
        on_status,
        template_retries,
        template_retry_delay,
    )
    image.wait(menu_wait)


def _expand_ledger_report_tree(
    image: ImageService,
    template_click: TemplateClickService,
    *,
    on_status: Callable[[str], None] | None,
    template_retries: int,
    template_retry_delay: float,
    menu_wait: float,
) -> None:
    _status(on_status, f"คลิกเมนู {MENU_ACCOUNT_REPORT_LABEL}")
    try:
        _retry_action(
            lambda: template_click.click("menu_account_report"),
            image=image,
            retries=template_retries,
            retry_delay=template_retry_delay,
        )
    except TemplateNotFoundError:
        _status(on_status, "จับภาพไม่เจอ — กด 5")
        image.press("5")
    image.wait(menu_wait)

    _status(on_status, f"คลิกเมนู {MENU_GENERAL_LEDGER_LABEL}")
    try:
        _retry_action(
            lambda: template_click.click("menu_general_ledger"),
            image=image,
            retries=template_retries,
            retry_delay=template_retry_delay,
        )
    except TemplateNotFoundError:
        _status(on_status, "จับภาพไม่เจอ — กด 4")
        image.press("4")
    image.wait(menu_wait)


def _click_report_normal(
    image: ImageService,
    template_click: TemplateClickService,
    search_region: tuple[int, int, int, int] | None,
    on_status: Callable[[str], None] | None,
    template_retries: int,
    template_retry_delay: float,
    fallback_key: bool = True,
    action_id: str = "menu_report_normal",
) -> None:
    _status(on_status, f"คลิกเมนู {MENU_REPORT_NORMAL_LABEL}")
    try:
        _retry_action(
            lambda: template_click.click(action_id, search_region=search_region),
            image=image,
            retries=template_retries,
            retry_delay=template_retry_delay,
        )
        return
    except TemplateNotFoundError:
        if search_region is not None:
            try:
                _retry_action(
                    lambda: template_click.click(action_id),
                    image=image,
                    retries=template_retries,
                    retry_delay=template_retry_delay,
                )
                return
            except TemplateNotFoundError:
                pass
        if not fallback_key:
            raise
        _status(on_status, "จับภาพไม่เจอ — กด 1")
        image.press("1")


def report_reopen_retries(template_retries: int) -> int:
    return max(1, min(2, template_retries))


def _type_report_field(image: ImageService, text: str) -> None:
    image.type_keys(text, clear_first=False)
    image.press("enter")


def _retry_action(action, *, image: ImageService, retries: int, retry_delay: float):
    attempts = max(1, retries)
    last_error: TemplateNotFoundError | None = None
    for attempt in range(attempts):
        try:
            return action()
        except TemplateNotFoundError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                image.wait(retry_delay)
                continue
            raise
    if last_error:
        raise last_error
    raise TemplateNotFoundError("ไม่พบเมนู")


def _status(on_status: Callable[[str], None] | None, message: str) -> None:
    if on_status:
        on_status(message)

"""เปิดเมนู Express ด้วยจับภาพคลิก — ไม่มีคีย์ลัด 5-1-2"""

from __future__ import annotations

from typing import Callable

from constants.routes import (
    MENU_ACCOUNT_LABEL,
    MENU_DAILY_ENTRY_LABEL,
    MENU_PAYMENT_JOURNAL_LABEL,
    MENU_PAYMENT_JOURNAL_PATH,
)
from services.image_service import ImageService
from services.template_click_service import TemplateClickService, TemplateNotFoundError

MENU_PAYMENT_JOURNAL_STEPS: tuple[tuple[str, str], ...] = (
    ("menu_account", MENU_ACCOUNT_LABEL),
    ("menu_daily_entry", MENU_DAILY_ENTRY_LABEL),
    ("menu_payment_journal", MENU_PAYMENT_JOURNAL_LABEL),
)


def open_payment_journal_menu(
    image: ImageService,
    template_click: TemplateClickService,
    *,
    on_status: Callable[[str], None] | None = None,
    template_retries: int = 4,
    template_retry_delay: float = 0.15,
    menu_wait: float = 0.25,
) -> None:
    if not template_click.enabled:
        raise RuntimeError("ต้องเปิด template_click และจับภาพเมนู 5-1-2")

    _status(on_status, f"เปิดเมนู {MENU_PAYMENT_JOURNAL_PATH} (คลิกจับภาพ)")
    for action_id, label in MENU_PAYMENT_JOURNAL_STEPS:
        _status(on_status, f"คลิกเมนู {label}")
        _click_menu_action(
            template_click,
            action_id,
            retries=template_retries,
            retry_delay=template_retry_delay,
            image=image,
        )
        image.wait(menu_wait)


def _click_menu_action(
    template_click: TemplateClickService,
    action_id: str,
    *,
    retries: int,
    retry_delay: float,
    image: ImageService,
) -> None:
    attempts = max(1, retries)
    for attempt in range(attempts):
        try:
            template_click.click(action_id)
            return
        except TemplateNotFoundError:
            if attempt + 1 < attempts:
                image.wait(retry_delay)
                continue
            raise


def _status(on_status: Callable[[str], None] | None, message: str) -> None:
    if on_status:
        on_status(message)

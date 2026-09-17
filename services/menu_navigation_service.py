"""เปิดเมนู Express ด้วยจับภาพคลิก — ไม่มีคีย์ลัด 5-1-2"""

from __future__ import annotations

from typing import Callable

from constants.routes import (
    MENU_ACCOUNT_LABEL,
    MENU_DAILY_ENTRY_LABEL,
    MENU_FLYOUT_WAIT,
    MENU_GENERAL_JOURNAL_LABEL,
    MENU_GENERAL_JOURNAL_PATH,
    MENU_PAYMENT_JOURNAL_LABEL,
    MENU_PAYMENT_JOURNAL_PATH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from models.step_match_result import StepMatchResult
from services.image_service import ImageService
from services.template_click_service import TemplateClickService, TemplateNotFoundError


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

    _status(on_status, f"คลิกเมนู {MENU_ACCOUNT_LABEL}")
    _retry_action(
        lambda: template_click.click("menu_account"),
        image=image,
        retries=template_retries,
        retry_delay=template_retry_delay,
    )
    image.wait(menu_wait)

    _status(on_status, f"ชี้เมนู {MENU_DAILY_ENTRY_LABEL} (เปิด submenu)")
    daily_match = _retry_action(
        lambda: template_click.hover("menu_daily_entry"),
        image=image,
        retries=template_retries,
        retry_delay=template_retry_delay,
    )
    image.wait(MENU_FLYOUT_WAIT)

    flyout_region = _flyout_search_region(daily_match)
    _status(on_status, f"คลิกเมนู {MENU_PAYMENT_JOURNAL_LABEL}")
    try:
        template_click.click("menu_payment_journal", search_region=flyout_region)
    except TemplateNotFoundError:
        _status(on_status, "จับภาพไม่เจอ — คลิกรายการที่ 2 ของ submenu")
        _click_flyout_item(image, daily_match, 1)
    image.wait(menu_wait)


def open_general_journal_menu(
    image: ImageService,
    template_click: TemplateClickService,
    *,
    on_status: Callable[[str], None] | None = None,
    template_retries: int = 4,
    template_retry_delay: float = 0.15,
    menu_wait: float = 0.25,
) -> None:
    if not template_click.enabled:
        raise RuntimeError("ต้องเปิด template_click และจับภาพเมนู 5-1-1")

    _status(on_status, f"เปิดเมนู {MENU_GENERAL_JOURNAL_PATH} (คลิกจับภาพ)")

    _status(on_status, f"คลิกเมนู {MENU_ACCOUNT_LABEL}")
    _retry_action(
        lambda: template_click.click("menu_account"),
        image=image,
        retries=template_retries,
        retry_delay=template_retry_delay,
    )
    image.wait(menu_wait)

    _status(on_status, f"ชี้เมนู {MENU_DAILY_ENTRY_LABEL} (เปิด submenu)")
    daily_match = _retry_action(
        lambda: template_click.hover("menu_daily_entry"),
        image=image,
        retries=template_retries,
        retry_delay=template_retry_delay,
    )
    image.wait(MENU_FLYOUT_WAIT)

    flyout_region = _flyout_search_region(daily_match)
    _status(on_status, f"คลิกเมนู {MENU_GENERAL_JOURNAL_LABEL}")
    try:
        template_click.click("menu_general_journal", search_region=flyout_region)
    except TemplateNotFoundError:
        _status(on_status, "จับภาพไม่เจอ — คลิกรายการแรกของ submenu")
        _click_flyout_item(image, daily_match, 0)
    image.wait(menu_wait)


def _flyout_search_region(daily_match: StepMatchResult) -> tuple[int, int, int, int]:
    """submenu เปิดทางขวาของ 1.ลงประจำวัน"""
    x0 = max(0, daily_match.x + daily_match.width - 10)
    y0 = max(0, daily_match.y - 20)
    x1 = min(SCREEN_WIDTH, daily_match.x + 460)
    y1 = min(SCREEN_HEIGHT, daily_match.y + 160)
    return x0, y0, x1, y1


def _click_flyout_item(image: ImageService, daily_match: StepMatchResult, index: int) -> None:
    x = min(SCREEN_WIDTH - 8, daily_match.x + daily_match.width + 48)
    row = max(8, daily_match.height)
    y = daily_match.y + max(8, row // 2) + (index * row)
    image.click_at(x, y)


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

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from models.pnd30_form_config import Pnd30FormConfig
from models.pnd30_matched_job import Pnd30MatchedJob
from services.image_service import ImageService
from services.template_click_service import TemplateClickService


@dataclass(frozen=True)
class Pnd30FillContext:
    image: ImageService
    template_click: TemplateClickService
    form_config: Pnd30FormConfig
    job: Pnd30MatchedJob
    on_status: Callable[[str], None]
    should_stop: Callable[[], bool]
    template_retries: int
    template_retry_delay: float

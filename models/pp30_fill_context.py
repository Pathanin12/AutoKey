from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from models.pp30_form_config import Pp30FormConfig
from models.pp30_matched_job import Pp30MatchedJob
from services.image_service import ImageService
from services.template_click_service import TemplateClickService


@dataclass(frozen=True)
class Pp30FillContext:
    image: ImageService
    template_click: TemplateClickService
    form_config: Pp30FormConfig
    job: Pp30MatchedJob
    on_status: Callable[[str], None]
    should_stop: Callable[[], bool]
    template_retries: int
    template_retry_delay: float

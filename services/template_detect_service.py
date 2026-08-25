"""จับภาพ template บนหน้าจอ Express — ใช้โดย TemplateClickService"""

from __future__ import annotations

from PIL import Image

from models.step_match_result import StepMatchResult
from models.template_target import TemplateTarget
from services.template_match_service import load_step_template, scan_best_match


def detect_step_match(
    background: Image.Image,
    step: TemplateTarget,
    *,
    search_region: tuple[int, int, int, int] | None = None,
) -> StepMatchResult:
    if not step.template_path.exists():
        return StepMatchResult(False, 0.0, 0, 0, 0, 0)

    template = load_step_template(step)
    template_width, template_height = template.size

    if search_region is None:
        result = scan_best_match(background, template)
    else:
        x0, y0, x1, y1 = search_region
        result = scan_best_match(
            background,
            template,
            x0=x0,
            y0=y0,
            x1=max(x0, x1 - template_width),
            y1=max(y0, y1 - template_height),
        )

    passed = result.score >= step.match_threshold
    return StepMatchResult(
        found=passed,
        score=result.score,
        x=result.x,
        y=result.y,
        width=template_width,
        height=template_height,
    )

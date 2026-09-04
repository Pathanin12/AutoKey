from __future__ import annotations

from constants.routes import UI_TEXT
from models.pp30_matched_job import Pp30MatchedJob, Pp30PdfRecord
from services.lookup_match_service import (
    core_company_name,
    name_similarity,
    names_match,
    normalize_name,
    tidy_vendor_name,
)
from services.pp30_pdf_service import company_hint_from_filename


class Pp30MatchService:
    @staticmethod
    def match_jobs(records: list[Pp30PdfRecord], excel_names: list[str]) -> list[Pp30MatchedJob]:
        jobs: list[Pp30MatchedJob] = []
        errors: list[str] = []
        for record in records:
            if not record.company_name:
                errors.append(UI_TEXT["pp30_pdf_name_missing"].format(path=record.pdf_path.name))
                continue
            excel_name = Pp30MatchService.match_name(record.company_name, excel_names)
            if excel_name is None:
                excel_name = Pp30MatchService.match_name(
                    company_hint_from_filename(record.pdf_path),
                    excel_names,
                )
            if excel_name is None:
                errors.append(
                    UI_TEXT["pp30_unmatched"].format(
                        pdf_name=record.company_name,
                        path=record.pdf_path.name,
                    )
                )
                continue
            jobs.append(
                Pp30MatchedJob(
                    pdf_path=record.pdf_path,
                    pdf_name=record.company_name,
                    excel_name=excel_name,
                )
            )
        if errors:
            raise ValueError("\n".join(errors))
        return jobs

    @staticmethod
    def match_name(pdf_name: str, excel_names: list[str]) -> str | None:
        pdf_tidy = tidy_vendor_name(pdf_name)
        pdf_norm = normalize_name(pdf_name)
        pdf_core = normalize_name(core_company_name(pdf_name))
        if not pdf_tidy:
            return None

        for excel_name in excel_names:
            if tidy_vendor_name(excel_name) == pdf_tidy:
                return excel_name
            if normalize_name(excel_name) == pdf_norm:
                return excel_name
            excel_core = normalize_name(core_company_name(excel_name))
            if pdf_core and excel_core and excel_core == pdf_core:
                return excel_name

        best_name: str | None = None
        best_score = 0.0
        pdf_core_name = core_company_name(pdf_name)
        for excel_name in excel_names:
            excel_core_name = core_company_name(excel_name)
            if not names_match(pdf_core_name, excel_core_name) and not names_match(
                excel_core_name, pdf_core_name
            ):
                if not names_match(pdf_name, excel_name) and not names_match(excel_name, pdf_name):
                    continue
            score = max(
                name_similarity(pdf_core_name, excel_core_name),
                name_similarity(pdf_name, excel_name),
            )
            if score > best_score:
                best_score = score
                best_name = excel_name
        return best_name

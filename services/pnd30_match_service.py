from __future__ import annotations

from constants.routes import UI_TEXT
from models.pnd30_matched_job import Pnd30MatchedJob, Pnd30PdfRecord
from services.lookup_match_service import tidy_vendor_name
from services.pp30_match_service import Pp30MatchService


class Pnd30MatchService:
    @staticmethod
    def match_jobs(records: list[Pnd30PdfRecord], excel_names: list[str]) -> list[Pnd30MatchedJob]:
        jobs: list[Pnd30MatchedJob] = []
        errors: list[str] = []
        for record in records:
            if not record.company_name:
                errors.append(UI_TEXT["pp30_pdf_name_missing"].format(path=record.pdf_path.name))
                continue
            if record.form_values is None:
                errors.append(UI_TEXT["pnd30_pdf_values_missing"].format(path=record.pdf_path.name))
                continue
            excel_name = Pp30MatchService.match_name(record.company_name, excel_names)
            if excel_name is None:
                excel_name = Pp30MatchService.match_name(
                    tidy_vendor_name(record.pdf_path.stem),
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
                Pnd30MatchedJob(
                    pdf_path=record.pdf_path,
                    pdf_name=record.company_name,
                    excel_name=excel_name,
                    form_values=record.form_values,
                )
            )
        if errors:
            raise ValueError("\n".join(errors))
        return jobs

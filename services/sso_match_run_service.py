from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Callable

from constants.routes import UI_TEXT
from models.sso_form_config import SsoFormConfig
from models.sso_matched_job import SsoMatchedJob
from services.express_journal_date_service import ExpressJournalDateService
from services.express_shop_index_service import ExpressShopIndexService
from services.name_match_service import tidy_name
from services.pp30_match_service import Pp30MatchService
from services.sso_insert_service import SsoInsertService
from services.sso_pdf_service import SsoPdfService


class SsoMatchRunService:
    @staticmethod
    def dup_star(total: int, index: int) -> int | None:
        if total <= 1:
            return None
        return index

    @staticmethod
    def receipt_key(folder: Path, receipt_no: str) -> str:
        number = (receipt_no or "").strip().upper()
        if not number:
            return ""
        return f"{folder}|{number}"

    @staticmethod
    def run(
        form_config: SsoFormConfig,
        express_data_dir: Path,
        *,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        should_stop: Callable[[], bool] | None = None,
    ) -> list[SsoMatchedJob]:
        companies = ExpressShopIndexService().load(express_data_dir)
        on_status(UI_TEXT["pp30_shops_total"].format(count=len(companies)))
        if not companies:
            raise ValueError(UI_TEXT["pp30_shops_none"])
        lookup = Pp30MatchService.lookup(companies)
        total = len(form_config.pdf_files)
        jobs: list[SsoMatchedJob] = []
        pending: list[SsoMatchedJob] = []
        seen_receipts: set[str] = set()
        for index, pdf_path in enumerate(form_config.pdf_files, start=1):
            if should_stop and should_stop():
                break
            on_progress(index - 1, total)
            try:
                record = SsoPdfService.load_record(pdf_path)
            except Exception as exc:
                on_status(f"{pdf_path.name}: {exc}")
                on_progress(index, total)
                continue
            if not record.company_name:
                on_status(UI_TEXT["pp30_pdf_name_missing"].format(path=pdf_path.name))
                on_progress(index, total)
                continue
            company = Pp30MatchService.match_lookup(record.company_name, lookup)
            if company is None:
                on_status(
                    UI_TEXT["pp30_unmatched"].format(
                        pdf_name=record.company_name,
                        path=pdf_path.name,
                    )
                )
                on_progress(index, total)
                continue
            on_status(
                UI_TEXT["pp30_match_log"].format(
                    pdf_name=record.company_name,
                    shop_name=tidy_name(company.shop_name),
                )
            )
            job = SsoMatchedJob(
                pdf_path=record.pdf_path,
                pdf_name=record.company_name,
                company=company,
                form_values=record.form_values,
            )
            jobs.append(job)
            if record.form_values is None:
                on_status(UI_TEXT["pp30_values_missing"].format(path=pdf_path.name))
                on_progress(index, total)
                continue
            if not record.form_values.has_contrib and not record.form_values.has_surcharge:
                on_status(UI_TEXT["sso_skip_zero_log"].format(name=record.company_name))
                on_progress(index, total)
                continue
            receipt_key = SsoMatchRunService.receipt_key(company.folder, record.form_values.receipt_no)
            if receipt_key:
                if receipt_key in seen_receipts:
                    on_status(
                        UI_TEXT["sso_skip_receipt_log"].format(
                            name=record.company_name,
                            number=record.form_values.receipt_no,
                        )
                    )
                    on_progress(index, total)
                    continue
                seen_receipts.add(receipt_key)
            pending.append(job)
            on_progress(index, total)
        counts = Counter(str(job.company.folder) for job in pending)
        stars: dict[str, int] = {}
        inserted = 0
        for job in pending:
            if should_stop and should_stop():
                break
            values = job.form_values
            if values is None:
                continue
            key = str(job.company.folder)
            stars[key] = stars.get(key, 0) + 1
            dup_n = SsoMatchRunService.dup_star(counts[key], stars[key])
            try:
                voucher = SsoInsertService.voucher(values, form_config, dup_n=dup_n)
                existing_date = ExpressJournalDateService.first_existing_voucher_date(
                    job.company.folder, [voucher]
                )
                if existing_date:
                    on_status(
                        UI_TEXT["pp30_skip_date_exists_log"].format(
                            name=job.pdf_name,
                            date=existing_date,
                        )
                    )
                    continue
                name = SsoInsertService.insert(
                    job.company.folder, values, form_config, dup_n=dup_n
                )
                if name:
                    inserted += 1
                    on_status(
                        UI_TEXT["sso_insert_log"].format(
                            shop=tidy_name(job.company.shop_name),
                            detail=name,
                        )
                    )
            except Exception as exc:
                on_status(f"{job.pdf_name}: {exc}")
        on_status(UI_TEXT["pp30_insert_done"].format(inserted=inserted, total=total))
        return jobs

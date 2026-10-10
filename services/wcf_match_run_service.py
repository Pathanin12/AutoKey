from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Callable

from constants.routes import UI_TEXT
from models.wcf_form_config import WcfFormConfig
from models.wcf_matched_job import WcfMatchedJob
from services.express_journal_date_service import ExpressJournalDateService
from services.express_shop_index_service import ExpressShopIndexService
from services.name_match_service import tidy_name
from services.pp30_match_service import Pp30MatchService
from services.wcf_excel_service import WcfExcelService
from services.wcf_insert_service import WcfInsertService


class WcfMatchRunService:
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
        form_config: WcfFormConfig,
        express_data_dir: Path,
        *,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        should_stop: Callable[[], bool] | None = None,
    ) -> list[WcfMatchedJob]:
        rows = WcfExcelService.load_rows(form_config.excel_path)
        on_status(UI_TEXT["wcf_excel_total"].format(count=len(rows)))
        if not rows:
            raise ValueError(UI_TEXT["wcf_excel_none"])
        companies = ExpressShopIndexService().load(express_data_dir)
        on_status(UI_TEXT["pp30_shops_total"].format(count=len(companies)))
        if not companies:
            raise ValueError(UI_TEXT["pp30_shops_none"])
        lookup = Pp30MatchService.lookup(companies)
        total = len(rows)
        jobs: list[WcfMatchedJob] = []
        pending: list[WcfMatchedJob] = []
        seen_receipts: set[str] = set()
        for index, row in enumerate(rows, start=1):
            if should_stop and should_stop():
                break
            on_progress(index - 1, total)
            company = Pp30MatchService.match_lookup(row.match_name, lookup) or Pp30MatchService.match_lookup(
                row.shop_name, lookup
            )
            if company is None:
                on_status(UI_TEXT["wcf_unmatched"].format(name=row.shop_name))
                on_progress(index, total)
                continue
            on_status(
                UI_TEXT["wcf_match_log"].format(
                    excel_name=row.shop_name,
                    shop_name=tidy_name(company.shop_name),
                    folder=company.folder.name,
                )
            )
            job = WcfMatchedJob(row=row, company=company)
            jobs.append(job)
            if not row.pv_date:
                on_status(UI_TEXT["wcf_skip_date_log"].format(name=row.shop_name))
                on_progress(index, total)
                continue
            if not row.has_contrib and not row.has_surcharge:
                on_status(UI_TEXT["wcf_skip_zero_log"].format(name=row.shop_name))
                on_progress(index, total)
                continue
            receipt_key = WcfMatchRunService.receipt_key(company.folder, row.receipt_no)
            if receipt_key:
                if receipt_key in seen_receipts:
                    on_status(
                        UI_TEXT["wcf_skip_receipt_log"].format(
                            name=row.shop_name,
                            number=row.receipt_no,
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
            key = str(job.company.folder)
            stars[key] = stars.get(key, 0) + 1
            dup_n = WcfMatchRunService.dup_star(counts[key], stars[key])
            try:
                voucher = WcfInsertService.voucher(job.row, form_config, dup_n=dup_n)
                _ready, skipped = ExpressJournalDateService.pending(job.company.folder, [voucher])
                for existing_date, detail in skipped:
                    on_status(
                        UI_TEXT["pp30_skip_date_exists_log"].format(
                            name=job.row.shop_name,
                            date=existing_date,
                            detail=detail,
                        )
                    )
                if not _ready:
                    continue
                name = WcfInsertService.insert(
                    job.company.folder, job.row, form_config, dup_n=dup_n
                )
                if name:
                    inserted += 1
                    on_status(
                        UI_TEXT["wcf_insert_log"].format(
                            shop=tidy_name(job.company.shop_name),
                            detail=name,
                        )
                    )
            except Exception as exc:
                on_status(f"{job.row.shop_name}: {exc}")
        on_status(UI_TEXT["ka_tam_insert_done"].format(inserted=inserted, total=total))
        return jobs

from __future__ import annotations

from pathlib import Path
from typing import Callable

from constants.date_utils import express_month_year_label
from constants.routes import UI_TEXT
from models.income_form_config import IncomeFormConfig
from models.income_matched_job import IncomeMatchedJob
from models.income_pdf_name import IncomePdfName
from services.express_journal_date_service import ExpressJournalDateService
from services.express_shop_index_service import ExpressShopIndexService
from services.income_insert_service import IncomeInsertService
from services.income_pdf_service import IncomePdfService
from services.name_match_service import tidy_name
from services.pp30_folder_service import Pp30FolderService
from services.pp30_match_service import Pp30MatchService

# from services.income_excel_service import IncomeExcelService
# from services.income_statement_download_service import IncomeStatementDownloadService


class IncomeMatchRunService:
    @staticmethod
    def run(
        form_config: IncomeFormConfig,
        express_data_dir: Path,
        *,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        should_stop: Callable[[], bool] | None = None,
    ) -> list[IncomeMatchedJob]:
        companies = ExpressShopIndexService().load(express_data_dir)
        on_status(UI_TEXT["pp30_shops_total"].format(count=len(companies)))
        if not companies:
            raise ValueError(UI_TEXT["pp30_shops_none"])
        # accounts = IncomeExcelService.load_accounts(form_config.excel_path)
        # on_status(UI_TEXT["income_excel_total"].format(count=len(accounts)))
        # if not accounts:
        #     raise ValueError(UI_TEXT["income_excel_none"])
        # form_config.pdf_files = IncomeStatementDownloadService.download(
        #     accounts,
        #     form_config,
        #     on_status=on_status,
        # )
        form_config.pdf_files = form_config.pdf_files or Pp30FolderService.list_pdfs(form_config.pdf_folder)
        if not form_config.pdf_files:
            raise ValueError(UI_TEXT["income_pdf_none"])
        is_locked = form_config.lock.is_locked
        lookup = Pp30MatchService.lookup(companies)
        total = len(form_config.pdf_files)
        jobs: list[IncomeMatchedJob] = []
        inserted = 0
        for index, pdf_path in enumerate(form_config.pdf_files, start=1):
            if should_stop and should_stop():
                break
            on_progress(index - 1, total)
            password = IncomePdfName.parse(pdf_path).password if is_locked else ""
            if is_locked and not password:
                on_status(UI_TEXT["income_skip_no_password_log"].format(path=pdf_path.name))
                on_progress(index, total)
                continue
            try:
                record = IncomePdfService.load_record(pdf_path, password)
            except Exception as exc:
                on_status(f"{pdf_path.name}: {exc}")
                on_progress(index, total)
                continue
            if record.locked:
                skip_key = "income_skip_wrong_password_log" if is_locked else "income_skip_locked_log"
                on_status(UI_TEXT[skip_key].format(path=pdf_path.name))
                on_progress(index, total)
                continue
            if not record.has_text:
                on_status(UI_TEXT["income_skip_image_log"].format(path=pdf_path.name))
                on_progress(index, total)
                continue
            if not record.invoices:
                on_status(UI_TEXT["income_skip_no_invoice_log"].format(path=pdf_path.name))
                on_progress(index, total)
                continue
            month_invoices = [values for values in record.invoices if form_config.matches_month(values)]
            if not month_invoices:
                month, year = express_month_year_label(form_config.start_date)
                on_status(UI_TEXT["income_skip_no_month_log"].format(path=pdf_path.name, month=month, year=year))
                on_progress(index, total)
                continue
            unmatched: set[str] = set()
            for values in month_invoices:
                company = Pp30MatchService.match_lookup(values.company_name, lookup)
                if company is None:
                    if values.company_name not in unmatched:
                        unmatched.add(values.company_name)
                        on_status(
                            UI_TEXT["pp30_unmatched"].format(
                                pdf_name=values.company_name,
                                path=pdf_path.name,
                            )
                        )
                    continue
                jobs.append(
                    IncomeMatchedJob(
                        pdf_path=record.pdf_path,
                        pdf_name=values.company_name,
                        company=company,
                        form_values=values,
                    )
                )
                if not values.has_total:
                    on_status(UI_TEXT["income_skip_zero_log"].format(name=values.company_name))
                    continue
                try:
                    voucher = IncomeInsertService.voucher(values, form_config)
                    existing_date = ExpressJournalDateService.first_existing_voucher_date(
                        company.folder, [voucher]
                    )
                    if existing_date:
                        on_status(
                            UI_TEXT["pp30_skip_date_exists_log"].format(
                                name=values.company_name,
                                date=existing_date,
                            )
                        )
                        continue
                    name = IncomeInsertService.insert(company.folder, values, form_config)
                    if name:
                        inserted += 1
                        on_status(
                            UI_TEXT["income_insert_log"].format(
                                shop=tidy_name(company.shop_name),
                                detail=name,
                            )
                        )
                except Exception as exc:
                    on_status(f"{values.company_name}: {exc}")
            on_progress(index, total)
        on_status(UI_TEXT["income_insert_done"].format(inserted=inserted, total=total))
        seen: set[tuple[str, str]] = set()
        for job in jobs:
            if job.form_values.bill_count <= 1:
                continue
            key = (job.pdf_name, job.form_values.branch_last5)
            if key in seen:
                continue
            seen.add(key)
            on_status(
                UI_TEXT["income_multi_bill_log"].format(
                    name=job.pdf_name,
                    branch=job.form_values.branch_last5,
                    count=job.form_values.bill_count,
                )
            )
        return jobs

from __future__ import annotations

from pathlib import Path

import pandas as pd

from models.ka_tam_row import KaTamRow
from models.run_config import ExcelSheetSummary
from services.tax_reference_service import build_nrg_tax_reference
from topics.ka_tam.sheet_configs import SheetColumnMap, get_sheet_column_map


def _to_float(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if not value:
            return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_text(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if text.lower() in {"xx", "nan", "no", "acct"}:
        return ""
    return text


def _credit_amount(row_values: tuple, column_map: SheetColumnMap) -> float:
    service = _to_float(row_values[column_map.service_amount])
    vat = _to_float(row_values[column_map.vat_amount])

    if column_map.credit_amount is not None:
        credit = _to_float(row_values[column_map.credit_amount])
        if credit > 0:
            return credit

    return round(service + vat, 2)


def _is_data_row(raw_values: tuple) -> bool:
    if not raw_values:
        return False
    first = raw_values[0]
    if first is None or (isinstance(first, float) and pd.isna(first)):
        return False
    try:
        int(float(first))
        return True
    except (TypeError, ValueError):
        return False


def _parse_sequence(raw_values: tuple) -> int | None:
    if not raw_values:
        return None
    first = raw_values[0]
    if first is None or (isinstance(first, float) and pd.isna(first)):
        return None
    try:
        return int(float(first))
    except (TypeError, ValueError):
        return None


def _parse_row(
    raw_values: tuple,
    column_map: SheetColumnMap,
    excel_row_number: int,
    sheet_name: str,
) -> KaTamRow | None:
    if not _is_data_row(raw_values):
        return None

    sequence = _parse_sequence(raw_values)
    if sequence is None:
        return None

    legal_name = _to_text(raw_values[column_map.legal_name])
    if not legal_name:
        return None

    invoice_number = ""
    if column_map.invoice_number is not None:
        invoice_number = _to_text(raw_values[column_map.invoice_number])

    nrg_tax_reference = (
        invoice_number
        if invoice_number.upper().startswith("NRG")
        else build_nrg_tax_reference(sheet_name, sequence)
    )

    return KaTamRow(
        row_number=excel_row_number,
        sequence=sequence,
        sheet_name=sheet_name,
        legal_name=legal_name,
        month=_to_text(raw_values[column_map.month]),
        tax_id=_to_text(raw_values[column_map.tax_id]),
        service_amount=_to_float(raw_values[column_map.service_amount]),
        vat_amount=_to_float(raw_values[column_map.vat_amount]),
        credit_amount=_credit_amount(raw_values, column_map),
        wt_amount=_to_float(raw_values[column_map.wt_amount]),
        invoice_number=invoice_number,
        nrg_tax_reference=nrg_tax_reference,
    )


class ExcelService:
    @staticmethod
    def load_ka_tam_rows(excel_path: Path, sheet_name: str) -> list[KaTamRow]:
        column_map = get_sheet_column_map(sheet_name)
        dataframe = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
        rows: list[KaTamRow] = []

        for index in range(column_map.data_start_row, len(dataframe)):
            raw_values = tuple(dataframe.iloc[index].tolist())
            parsed = _parse_row(raw_values, column_map, index + 1, sheet_name)
            if parsed is not None:
                rows.append(parsed)

        return rows

    @staticmethod
    def list_supported_sheets(excel_path: Path) -> list[str]:
        from topics.ka_tam.sheet_configs import SHEET_COLUMN_MAPS

        workbook = pd.ExcelFile(excel_path)
        return [sheet for sheet in workbook.sheet_names if sheet in SHEET_COLUMN_MAPS]

    @staticmethod
    def load_sheet_summaries(excel_path: Path) -> list[ExcelSheetSummary]:
        summaries: list[ExcelSheetSummary] = []
        for sheet_name in ExcelService.list_supported_sheets(excel_path):
            rows = ExcelService.load_ka_tam_rows(excel_path, sheet_name)
            if rows:
                summaries.append(ExcelSheetSummary(name=sheet_name, row_count=len(rows)))
        return summaries

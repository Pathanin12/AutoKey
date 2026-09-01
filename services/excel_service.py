from __future__ import annotations

from pathlib import Path

import pandas as pd

from models.ka_tam_row import KaTamRow
from models.run_config import ExcelSheetSummary
from services.tax_reference_service import build_nrg_tax_reference
from topics.ka_tam.sheet_configs import SheetColumnMap, detect_column_map


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


def _to_tax_id(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, bool):
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return "".join(ch for ch in f"{value:.0f}" if ch.isdigit())
    return _to_text(value)


def _cell_at(raw_values: tuple, index: int | None):
    if index is None or index < 0 or index >= len(raw_values):
        return None
    return raw_values[index]


def _credit_amount(row_values: tuple, column_map: SheetColumnMap) -> float:
    service = _to_float(_cell_at(row_values, column_map.service_amount))
    vat = _to_float(_cell_at(row_values, column_map.vat_amount))

    if column_map.credit_amount is not None:
        credit = _to_float(_cell_at(row_values, column_map.credit_amount))
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
    period_text: str,
) -> KaTamRow | None:
    if not _is_data_row(raw_values):
        return None

    sequence = _parse_sequence(raw_values)
    if sequence is None:
        return None

    legal_name = _to_text(_cell_at(raw_values, column_map.legal_name))
    if not legal_name:
        return None

    invoice_number = _to_text(_cell_at(raw_values, column_map.invoice_number))

    if invoice_number.upper().startswith("NRG"):
        nrg_tax_reference = invoice_number
    else:
        nrg_tax_reference = build_nrg_tax_reference(period_text, sequence)

    return KaTamRow(
        row_number=excel_row_number,
        sequence=sequence,
        sheet_name=sheet_name,
        legal_name=legal_name,
        month=_to_text(_cell_at(raw_values, column_map.month)),
        tax_id=_to_tax_id(_cell_at(raw_values, column_map.tax_id)),
        service_amount=_to_float(_cell_at(raw_values, column_map.service_amount)),
        vat_amount=_to_float(_cell_at(raw_values, column_map.vat_amount)),
        credit_amount=_credit_amount(raw_values, column_map),
        wt_amount=_to_float(_cell_at(raw_values, column_map.wt_amount)),
        invoice_number=invoice_number,
        nrg_tax_reference=nrg_tax_reference,
        legal_name_column=column_map.legal_name,
    )


class ExcelService:
    @staticmethod
    def load_workbook(excel_path: Path) -> tuple[list[ExcelSheetSummary], dict[str, list[KaTamRow]]]:
        workbook = pd.ExcelFile(excel_path)
        if not workbook.sheet_names:
            raise ValueError("ไฟล์ Excel ไม่มีชีต")
        sheet_name = workbook.sheet_names[0]
        dataframe = pd.read_excel(workbook, sheet_name=sheet_name, header=None)
        rows = ExcelService._rows_from_dataframe(
            dataframe,
            sheet_name,
            period_text=f"{sheet_name} {excel_path.stem}",
        )
        if not rows:
            raise ValueError("ไม่พบรายการในไฟล์ Excel")
        return [ExcelSheetSummary(name=sheet_name, row_count=len(rows))], {sheet_name: rows}

    @staticmethod
    def _rows_from_dataframe(
        dataframe: pd.DataFrame,
        sheet_name: str,
        *,
        period_text: str = "",
    ) -> list[KaTamRow]:
        preview = [tuple(dataframe.iloc[index].tolist()) for index in range(min(8, len(dataframe)))]
        column_map = detect_column_map(preview)
        rows: list[KaTamRow] = []
        source = period_text or sheet_name

        for index in range(column_map.data_start_row, len(dataframe)):
            raw_values = tuple(dataframe.iloc[index].tolist())
            parsed = _parse_row(raw_values, column_map, index + 1, sheet_name, source)
            if parsed is not None:
                rows.append(parsed)

        return rows

    @staticmethod
    def load_ka_tam_rows(excel_path: Path, sheet_name: str) -> list[KaTamRow]:
        dataframe = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
        return ExcelService._rows_from_dataframe(
            dataframe,
            sheet_name,
            period_text=f"{sheet_name} {excel_path.stem}",
        )

    @staticmethod
    def list_supported_sheets(excel_path: Path) -> list[str]:
        workbook = pd.ExcelFile(excel_path)
        if not workbook.sheet_names:
            return []
        return [workbook.sheet_names[0]]

    @staticmethod
    def load_sheet_summaries(excel_path: Path) -> list[ExcelSheetSummary]:
        summaries, _ = ExcelService.load_workbook(excel_path)
        return summaries

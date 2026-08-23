from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.excel_service import ExcelService
from services.tax_reference_service import resolve_tax_payer_id


def main() -> None:
    excel_path = Path("/Users/pathanin/Downloads/ค่าทำ.xlsx")
    if not excel_path.exists():
        excel_path = Path.home() / "Downloads" / "ค่าทำ.xlsx"

    sheets = ExcelService.list_supported_sheets(excel_path)
    print("Supported sheets:", sheets)

    for sheet in sheets:
        rows = ExcelService.load_ka_tam_rows(excel_path, sheet)
        print(f"\n{sheet}: {len(rows)} rows")
        if rows:
            sample = rows[0]
            print(
                f"ลำดับ {sample.sequence}",
                sample.legal_name,
                sample.service_amount,
                sample.vat_amount,
                sample.credit_amount,
                sample.wt_amount,
                f"เลขที่ {sample.tax_invoice_number}",
                f"เลขผู้เสียภาษี {resolve_tax_payer_id(sample.tax_id)}",
            )


if __name__ == "__main__":
    main()

from dataclasses import dataclass


@dataclass
class KaTamRow:
    row_number: int
    sequence: int
    sheet_name: str
    legal_name: str
    month: str
    tax_id: str
    service_amount: float
    vat_amount: float
    credit_amount: float
    wt_amount: float
    invoice_number: str = ""
    nrg_tax_reference: str = ""

    @property
    def has_vat(self) -> bool:
        return self.vat_amount > 0

    @property
    def has_wt(self) -> bool:
        return self.wt_amount > 0

    @property
    def tax_invoice_number(self) -> str:
        return self.invoice_number.strip() or self.nrg_tax_reference

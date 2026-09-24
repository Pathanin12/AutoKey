from __future__ import annotations

from pathlib import Path

from constants.routes import ISVAT_FILE_NAMES
from models.express_vat_record import ExpressVatRecord
from services.cdx_index_service import CdxIndexService
from services.dbf_table_service import DbfTableService
from services.name_match_service import tidy_name


class ExpressVatService:
    @staticmethod
    def insert(folder: Path, record: ExpressVatRecord) -> None:
        path = _first_file(folder, ISVAT_FILE_NAMES)
        values = {
            "VATREC": record.vatrec,
            "VATPRD": record.vatprd,
            "VATDAT": record.vatdat,
            "DOCDAT": record.docdat,
            "DOCNUM": record.docnum,
            "REFNUM": record.refnum,
            "DESCRP": tidy_name(record.descrp).replace(" ", "\xa0"),
            "AMT01": record.amt01,
            "VAT01": record.vat01,
            "TAXID": record.taxid,
            "DOCSTAT": record.docstat,
            "RECTYP": "",
        }
        recno = DbfTableService.append(path, values)
        cdx = _cdx_path(path)
        if cdx:
            CdxIndexService.insert_key(cdx, {key: str(item) for key, item in values.items()}, recno)


def _first_file(folder: Path, names: tuple[str, ...]) -> Path:
    for name in names:
        path = folder / name
        if path.exists():
            return path
    raise FileNotFoundError(names[0])


def _cdx_path(dbf_path: Path) -> Path | None:
    for suffix in (".CDX", ".cdx"):
        path = dbf_path.with_name(dbf_path.stem + suffix)
        if path.exists():
            return path
    return None

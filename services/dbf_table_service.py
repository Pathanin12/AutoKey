from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from struct import pack, unpack

from constants.routes import DBF_ENCODING


@dataclass(frozen=True)
class DbfField:
    name: str
    type: str
    length: int
    decimal: int


@dataclass
class DbfTable:
    path: Path
    header: bytearray
    fields: list[DbfField]
    nrecords: int
    header_len: int
    rec_len: int
    records_blob: bytearray
    eof: bytes


class DbfTableService:
    @staticmethod
    def load(path: Path) -> DbfTable:
        data = bytearray(path.read_bytes())
        nrecords = unpack("<I", data[4:8])[0]
        header_len = unpack("<H", data[8:10])[0]
        rec_len = unpack("<H", data[10:12])[0]
        fields: list[DbfField] = []
        offset = 32
        while offset + 32 <= header_len and data[offset] != 0x0D:
            name = bytes(data[offset : offset + 11]).split(b"\x00", 1)[0].decode("ascii", "replace").strip()
            typ = chr(data[offset + 11])
            length = data[offset + 16]
            decimal = data[offset + 17]
            fields.append(DbfField(name=name, type=typ, length=length, decimal=decimal))
            offset += 32
        body_end = header_len + nrecords * rec_len
        eof = bytes(data[body_end:])
        return DbfTable(
            path=path,
            header=data[:header_len],
            fields=fields,
            nrecords=nrecords,
            header_len=header_len,
            rec_len=rec_len,
            records_blob=data[header_len:body_end],
            eof=eof,
        )

    @staticmethod
    def read_records(path: Path) -> list[dict[str, str]]:
        table = DbfTableService.load(path)
        rows: list[dict[str, str]] = []
        for recno in range(table.nrecords):
            rec = table.records_blob[recno * table.rec_len : (recno + 1) * table.rec_len]
            if not rec or rec[0:1] == b"*":
                continue
            rows.append(DbfTableService._unpack(table, rec))
        return rows

    @staticmethod
    def append(path: Path, values: dict[str, object]) -> int:
        table = DbfTableService.load(path)
        rec = DbfTableService._pack(table, values)
        table.records_blob.extend(rec)
        table.nrecords += 1
        table.header[4:8] = pack("<I", table.nrecords)
        path.write_bytes(bytes(table.header) + bytes(table.records_blob) + table.eof)
        return table.nrecords

    @staticmethod
    def _unpack(table: DbfTable, rec: bytes) -> dict[str, str]:
        values: dict[str, str] = {}
        cursor = 1
        for field in table.fields:
            raw = rec[cursor : cursor + field.length]
            cursor += field.length
            values[field.name] = raw.decode(DBF_ENCODING, "replace").replace("\x00", "").rstrip(" ")
        return values

    @staticmethod
    def _pack(table: DbfTable, values: dict[str, object]) -> bytes:
        rec = bytearray(b" " * table.rec_len)
        rec[0] = 0x20
        cursor = 1
        for field in table.fields:
            raw = _pack_field(field, values.get(field.name, ""))
            rec[cursor : cursor + field.length] = raw
            cursor += field.length
        return bytes(rec)


def _pack_field(field: DbfField, value: object) -> bytes:
    if field.type == "N":
        if value in ("", None):
            return b" " * field.length
        number = float(value)
        if field.decimal:
            text = f"{number:.{field.decimal}f}"
        else:
            text = str(int(number))
        return text.encode("ascii")[: field.length].rjust(field.length)
    if field.type == "D":
        text = str(value or "").replace("-", "")[:8]
        return text.encode("ascii").ljust(field.length, b" ")
    text = str(value or "")
    encoded = text.encode(DBF_ENCODING, "replace")[: field.length]
    return encoded.ljust(field.length, b" ")

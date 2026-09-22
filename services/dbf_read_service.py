from __future__ import annotations

from pathlib import Path
from struct import unpack

from constants.routes import DBF_ENCODING


class DbfReadService:
    @staticmethod
    def read_records(path: Path) -> list[dict[str, str]]:
        data = path.read_bytes()
        if len(data) < 32:
            return []
        nrecords = unpack("<I", data[4:8])[0]
        header_len = unpack("<H", data[8:10])[0]
        rec_len = unpack("<H", data[10:12])[0]
        if header_len < 33 or rec_len < 1:
            return []
        fields: list[tuple[str, int]] = []
        offset = 32
        while offset + 32 <= len(data) and data[offset] != 0x0D:
            name = data[offset : offset + 11].split(b"\x00", 1)[0].decode("ascii", "replace").strip()
            length = data[offset + 16]
            fields.append((name, length))
            offset += 32
        rows: list[dict[str, str]] = []
        pos = header_len
        for _ in range(nrecords):
            rec = data[pos : pos + rec_len]
            pos += rec_len
            if len(rec) < rec_len or rec[0:1] == b"*":
                continue
            values: dict[str, str] = {}
            cursor = 1
            for name, length in fields:
                raw = rec[cursor : cursor + length]
                cursor += length
                values[name] = raw.decode(DBF_ENCODING, "replace").replace("\x00", "").rstrip(" ")
            rows.append(values)
        return rows

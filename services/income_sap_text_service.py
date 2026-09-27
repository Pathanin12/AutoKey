from __future__ import annotations

import struct

from pypdf.generic import ArrayObject, ContentStream, NumberObject


class IncomeSapTextService:
    @staticmethod
    def read_page(page) -> str:
        fonts = page.get("/Resources", {}).get("/Font")
        if not fonts:
            return ""
        decoders = {str(name): _FontDecoder(obj.get_object()) for name, obj in fonts.items()}
        contents = page.get_contents()
        if contents is None:
            return ""
        stream = ContentStream(contents, page.pdf)
        current: _FontDecoder | None = None
        parts: list[str] = []
        last_y: float | None = None
        for operands, operator in stream.operations:
            op = operator.decode() if isinstance(operator, bytes) else str(operator)
            if op == "Tf" and operands:
                current = decoders.get(str(operands[0]))
            elif op == "Tm" and len(operands) >= 6:
                y = float(operands[5])
                if last_y is not None and abs(y - last_y) > 2:
                    parts.append("\n")
                last_y = y
            elif op == "Td" and len(operands) >= 2 and abs(float(operands[1])) > 2:
                parts.append("\n")
            elif op == "T*":
                parts.append("\n")
            elif op in ("Tj", "'", '"') and operands and current:
                if op == "'":
                    parts.append("\n")
                parts.append(current.decode(_operand_bytes(operands[-1])))
            elif op == "TJ" and operands and current:
                parts.append(_decode_tj(operands[0], current))
        return "".join(parts)


class _FontDecoder:
    def __init__(self, font) -> None:
        self.identity = str(font.get("/Encoding")) == "/Identity-H"
        self.cid_to_gid = _cid_to_gid(font) if self.identity else None
        data = _font_file(font)
        self.gid_to_uni = _invert_cmap(data) if data else {}

    def decode(self, raw: bytes) -> str:
        if not self.identity:
            return raw.decode("latin-1", "replace")
        chars: list[str] = []
        for index in range(0, len(raw) - 1, 2):
            cid = (raw[index] << 8) | raw[index + 1]
            gid = cid
            if self.cid_to_gid is not None:
                if cid >= len(self.cid_to_gid):
                    continue
                gid = self.cid_to_gid[cid]
            uni = self.gid_to_uni.get(gid)
            if uni:
                chars.append(chr(uni))
        return "".join(chars)


def _decode_tj(items, decoder: _FontDecoder) -> str:
    if not isinstance(items, ArrayObject):
        return decoder.decode(_operand_bytes(items))
    parts: list[str] = []
    for item in items:
        if isinstance(item, (int, float, NumberObject)):
            if float(item) < -120:
                parts.append(" ")
            continue
        parts.append(decoder.decode(_operand_bytes(item)))
    return "".join(parts)


def _operand_bytes(value) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    raw = getattr(value, "original_bytes", None)
    if raw:
        return bytes(raw)
    if isinstance(value, str):
        return value.encode("latin-1", "replace")
    return b""


def _font_file(font) -> bytes:
    descriptor = font.get("/FontDescriptor")
    if descriptor:
        descriptor = descriptor.get_object()
        for key in ("/FontFile2", "/FontFile", "/FontFile3"):
            if descriptor.get(key):
                return descriptor[key].get_object().get_data()
    descendants = font.get("/DescendantFonts")
    if descendants:
        return _font_file(descendants[0].get_object())
    return b""


def _cid_to_gid(font) -> list[int] | None:
    descendants = font.get("/DescendantFonts")
    if not descendants:
        return None
    raw = descendants[0].get_object().get("/CIDToGIDMap")
    if raw in (None, "/Identity"):
        return None
    data = raw.get_object().get_data()
    return [struct.unpack_from(">H", data, index)[0] for index in range(0, len(data) - 1, 2)]


def _u16(data: bytes, offset: int) -> int:
    return struct.unpack_from(">H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def _i16(data: bytes, offset: int) -> int:
    return struct.unpack_from(">h", data, offset)[0]


def _invert_cmap(data: bytes) -> dict[int, int]:
    if len(data) < 12:
        return {}
    tables: dict[str, tuple[int, int]] = {}
    for index in range(_u16(data, 4)):
        record = 12 + index * 16
        if record + 16 > len(data):
            break
        tag = data[record : record + 4].decode("latin-1", "replace")
        tables[tag] = (_u32(data, record + 8), _u32(data, record + 12))
    if "cmap" not in tables:
        return {}
    cmap_at, _ = tables["cmap"]
    mapping: dict[int, int] = {}
    for index in range(_u16(data, cmap_at + 2)):
        sub = cmap_at + _u32(data, cmap_at + 8 + index * 8)
        if sub + 2 > len(data):
            continue
        fmt = _u16(data, sub)
        if fmt == 4:
            _add_cmap_format4(data, sub, mapping)
        elif fmt == 12 and sub + 16 <= len(data):
            _add_cmap_format12(data, sub, mapping)
    return mapping


def _add_cmap_format4(data: bytes, base: int, mapping: dict[int, int]) -> None:
    seg_count = _u16(data, base + 6) // 2
    end_at = base + 14
    start_at = end_at + 2 * seg_count + 2
    delta_at = start_at + 2 * seg_count
    range_at = delta_at + 2 * seg_count
    for seg in range(seg_count):
        end = _u16(data, end_at + 2 * seg)
        start = _u16(data, start_at + 2 * seg)
        delta = _i16(data, delta_at + 2 * seg)
        range_offset = _u16(data, range_at + 2 * seg)
        for code in range(start, end + 1):
            if range_offset == 0:
                gid = (code + delta) & 0xFFFF
            else:
                pos = range_at + 2 * seg + range_offset + 2 * (code - start)
                if pos + 2 > len(data):
                    continue
                gid = _u16(data, pos)
                if gid:
                    gid = (gid + delta) & 0xFFFF
            if gid:
                mapping.setdefault(gid, code)


def _add_cmap_format12(data: bytes, base: int, mapping: dict[int, int]) -> None:
    groups = _u32(data, base + 12)
    pos = base + 16
    for _ in range(groups):
        if pos + 12 > len(data):
            break
        start, end, glyph = _u32(data, pos), _u32(data, pos + 4), _u32(data, pos + 8)
        pos += 12
        for offset, code in enumerate(range(start, end + 1)):
            mapping.setdefault(glyph + offset, code)

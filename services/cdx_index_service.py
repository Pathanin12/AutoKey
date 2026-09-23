from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from struct import pack, unpack

CDX_PAGE = 512
CDX_EXT_HEAD = 24
CDX_INT_HEAD = 12
CDX_NODE_LEAF = 0x02
CDX_HEADER = 1024


@dataclass
class CdxTag:
    offset: int
    root: int
    key_size: int
    key_expr: str
    for_expr: str
    trail: int = 0x20


class CdxIndexService:
    @staticmethod
    def insert_key(cdx_path: Path, record: dict[str, str], recno: int) -> None:
        data = bytearray(cdx_path.read_bytes())
        added = 0
        for tag in _tags(data):
            if not _for_matches(tag.for_expr, record):
                continue
            key = _key_value(tag.key_expr, record, tag.key_size)
            _insert_into_tag(data, tag, key, recno)
            added += 1
        if added:
            _bump_file_version(data)
        cdx_path.write_bytes(data)


def _bump_file_version(data: bytearray) -> None:
    version = unpack(">I", data[8:12])[0] + 1
    data[8:12] = pack(">I", version)


def _tags(data: bytes) -> list[CdxTag]:
    tags: list[CdxTag] = []
    offset = CDX_HEADER
    while offset + CDX_HEADER <= len(data):
        root = unpack("<I", data[offset : offset + 4])[0]
        key_size = unpack("<H", data[offset + 12 : offset + 14])[0]
        opt = data[offset + 14]
        pool = data[offset + 512 : offset + CDX_HEADER]
        if key_size == 0 or key_size > 240 or opt in (0x00, 0xFF):
            break
        if root == 0 or root >= len(data):
            break
        parts = pool.split(b"\x00")
        key_expr = parts[0].decode("ascii", "replace") if parts else ""
        for_expr = parts[1].decode("ascii", "replace") if len(parts) > 1 else ""
        if not key_expr or not key_expr[0].isalpha():
            break
        tags.append(CdxTag(offset=offset, root=root, key_size=key_size, key_expr=key_expr, for_expr=for_expr))
        offset += CDX_HEADER
    return tags


def _for_matches(for_expr: str, record: dict[str, str]) -> bool:
    expr = (for_expr or "").replace(" ", "").upper()
    if "TRNSTAT#'U'" in expr or 'TRNSTAT#"U"' in expr:
        return (record.get("TRNSTAT") or "") != "U"
    if "TRNSTAT='U'" in expr:
        return (record.get("TRNSTAT") or "") == "U"
    return True


def _key_value(expr: str, record: dict[str, str], key_size: int) -> bytes:
    parts = expr.split("+")
    chunks: list[bytes] = []
    for part in parts:
        token = part.strip()
        if token.startswith("DTOS(") and token.endswith(")"):
            field = token[5:-1]
            chunks.append((record.get(field) or "").encode("ascii", "replace")[:8].ljust(8, b" "))
            continue
        value = (record.get(token) or "")
        width = _field_width(token)
        encoded = value.encode("cp874", "replace")[:width].ljust(width, b" ")
        chunks.append(encoded)
    key = b"".join(chunks)
    return key[:key_size].ljust(key_size, b" ")


def _field_width(name: str) -> int:
    widths = {
        "VOUCHER": 12,
        "JNLTYP": 2,
        "SEQIT": 2,
        "TRNTYP": 1,
        "ACCNUM": 15,
        "DEPCOD": 4,
        "VOUDAT": 8,
        "CHGDAT": 8,
    }
    return widths.get(name, 12)


def _insert_into_tag(data: bytearray, tag: CdxTag, key: bytes, recno: int) -> None:
    page_off, ancestors = _find_leaf_path(data, tag, key, recno)
    _insert_leaf_key(data, tag, page_off, key, recno)
    last_key, last_rec = _leaf_last(data, tag, page_off)
    _update_ancestors(data, tag, ancestors, last_key, last_rec)


def _find_leaf(data: bytearray, tag: CdxTag, key: bytes, recno: int) -> int:
    page_off, _ancestors = _find_leaf_path(data, tag, key, recno)
    return page_off


def _find_leaf_path(data: bytearray, tag: CdxTag, key: bytes, recno: int) -> tuple[int, list[tuple[int, int]]]:
    page_off = tag.root
    ancestors: list[tuple[int, int]] = []
    while True:
        page = data[page_off : page_off + CDX_PAGE]
        attr = unpack("<H", page[0:2])[0]
        if attr & CDX_NODE_LEAF:
            return page_off, ancestors
        nkeys = unpack("<H", page[2:4])[0]
        slot = tag.key_size + 8
        child = 0
        chosen = 0
        for index in range(nkeys):
            base = CDX_INT_HEAD + index * slot
            item_key = bytes(page[base : base + tag.key_size])
            item_rec = unpack(">I", page[base + tag.key_size : base + tag.key_size + 4])[0]
            item_page = unpack(">I", page[base + tag.key_size + 4 : base + tag.key_size + 8])[0]
            child = item_page
            chosen = index
            if (item_key, item_rec) >= (key, recno):
                break
        if child == 0:
            raise ValueError("CDX interior ไม่มีหน้าลูก")
        ancestors.append((page_off, chosen))
        page_off = child


def _leaf_last(data: bytearray, tag: CdxTag, page_off: int) -> tuple[bytes, int]:
    page = data[page_off : page_off + CDX_PAGE]
    nkeys = unpack("<H", page[2:4])[0]
    rec_mask = unpack("<I", page[14:18])[0]
    decoded = _decode_leaf(
        page, tag.key_size, nkeys, page[23], rec_mask, page[21], page[22], page[18], page[19]
    )
    if not decoded:
        raise ValueError("CDX leaf ว่าง")
    last_key, last_rec, _dup, _trl = decoded[-1]
    return last_key, last_rec


def _update_ancestors(
    data: bytearray,
    tag: CdxTag,
    ancestors: list[tuple[int, int]],
    last_key: bytes,
    last_rec: int,
) -> None:
    for page_off, slot_index in reversed(ancestors):
        _write_interior_slot(data, tag, page_off, slot_index, last_key, last_rec)
        nkeys = unpack("<H", data[page_off + 2 : page_off + 4])[0]
        if slot_index != nkeys - 1:
            break


def _write_interior_slot(
    data: bytearray,
    tag: CdxTag,
    page_off: int,
    slot_index: int,
    key: bytes,
    recno: int,
) -> None:
    slot = tag.key_size + 8
    base = page_off + CDX_INT_HEAD + slot_index * slot
    data[base : base + tag.key_size] = key
    data[base + tag.key_size : base + tag.key_size + 4] = pack(">I", recno)


def _insert_leaf_key(data: bytearray, tag: CdxTag, page_off: int, key: bytes, recno: int) -> None:
    page = bytearray(data[page_off : page_off + CDX_PAGE])
    nkeys = unpack("<H", page[2:4])[0]
    free = unpack("<H", page[12:14])[0]
    rec_mask = unpack("<I", page[14:18])[0]
    dup_mask = page[18]
    trl_mask = page[19]
    rec_bits = page[20]
    dup_bits = page[21]
    trl_bits = page[22]
    req = page[23]
    decoded = _decode_leaf(page, tag.key_size, nkeys, req, rec_mask, dup_bits, trl_bits, dup_mask, trl_mask)
    index = 0
    while index < len(decoded):
        item_key, item_rec, _dup, _trl = decoded[index]
        if (item_key, item_rec) > (key, recno):
            break
        index += 1
    trail = 0
    while trail < tag.key_size and key[tag.key_size - 1 - trail] == tag.trail:
        trail += 1
    dup = 0
    if index > 0:
        prev = decoded[index - 1][0]
        limit = tag.key_size - trail
        while dup < limit and key[dup] == prev[dup]:
            dup += 1
    needed = req + tag.key_size - trail - dup
    if needed > free:
        raise ValueError("หน้า CDX เต็ม — ใส่ index ไม่ได้")
    decoded.insert(index, (key, recno, dup, trail))
    if index + 1 < len(decoded):
        nxt_key, nxt_rec, _old_dup, nxt_trl = decoded[index + 1]
        nxt_dup = 0
        nxt_limit = tag.key_size - nxt_trl
        while nxt_dup < nxt_limit and nxt_key[nxt_dup] == key[nxt_dup]:
            nxt_dup += 1
        decoded[index + 1] = (nxt_key, nxt_rec, nxt_dup, nxt_trl)
    encoded, new_free = _encode_leaf(decoded, tag.key_size, req, rec_bits, dup_bits, trl_bits, tag.trail)
    page[2:4] = pack("<H", len(decoded))
    page[12:14] = pack("<H", new_free)
    page[CDX_EXT_HEAD:] = encoded
    data[page_off : page_off + CDX_PAGE] = page


def _decode_leaf(
    page: bytes,
    key_size: int,
    nkeys: int,
    req: int,
    rec_mask: int,
    dup_bits: int,
    trl_bits: int,
    dup_mask: int,
    trl_mask: int,
) -> list[tuple[bytes, int, int, int]]:
    shift = 32 - trl_bits - dup_bits
    pool = page[CDX_EXT_HEAD:]
    src = len(pool)
    current = bytearray(b" " * key_size)
    out: list[tuple[bytes, int, int, int]] = []
    for index in range(nkeys):
        rec_off = CDX_EXT_HEAD + index * req
        recno = unpack("<I", page[rec_off : rec_off + 4])[0] & rec_mask
        info_off = CDX_EXT_HEAD + (index + 1) * req - 4
        info = unpack("<I", page[info_off : info_off + 4])[0] >> shift
        dup = 0 if index == 0 else info & dup_mask
        trl = (info >> dup_bits) & trl_mask
        unique = key_size - dup - trl
        if unique > 0:
            src -= unique
            current[dup : dup + unique] = pool[src : src + unique]
        if trl > 0:
            current[key_size - trl :] = bytes([0x20]) * trl
        out.append((bytes(current), recno, dup, trl))
    return out


def _encode_leaf(
    keys: list[tuple[bytes, int, int, int]],
    key_size: int,
    req: int,
    rec_bits: int,
    dup_bits: int,
    trl_bits: int,
    trail: int,
) -> tuple[bytes, int]:
    del rec_bits, trail
    pool = bytearray(CDX_PAGE - CDX_EXT_HEAD)
    rec_pos = 0
    key_pos = len(pool)
    for key, recno, dup, trl in keys:
        unique = key_size - trl - dup
        _set_leaf_record(pool, rec_pos, req, recno, dup, trl, dup_bits, trl_bits)
        rec_pos += req
        if unique > 0:
            key_pos -= unique
            pool[key_pos : key_pos + unique] = key[dup : dup + unique]
    if rec_pos < key_pos:
        pool[rec_pos:key_pos] = b"\x00" * (key_pos - rec_pos)
    return bytes(pool), key_pos - rec_pos


def _set_leaf_record(
    pool: bytearray,
    offset: int,
    req: int,
    recno: int,
    dup: int,
    trl: int,
    dup_bits: int,
    trl_bits: int,
) -> None:
    from_bytes = (trl_bits + dup_bits + 7) >> 3
    bits = ((trl << dup_bits) | dup) << ((from_bytes << 3) - trl_bits - dup_bits)
    start = req - from_bytes
    value = recno
    for index in range(req):
        byte = value & 0xFF
        if index >= start:
            byte |= bits & 0xFF
            bits >>= 8
        pool[offset + index] = byte
        value >>= 8

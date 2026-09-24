from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from struct import pack, unpack

CDX_PAGE = 512
CDX_EXT_HEAD = 24
CDX_INT_HEAD = 12
CDX_NODE_ROOT = 0x01
CDX_NODE_LEAF = 0x02
CDX_HEADER = 1024
CDX_NO_PAGE = 0xFFFFFFFF
CDX_LEAF_POOL = CDX_PAGE - CDX_EXT_HEAD


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
    split = _insert_leaf_key(data, tag, page_off, key, recno)
    if split is None:
        last_key, last_rec = _leaf_last(data, tag, page_off)
        _update_ancestors(data, tag, ancestors, last_key, last_rec)
        return
    left_off, right_off = split
    left_key, left_rec = _leaf_last(data, tag, left_off)
    right_key, right_rec = _leaf_last(data, tag, right_off)
    _promote_split(data, tag, ancestors, left_off, left_key, left_rec, right_off, right_key, right_rec)


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


def _insert_leaf_key(data: bytearray, tag: CdxTag, page_off: int, key: bytes, recno: int) -> tuple[int, int] | None:
    page = bytearray(data[page_off : page_off + CDX_PAGE])
    nkeys = unpack("<H", page[2:4])[0]
    rec_mask = unpack("<I", page[14:18])[0]
    req = page[23]
    decoded = _decode_leaf(page, tag.key_size, nkeys, req, rec_mask, page[21], page[22], page[18], page[19])
    index = 0
    while index < len(decoded):
        item_key, item_rec, _dup, _trl = decoded[index]
        if (item_key, item_rec) > (key, recno):
            break
        index += 1
    decoded.insert(index, (key, recno, 0, 0))
    decoded = _recompute_leaf_keys(decoded, tag.key_size, tag.trail)
    if _leaf_used(decoded, tag.key_size, req) <= CDX_LEAF_POOL:
        _write_leaf_keys(data, page_off, page, tag, decoded)
        return None
    return _split_leaf(data, tag, page_off, page, decoded)


def _recompute_leaf_keys(
    keys: list[tuple[bytes, int, int, int]], key_size: int, trail_byte: int
) -> list[tuple[bytes, int, int, int]]:
    out: list[tuple[bytes, int, int, int]] = []
    for index, (key, recno, _dup, _trl) in enumerate(keys):
        trail = 0
        while trail < key_size and key[key_size - 1 - trail] == trail_byte:
            trail += 1
        dup = 0
        if index > 0:
            prev = keys[index - 1][0]
            limit = key_size - trail
            while dup < limit and key[dup] == prev[dup]:
                dup += 1
        out.append((key, recno, dup, trail))
    return out


def _leaf_used(keys: list[tuple[bytes, int, int, int]], key_size: int, req: int) -> int:
    return sum(req + key_size - dup - trl for _key, _recno, dup, trl in keys)


def _write_leaf_keys(
    data: bytearray,
    page_off: int,
    template: bytes,
    tag: CdxTag,
    keys: list[tuple[bytes, int, int, int]],
    *,
    left: int | None = None,
    right: int | None = None,
    is_root: bool | None = None,
) -> None:
    page = bytearray(template[:CDX_PAGE])
    if len(page) < CDX_PAGE:
        page.extend(b"\x00" * (CDX_PAGE - len(page)))
    attr = unpack("<H", page[0:2])[0]
    if is_root is True:
        attr = CDX_NODE_ROOT | CDX_NODE_LEAF
    elif is_root is False:
        attr = CDX_NODE_LEAF
    page[0:2] = pack("<H", attr)
    if left is not None:
        page[4:8] = pack("<I", left)
    if right is not None:
        page[8:12] = pack("<I", right)
    req = page[23]
    encoded, new_free = _encode_leaf(keys, tag.key_size, req, page[20], page[21], page[22], tag.trail)
    if new_free < 0:
        raise ValueError("หน้า CDX เต็ม — ใส่ index ไม่ได้")
    page[2:4] = pack("<H", len(keys))
    page[12:14] = pack("<H", new_free)
    page[CDX_EXT_HEAD:] = encoded
    data[page_off : page_off + CDX_PAGE] = page


def _split_leaf(
    data: bytearray,
    tag: CdxTag,
    page_off: int,
    template: bytes,
    keys: list[tuple[bytes, int, int, int]],
) -> tuple[int, int]:
    req = template[23]
    left_keys, right_keys = _choose_leaf_split(keys, tag.key_size, req, tag.trail)
    new_off = _alloc_page(data)
    old_left = unpack("<I", template[4:8])[0]
    old_right = unpack("<I", template[8:12])[0]
    _write_leaf_keys(
        data, page_off, template, tag, left_keys, left=old_left, right=new_off, is_root=False
    )
    _write_leaf_keys(
        data, new_off, template, tag, right_keys, left=page_off, right=old_right, is_root=False
    )
    if old_right != CDX_NO_PAGE:
        data[old_right + 4 : old_right + 8] = pack("<I", new_off)
    return page_off, new_off


def _choose_leaf_split(
    keys: list[tuple[bytes, int, int, int]],
    key_size: int,
    req: int,
    trail_byte: int,
) -> tuple[list[tuple[bytes, int, int, int]], list[tuple[bytes, int, int, int]]]:
    target = len(keys) // 2
    best: tuple[int, list[tuple[bytes, int, int, int]], list[tuple[bytes, int, int, int]]] | None = None
    for mid in range(1, len(keys)):
        left = _recompute_leaf_keys(keys[:mid], key_size, trail_byte)
        right = _recompute_leaf_keys(keys[mid:], key_size, trail_byte)
        if _leaf_used(left, key_size, req) <= CDX_LEAF_POOL and _leaf_used(right, key_size, req) <= CDX_LEAF_POOL:
            if best is None or abs(mid - target) < abs(best[0] - target):
                best = (mid, left, right)
    if best is None:
        raise ValueError("แยกหน้า CDX ไม่ได้")
    return best[1], best[2]


def _alloc_page(data: bytearray) -> int:
    free = unpack("<I", data[4:8])[0]
    if free:
        nxt = unpack("<I", data[free : free + 4])[0]
        data[4:8] = pack("<I", nxt)
        data[free : free + CDX_PAGE] = b"\x00" * CDX_PAGE
        return free
    offset = len(data)
    data.extend(b"\x00" * CDX_PAGE)
    return offset


def _set_tag_root(data: bytearray, tag: CdxTag, root: int) -> None:
    tag.root = root
    data[tag.offset : tag.offset + 4] = pack("<I", root)


def _promote_split(
    data: bytearray,
    tag: CdxTag,
    ancestors: list[tuple[int, int]],
    left_off: int,
    left_key: bytes,
    left_rec: int,
    right_off: int,
    right_key: bytes,
    right_rec: int,
) -> None:
    if not ancestors:
        _new_root(data, tag, left_off, left_key, left_rec, right_off, right_key, right_rec)
        return
    parent_off, slot_index = ancestors[-1]
    _write_interior_slot(data, tag, parent_off, slot_index, left_key, left_rec)
    _insert_interior_slot(
        data, tag, ancestors[:-1], parent_off, slot_index + 1, right_key, right_rec, right_off
    )


def _new_root(
    data: bytearray,
    tag: CdxTag,
    left_off: int,
    left_key: bytes,
    left_rec: int,
    right_off: int,
    right_key: bytes,
    right_rec: int,
) -> None:
    root = _alloc_page(data)
    _write_interior_page(
        data,
        root,
        tag,
        [(left_key, left_rec, left_off), (right_key, right_rec, right_off)],
        CDX_NO_PAGE,
        CDX_NO_PAGE,
        is_root=True,
    )
    _set_tag_root(data, tag, root)


def _read_interior_slots(data: bytearray, tag: CdxTag, page_off: int) -> list[tuple[bytes, int, int]]:
    page = data[page_off : page_off + CDX_PAGE]
    nkeys = unpack("<H", page[2:4])[0]
    slot = tag.key_size + 8
    slots: list[tuple[bytes, int, int]] = []
    for index in range(nkeys):
        base = CDX_INT_HEAD + index * slot
        key = bytes(page[base : base + tag.key_size])
        recno = unpack(">I", page[base + tag.key_size : base + tag.key_size + 4])[0]
        child = unpack(">I", page[base + tag.key_size + 4 : base + tag.key_size + 8])[0]
        slots.append((key, recno, child))
    return slots


def _write_interior_page(
    data: bytearray,
    page_off: int,
    tag: CdxTag,
    slots: list[tuple[bytes, int, int]],
    left: int,
    right: int,
    *,
    is_root: bool,
) -> None:
    page = bytearray(CDX_PAGE)
    page[0:2] = pack("<H", CDX_NODE_ROOT if is_root else 0)
    page[2:4] = pack("<H", len(slots))
    page[4:8] = pack("<I", left)
    page[8:12] = pack("<I", right)
    slot = tag.key_size + 8
    for index, (key, recno, child) in enumerate(slots):
        base = CDX_INT_HEAD + index * slot
        page[base : base + tag.key_size] = key
        page[base + tag.key_size : base + tag.key_size + 4] = pack(">I", recno)
        page[base + tag.key_size + 4 : base + tag.key_size + 8] = pack(">I", child)
    data[page_off : page_off + CDX_PAGE] = page


def _insert_interior_slot(
    data: bytearray,
    tag: CdxTag,
    ancestors: list[tuple[int, int]],
    page_off: int,
    index: int,
    key: bytes,
    recno: int,
    child: int,
) -> None:
    slots = _read_interior_slots(data, tag, page_off)
    slots.insert(index, (key, recno, child))
    page = data[page_off : page_off + CDX_PAGE]
    left = unpack("<I", page[4:8])[0]
    right = unpack("<I", page[8:12])[0]
    max_keys = (CDX_PAGE - CDX_INT_HEAD) // (tag.key_size + 8)
    if len(slots) <= max_keys:
        _write_interior_page(data, page_off, tag, slots, left, right, is_root=page_off == tag.root)
        if ancestors and index == len(slots) - 1:
            last_key, last_rec, _child = slots[-1]
            _update_ancestors(data, tag, ancestors, last_key, last_rec)
        return
    mid = len(slots) // 2
    new_off = _alloc_page(data)
    _write_interior_page(data, page_off, tag, slots[:mid], left, new_off, is_root=False)
    _write_interior_page(data, new_off, tag, slots[mid:], page_off, right, is_root=False)
    if right != CDX_NO_PAGE:
        data[right + 4 : right + 8] = pack("<I", new_off)
    left_key, left_rec, _left_child = slots[mid - 1]
    right_key, right_rec, _right_child = slots[-1]
    _promote_split(data, tag, ancestors, page_off, left_key, left_rec, new_off, right_key, right_rec)


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

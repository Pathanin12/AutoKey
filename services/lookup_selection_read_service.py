"""อ่านชื่อแถวที่เลือกในหน้าจอ Express — ฟอร์ม F8 อยู่ในโปรแกรม Express ไม่ใช่หน้าต่างแยกเสมอไป"""

from __future__ import annotations

import sys

_AUTOKEY_TITLE_NEEDLE = "autokey"


def read_selected_row_text(
    *,
    name_subitems: tuple[int, ...] = (1, 0, 2, 3),
    express_title_contains: str = "Express",
) -> str:
    if sys.platform != "win32":
        return ""

    express_hwnd = _find_express_window_hwnd(express_title_contains)
    if not express_hwnd:
        return ""

    readers = (
        lambda: _read_via_uiautomation(express_title_contains, name_subitems),
        lambda: _read_via_uiautomation_hwnd(express_hwnd, name_subitems),
        lambda: _read_via_listview(express_hwnd, name_subitems),
        lambda: _read_via_focused_control(express_hwnd),
    )
    for read in readers:
        text = read().strip()
        if text:
            return text
    return ""


def _find_express_window_hwnd(express_title_contains: str) -> int | None:
    express_hwnd = _find_window_by_title_contains(express_title_contains)
    if express_hwnd:
        return express_hwnd

    import ctypes

    foreground = int(ctypes.windll.user32.GetForegroundWindow())
    if foreground and not _is_autokey_window(foreground):
        return foreground

    return None


def _is_autokey_window(hwnd: int) -> bool:
    title = _get_window_title(hwnd).casefold()
    return _AUTOKEY_TITLE_NEEDLE in title


def _find_window_by_title_contains(title_contains: str) -> int | None:
    if not title_contains.strip():
        return None

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    matches: list[int] = []
    needle = title_contains.casefold()

    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @EnumWindowsProc
    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _get_window_title(int(hwnd))
        if needle in title.casefold():
            matches.append(int(hwnd))
        return True

    user32.EnumWindows(callback, 0)
    return matches[0] if matches else None


def _get_window_title(hwnd: int) -> str:
    import ctypes

    user32 = ctypes.windll.user32
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _get_class_name(hwnd: int) -> str:
    import ctypes

    user32 = ctypes.windll.user32
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, 256)
    return buffer.value


def _read_via_uiautomation(express_title_contains: str, name_subitems: tuple[int, ...]) -> str:
    try:
        import uiautomation as auto
    except ImportError:
        return ""

    express = auto.WindowControl(searchDepth=2, SubName=express_title_contains)
    if not express.Exists(maxSearchSeconds=0.3):
        return ""

    return _uia_collect_selected_text(express, name_subitems)


def _read_via_uiautomation_hwnd(express_hwnd: int, name_subitems: tuple[int, ...]) -> str:
    try:
        import uiautomation as auto
    except ImportError:
        return ""

    root = auto.ControlFromHandle(express_hwnd)
    if root is None or not root.Exists(maxSearchSeconds=0.2):
        return ""

    return _uia_collect_selected_text(root, name_subitems)


def _uia_collect_selected_text(root, name_subitems: tuple[int, ...]) -> str:
    for reader in (
        lambda: _uia_selected_from_patterns(root, name_subitems),
        lambda: _uia_selected_from_lists(root),
        lambda: _uia_selected_from_grid(root, name_subitems),
        lambda: _uia_walk_selected(root, name_subitems),
    ):
        text = reader().strip()
        if text:
            return text
    return ""


def _uia_selected_from_patterns(root, name_subitems: tuple[int, ...]) -> str:
    import uiautomation as auto

    for control, _depth in auto.WalkControl(root, includeTop=True, maxDepth=35):
        for reader in (
            lambda: _uia_selection_item(control, name_subitems),
            lambda: _uia_selection_container(control, name_subitems),
        ):
            text = reader().strip()
            if text:
                return text
    return ""


def _uia_selection_item(control, name_subitems: tuple[int, ...]) -> str:
    pattern = control.GetSelectionItemPattern()
    if pattern is None or not pattern.IsSelected:
        return ""
    return _uia_control_text(control, name_subitems)


def _uia_selection_container(control, name_subitems: tuple[int, ...]) -> str:
    pattern = control.GetSelectionPattern()
    if pattern is None:
        return ""
    for item in pattern.GetSelection():
        text = _uia_control_text(item, name_subitems)
        if text:
            return text
    return ""


def _uia_selected_from_lists(root) -> str:
    import uiautomation as auto

    list_control = root.ListControl(searchDepth=25)
    if not list_control.Exists(maxSearchSeconds=0.1):
        return ""
    pattern = list_control.GetSelectionPattern()
    if pattern is None:
        return ""
    for item in pattern.GetSelection():
        text = (item.Name or "").strip()
        if text:
            return text
    return ""


def _uia_selected_from_grid(root, name_subitems: tuple[int, ...]) -> str:
    import uiautomation as auto

    for finder in (root.DataGridControl, root.TableControl, root.TreeControl):
        control = finder(searchDepth=25)
        if not control.Exists(maxSearchSeconds=0.1):
            continue
        for row in control.GetChildren():
            if not (_uia_is_selected(row) or row.HasKeyboardFocus):
                continue
            text = _uia_control_text(row, name_subitems)
            if text:
                return text
    return ""


def _uia_walk_selected(root, name_subitems: tuple[int, ...]) -> str:
    import uiautomation as auto

    for control, _depth in auto.WalkControl(root, includeTop=True, maxDepth=35):
        if not (_uia_is_selected(control) or control.HasKeyboardFocus):
            continue
        text = _uia_control_text(control, name_subitems)
        if text:
            return text
    return ""


def _uia_is_selected(control) -> bool:
    try:
        pattern = control.GetSelectionItemPattern()
        return pattern is not None and pattern.IsSelected
    except Exception:
        return False


def _uia_control_text(control, name_subitems: tuple[int, ...]) -> str:
    children = control.GetChildren()
    if children:
        for subitem in name_subitems:
            if 0 <= subitem < len(children):
                text = _uia_leaf_text(children[subitem])
                if text:
                    return text
        for child in children:
            text = _uia_leaf_text(child)
            if text:
                return text

    return _uia_leaf_text(control)


def _uia_leaf_text(control) -> str:
    name = (control.Name or "").strip()
    if name:
        return name
    try:
        value_pattern = control.GetValuePattern()
        if value_pattern is not None:
            value = (value_pattern.Value or "").strip()
            if value:
                return value
    except Exception:
        pass
    return ""


def _read_via_listview(express_hwnd: int, name_subitems: tuple[int, ...]) -> str:
    for hwnd in _find_child_class_handles(express_hwnd, "SysListView32"):
        selected_index = _listview_selected_index(hwnd)
        if selected_index < 0:
            selected_index = 0
        for subitem in name_subitems:
            text = _listview_subitem_text(hwnd, selected_index, subitem)
            if text:
                return text
    return ""


def _read_via_focused_control(express_hwnd: int) -> str:
    import ctypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    target_thread = user32.GetWindowThreadProcessId(express_hwnd, None)
    current_thread = kernel32.GetCurrentThreadId()
    attached = False
    try:
        if target_thread and target_thread != current_thread:
            user32.AttachThreadInput(current_thread, target_thread, True)
            attached = True
        focused = int(user32.GetFocus())
    finally:
        if attached:
            user32.AttachThreadInput(current_thread, target_thread, False)

    if not focused:
        return ""

    return _read_window_text(focused)


def _read_window_text(hwnd: int) -> str:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    WM_GETTEXT = 0x000D
    WM_GETTEXTLENGTH = 0x000E

    length = int(user32.SendMessageW(hwnd, WM_GETTEXTLENGTH, 0, 0))
    if length > 0:
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.SendMessageW(
            hwnd,
            WM_GETTEXT,
            length + 1,
            ctypes.cast(buffer, wintypes.LPARAM),
        )
        text = buffer.value.strip()
        if text:
            return text

    title_length = user32.GetWindowTextLengthW(hwnd)
    if title_length > 0:
        buffer = ctypes.create_unicode_buffer(title_length + 1)
        user32.GetWindowTextW(hwnd, buffer, title_length + 1)
        return buffer.value.strip()

    return ""


def _find_child_class_handles(parent: int, class_name: str) -> list[int]:
    if not parent:
        return []

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    handles: list[int] = []

    EnumChildProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @EnumChildProc
    def callback(hwnd, _lparam):
        if _get_class_name(int(hwnd)) == class_name:
            handles.append(int(hwnd))
        handles.extend(_find_child_class_handles(int(hwnd), class_name))
        return True

    user32.EnumChildWindows(parent, callback, 0)
    return handles


def _listview_selected_index(hwnd: int) -> int:
    import ctypes

    user32 = ctypes.windll.user32
    LVM_GETNEXTITEM = 0x100C
    LVNI_SELECTED = 0x0002
    return int(user32.SendMessageW(hwnd, LVM_GETNEXTITEM, -1, LVNI_SELECTED))


def _listview_subitem_text(hwnd: int, item_index: int, subitem: int) -> str:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    LVM_GETITEMTEXTW = 0x1073
    LVIF_TEXT = 0x0001

    class LVITEMW(ctypes.Structure):
        _fields_ = [
            ("mask", wintypes.UINT),
            ("iItem", ctypes.c_int),
            ("iSubItem", ctypes.c_int),
            ("state", wintypes.UINT),
            ("stateMask", wintypes.UINT),
            ("pszText", wintypes.LPWSTR),
            ("cchTextMax", ctypes.c_int),
            ("iImage", ctypes.c_int),
            ("lParam", wintypes.LPARAM),
            ("iIndent", ctypes.c_int),
            ("iGroupId", ctypes.c_int),
            ("cColumns", wintypes.UINT),
            ("puColumns", wintypes.LPVOID),
        ]

    buffer = ctypes.create_unicode_buffer(1024)
    item = LVITEMW()
    item.mask = LVIF_TEXT
    item.iItem = item_index
    item.iSubItem = subitem
    item.pszText = ctypes.cast(buffer, wintypes.LPWSTR)
    item.cchTextMax = 1024
    user32.SendMessageW(hwnd, LVM_GETITEMTEXTW, item_index, ctypes.byref(item))
    return buffer.value.strip()

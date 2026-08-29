"""เลือกไฟล์บน Windows — GetOpenFileNameW แล้วค่อย IFileOpenDialog"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from uuid import UUID

from constants.routes import EXCEL_OPEN_EXTENSIONS, UI_TEXT

ole32 = ctypes.WinDLL("ole32")
comdlg32 = ctypes.WinDLL("comdlg32")

CLSCTX_INPROC_SERVER = 1
FOS_FORCEFILESYSTEM = 0x40
FOS_PATHMUSTEXIST = 0x800
FOS_FILEMUSTEXIST = 0x1000
SIGDN_FILESYSPATH = 0x80058000
S_OK = 0
OFN_HIDEREADONLY = 0x00000004
OFN_PATHMUSTEXIST = 0x00000800
OFN_FILEMUSTEXIST = 0x00001000
OFN_EXPLORER = 0x00080000
OFN_ENABLESIZING = 0x00800000
HRESULT = ctypes.c_long


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_string(cls, text: str) -> "GUID":
        parsed = UUID(text)
        return cls(
            parsed.time_low,
            parsed.time_mid,
            parsed.time_hi_version,
            (ctypes.c_ubyte * 8).from_buffer_copy(parsed.bytes[8:]),
        )


class COMDLG_FILTERSPEC(ctypes.Structure):
    _fields_ = [("pszName", wintypes.LPCWSTR), ("pszSpec", wintypes.LPCWSTR)]


class OPENFILENAMEW(ctypes.Structure):
    _fields_ = [
        ("lStructSize", wintypes.DWORD),
        ("hwndOwner", wintypes.HWND),
        ("hInstance", wintypes.HINSTANCE),
        ("lpstrFilter", wintypes.LPCWSTR),
        ("lpstrCustomFilter", wintypes.LPWSTR),
        ("nMaxCustFilter", wintypes.DWORD),
        ("nFilterIndex", wintypes.DWORD),
        ("lpstrFile", wintypes.LPWSTR),
        ("nMaxFile", wintypes.DWORD),
        ("lpstrFileTitle", wintypes.LPWSTR),
        ("nMaxFileTitle", wintypes.DWORD),
        ("lpstrInitialDir", wintypes.LPCWSTR),
        ("lpstrTitle", wintypes.LPCWSTR),
        ("Flags", wintypes.DWORD),
        ("nFileOffset", wintypes.WORD),
        ("nFileExtension", wintypes.WORD),
        ("lpstrDefExt", wintypes.LPCWSTR),
        ("lCustData", ctypes.c_void_p),
        ("lpfnHook", ctypes.c_void_p),
        ("lpTemplateName", wintypes.LPCWSTR),
    ]


CLSID_FileOpenDialog = GUID.from_string("DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7")
IID_IFileOpenDialog = GUID.from_string("D57C7288-D4AD-4768-BE02-9D969532D960")

ole32.CoCreateInstance.argtypes = [
    ctypes.POINTER(GUID),
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(GUID),
    ctypes.POINTER(ctypes.c_void_p),
]
ole32.CoCreateInstance.restype = HRESULT
ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
comdlg32.GetOpenFileNameW.argtypes = [ctypes.POINTER(OPENFILENAMEW)]
comdlg32.GetOpenFileNameW.restype = wintypes.BOOL
comdlg32.CommDlgExtendedError.argtypes = []
comdlg32.CommDlgExtendedError.restype = wintypes.DWORD


def pick_excel_path(owner_hwnd) -> str | None:
    try:
        path = _pick_with_get_open_file_name(owner_hwnd)
        if path:
            return path
    except Exception:
        pass
    try:
        return _pick_with_file_open_dialog(owner_hwnd)
    except Exception:
        return None


def _pick_with_get_open_file_name(owner_hwnd) -> str | None:
    extensions = ";".join(f"*.{ext}" for ext in EXCEL_OPEN_EXTENSIONS)
    file_buf = ctypes.create_unicode_buffer(32768)
    filter_buf = _wchar_zchunks(f"Excel ({extensions})", extensions, "All files (*.*)", "*.*")
    title_buf = ctypes.create_unicode_buffer(UI_TEXT["choose_file"])
    defext_buf = ctypes.create_unicode_buffer(EXCEL_OPEN_EXTENSIONS[0])
    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.hwndOwner = owner_hwnd or None
    ofn.lpstrFilter = ctypes.cast(filter_buf, wintypes.LPCWSTR)
    ofn.nFilterIndex = 1
    ofn.lpstrFile = file_buf
    ofn.nMaxFile = len(file_buf)
    ofn.lpstrTitle = title_buf
    ofn.Flags = OFN_EXPLORER | OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST | OFN_HIDEREADONLY | OFN_ENABLESIZING
    ofn.lpstrDefExt = defext_buf
    if comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
        return file_buf.value
    return None


def _pick_with_file_open_dialog(owner_hwnd) -> str | None:
    dialog = ctypes.c_void_p()
    hr = ole32.CoCreateInstance(
        ctypes.byref(CLSID_FileOpenDialog),
        None,
        CLSCTX_INPROC_SERVER,
        ctypes.byref(IID_IFileOpenDialog),
        ctypes.byref(dialog),
    )
    if int(hr) != S_OK or not dialog.value:
        return None
    obj = dialog.value
    spec = ";".join(f"*.{ext}" for ext in EXCEL_OPEN_EXTENSIONS)
    name = f"Excel ({spec})"
    filters = (COMDLG_FILTERSPEC * 2)(
        COMDLG_FILTERSPEC(name, spec),
        COMDLG_FILTERSPEC("All files (*.*)", "*.*"),
    )
    try:
        if _vtable_call(obj, 4, HRESULT, [ctypes.POINTER(COMDLG_FILTERSPEC), ctypes.c_uint], ctypes.cast(filters, ctypes.POINTER(COMDLG_FILTERSPEC)), 2) != S_OK:
            return None
        _vtable_call(
            obj,
            9,
            HRESULT,
            [wintypes.DWORD],
            FOS_FORCEFILESYSTEM | FOS_FILEMUSTEXIST | FOS_PATHMUSTEXIST,
        )
        _vtable_call(obj, 17, HRESULT, [wintypes.LPCWSTR], UI_TEXT["choose_file"])
        _vtable_call(obj, 22, HRESULT, [wintypes.LPCWSTR], EXCEL_OPEN_EXTENSIONS[0])
        hr = _vtable_call(obj, 3, HRESULT, [wintypes.HWND], owner_hwnd)
        if int(hr) != S_OK:
            return None
        item = ctypes.c_void_p()
        if _vtable_call(obj, 20, HRESULT, [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(item)) != S_OK:
            return None
        if not item.value:
            return None
        try:
            path_ptr = wintypes.LPWSTR()
            hr = _vtable_call(
                item.value,
                5,
                HRESULT,
                [ctypes.c_uint32, ctypes.POINTER(wintypes.LPWSTR)],
                SIGDN_FILESYSPATH,
                ctypes.byref(path_ptr),
            )
            if int(hr) != S_OK or not path_ptr:
                return None
            path = path_ptr.value
            ole32.CoTaskMemFree(path_ptr)
            return path
        finally:
            _vtable_call(item.value, 2, ctypes.c_ulong, [])
    finally:
        _vtable_call(obj, 2, ctypes.c_ulong, [])


def _vtable_call(obj, index, restype, argtypes, *args):
    vtable = ctypes.cast(ctypes.cast(obj, ctypes.POINTER(ctypes.c_void_p)).contents, ctypes.POINTER(ctypes.c_void_p))
    proto = ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
    return proto(vtable[index])(obj, *args)


def _wchar_zchunks(*parts: str):
    payload = "\0".join(parts) + "\0\0"
    buf = ctypes.create_unicode_buffer(len(payload))
    for index, char in enumerate(payload):
        buf[index] = char
    return buf

#!/usr/bin/env python3
"""Bump patch version — single source: constants/version.py"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_PY = ROOT / "constants" / "version.py"
VERSION_INFO = ROOT / "packaging" / "version_info.txt"


def _parse_version(text: str) -> tuple[int, int, int]:
    match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', text)
    if not match:
        raise ValueError(f"ไม่พบ __version__ ใน {VERSION_PY}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _bump_patch(version: tuple[int, int, int]) -> str:
    major, minor, patch = version
    return f"{major}.{minor}.{patch + 1}"


def _write_version_py(new_version: str) -> None:
    text = VERSION_PY.read_text(encoding="utf-8")
    updated = re.sub(
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{new_version}"',
        text,
        count=1,
    )
    VERSION_PY.write_text(updated, encoding="utf-8")


def _write_version_info(new_version: str) -> None:
    major, minor, patch = (int(part) for part in new_version.split("."))
    build = 0
    win_version = f"{major}.{minor}.{patch}.{build}"
    text = VERSION_INFO.read_text(encoding="utf-8")
    text = re.sub(
        r"filevers=\(\d+, \d+, \d+, \d+\)",
        f"filevers=({major}, {minor}, {patch}, {build})",
        text,
        count=1,
    )
    text = re.sub(
        r"prodvers=\(\d+, \d+, \d+, \d+\)",
        f"prodvers=({major}, {minor}, {patch}, {build})",
        text,
        count=1,
    )
    text = re.sub(
        r"StringStruct\('FileVersion', '[^']+'\)",
        f"StringStruct('FileVersion', '{win_version}')",
        text,
        count=1,
    )
    text = re.sub(
        r"StringStruct\('ProductVersion', '[^']+'\)",
        f"StringStruct('ProductVersion', '{win_version}')",
        text,
        count=1,
    )
    VERSION_INFO.write_text(text, encoding="utf-8")


def bump_version() -> str:
    current = _parse_version(VERSION_PY.read_text(encoding="utf-8"))
    new_version = _bump_patch(current)
    _write_version_py(new_version)
    _write_version_info(new_version)
    return new_version


def main() -> None:
    print(bump_version())


if __name__ == "__main__":
    main()

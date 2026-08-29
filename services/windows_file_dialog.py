"""เลือกไฟล์บน Windows — ใช้ OpenFileDialog ของระบบผ่าน PowerShell"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from constants.routes import EXCEL_OPEN_EXTENSIONS, UI_TEXT


def pick_excel_path(_owner_hwnd=None) -> str | None:
    extensions = ";".join(f"*.{ext}" for ext in EXCEL_OPEN_EXTENSIONS)
    out_file = Path(tempfile.gettempdir()) / "autokey_picked_excel.txt"
    if out_file.exists():
        out_file.unlink()
    out_ps = str(out_file).replace("'", "''")
    title = UI_TEXT["choose_file"].replace("'", "''")
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$d = New-Object System.Windows.Forms.OpenFileDialog; "
        f"$d.Title = '{title}'; "
        f"$d.Filter = 'Excel ({extensions})|{extensions}|All files (*.*)|*.*'; "
        "$d.Multiselect = $false; "
        "if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { "
        f"[System.IO.File]::WriteAllText('{out_ps}', $d.FileName, [System.Text.UTF8Encoding]::new($false)) "
        "}"
    )
    completed = subprocess.run(
        [
            "powershell",
            "-STA",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-Command",
            script,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if out_file.exists():
        path = out_file.read_text(encoding="utf-8").strip()
        out_file.unlink(missing_ok=True)
        if path:
            return path
    if completed.returncode not in (0, None) and completed.stderr:
        raise RuntimeError(completed.stderr.strip()[:500])
    return None

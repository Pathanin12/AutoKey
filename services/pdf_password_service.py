from __future__ import annotations


class PdfLockedError(Exception):
    pass


class PdfPasswordService:
    @staticmethod
    def unlock(reader, password: str) -> None:
        if not reader.is_encrypted:
            return
        if not reader.decrypt(password or ""):
            raise PdfLockedError()

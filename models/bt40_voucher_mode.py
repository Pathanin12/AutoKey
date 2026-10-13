from __future__ import annotations

from dataclasses import dataclass

from constants.routes import BT40_MODE_ALL, BT40_MODE_PV, BT40_MODE_RV, BT40_VOUCHER_MODES, UI_TEXT


@dataclass(frozen=True)
class Bt40VoucherMode:
    key: str

    @staticmethod
    def all() -> Bt40VoucherMode:
        return Bt40VoucherMode(key=BT40_MODE_ALL)

    @staticmethod
    def pv() -> Bt40VoucherMode:
        return Bt40VoucherMode(key=BT40_MODE_PV)

    @staticmethod
    def rv() -> Bt40VoucherMode:
        return Bt40VoucherMode(key=BT40_MODE_RV)

    @staticmethod
    def parse(value: str) -> Bt40VoucherMode:
        key = (value or "").strip() or BT40_MODE_ALL
        if key not in BT40_VOUCHER_MODES:
            return Bt40VoucherMode.all()
        return Bt40VoucherMode(key=key)

    @property
    def label(self) -> str:
        if self.key == BT40_MODE_PV:
            return UI_TEXT["bt40_mode_pv"]
        if self.key == BT40_MODE_RV:
            return UI_TEXT["bt40_mode_rv"]
        return UI_TEXT["bt40_mode_all"]

    @property
    def include_rv(self) -> bool:
        return self.key in (BT40_MODE_ALL, BT40_MODE_RV)

    @property
    def include_pv(self) -> bool:
        return self.key in (BT40_MODE_ALL, BT40_MODE_PV)

    @property
    def is_valid(self) -> bool:
        return self.key in BT40_VOUCHER_MODES

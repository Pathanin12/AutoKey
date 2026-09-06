from __future__ import annotations

from dataclasses import dataclass

from constants.routes import (
    PP30_KIND_NO_PAY_NEW_SHOP,
    PP30_KIND_NO_PAY_NORMAL,
    PP30_KIND_PAY,
    PP30_KIND_PENALTY,
    PP30_KIND_SKIP_ZERO,
    PP30_KIND_UNKNOWN,
    PP30_PAYMENT_KINDS,
    UI_TEXT,
)


@dataclass(frozen=True)
class Pp30PaymentKind:
    key: str

    @staticmethod
    def no_pay_normal() -> Pp30PaymentKind:
        return Pp30PaymentKind(key=PP30_KIND_NO_PAY_NORMAL)

    @staticmethod
    def no_pay_new_shop() -> Pp30PaymentKind:
        return Pp30PaymentKind(key=PP30_KIND_NO_PAY_NEW_SHOP)

    @staticmethod
    def pay() -> Pp30PaymentKind:
        return Pp30PaymentKind(key=PP30_KIND_PAY)

    @staticmethod
    def penalty() -> Pp30PaymentKind:
        return Pp30PaymentKind(key=PP30_KIND_PENALTY)

    @staticmethod
    def skip_zero() -> Pp30PaymentKind:
        return Pp30PaymentKind(key=PP30_KIND_SKIP_ZERO)

    @staticmethod
    def unknown() -> Pp30PaymentKind:
        return Pp30PaymentKind(key=PP30_KIND_UNKNOWN)

    @staticmethod
    def parse(value: str) -> Pp30PaymentKind:
        key = (value or "").strip() or PP30_KIND_UNKNOWN
        if key not in PP30_PAYMENT_KINDS:
            return Pp30PaymentKind.unknown()
        return Pp30PaymentKind(key=key)

    @property
    def label(self) -> str:
        labels = {
            PP30_KIND_NO_PAY_NORMAL: UI_TEXT["pp30_kind_no_pay_normal"],
            PP30_KIND_NO_PAY_NEW_SHOP: UI_TEXT["pp30_kind_no_pay_new_shop"],
            PP30_KIND_PAY: UI_TEXT["pp30_kind_pay"],
            PP30_KIND_PENALTY: UI_TEXT["pp30_kind_penalty"],
            PP30_KIND_SKIP_ZERO: UI_TEXT["pp30_kind_skip_zero"],
            PP30_KIND_UNKNOWN: UI_TEXT["pp30_kind_unknown"],
        }
        return labels.get(self.key, UI_TEXT["pp30_kind_unknown"])

    @property
    def is_skip(self) -> bool:
        return self.key == PP30_KIND_SKIP_ZERO

    @property
    def is_no_pay_normal(self) -> bool:
        return self.key == PP30_KIND_NO_PAY_NORMAL

    @property
    def is_new_shop(self) -> bool:
        return self.key == PP30_KIND_NO_PAY_NEW_SHOP

    @property
    def is_pay(self) -> bool:
        return self.key == PP30_KIND_PAY

    @property
    def is_penalty(self) -> bool:
        return self.key == PP30_KIND_PENALTY

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SHOP_TZ = ZoneInfo("Europe/Madrid")  # Spain time (handles DST)


class BookingValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end

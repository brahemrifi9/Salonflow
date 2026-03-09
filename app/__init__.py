from __future__ import annotations

from datetime import datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo

SHOP_TZ = ZoneInfo("Europe/Madrid")  # Spain time (handles DST)

class BookingValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

def _time_in_range(t: time, start: time, end: time) -> bool:
    # inclusive start, exclusive end
    return start <= t < end

def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    # [start, end) overlap check
    return a_start < b_end and b_start < a_end

def validate_new_booking_start(
    *,
    start_time: datetime,
    duration_minutes: int,
    now_utc: datetime | None = None,
) -> tuple[datetime, datetime]:
    """
    Returns (start_utc, end_utc) if valid, otherwise raises BookingValidationError.
    """
    start_utc = ensure_utc_aware(start_time)
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    # 1) Future-only (allow a small buffer if you want; here it's strict)
    if start_utc <= now_utc:
        raise BookingValidationError("Booking start_time must be in the future.")

    # 2) Slot alignment (15-min grid)
    if start_utc.second != 0 or start_utc.microsecond != 0:
        raise BookingValidationError("start_time must be aligned to the minute (no seconds).")
    if (start_utc.minute % RULES.slot_minutes) != 0:
        raise BookingValidationError(f"start_time must be aligned to {RULES.slot_minutes}-minute slots.")

    # 3) Compute end_time
    if duration_minutes <= 0:
        raise BookingValidationError("Service duration must be > 0 minutes.")
    end_utc = start_utc + timedelta(minutes=duration_minutes)

    # Validate business hours/lunch in SHOP LOCAL time
    start_local = to_shop_local(start_utc)
    end_local = to_shop_local(end_utc)

    # 4) Same-day rule (optional, but usually required for barbershop slots)
    if start_local.date() != end_local.date():
        raise BookingValidationError("Booking cannot cross midnight.")

    # 5) Business hours window
    open_dt = start_local.replace(hour=RULES.open_time.hour, minute=RULES.open_time.minute, second=0, microsecond=0)
    close_dt = start_local.replace(hour=RULES.close_time.hour, minute=RULES.close_time.minute, second=0, microsecond=0)

    if not (start_local >= open_dt and end_local <= close_dt):
        raise BookingValidationError("Booking is outside business hours (11:00–21:30).")

    # 6) Lunch break overlap
    lunch_start_dt = start_local.replace(hour=RULES.lunch_start.hour, minute=RULES.lunch_start.minute, second=0, microsecond=0)
    lunch_end_dt = start_local.replace(hour=RULES.lunch_end.hour, minute=RULES.lunch_end.minute, second=0, microsecond=0)

    if _overlaps(start_local, end_local, lunch_start_dt, lunch_end_dt):
        raise BookingValidationError("Booking overlaps lunch break (15:00–16:00).")

    return start_utc, end_utc
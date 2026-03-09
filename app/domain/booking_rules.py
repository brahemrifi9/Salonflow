from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status


MADRID_TZ = ZoneInfo("Europe/Madrid")


@dataclass(frozen=True)
class BusinessHours:
    open_time: time = time(11, 0)
    close_time: time = time(21, 30)
    lunch_start: time = time(15, 0)
    lunch_end: time = time(16, 0)
    slot_step_minutes: int = 15


BUSINESS_HOURS = BusinessHours()


def _raise_400(msg: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


def validate_and_compute_end_time_utc(
    start_time: datetime,
    duration_minutes: int,
    *,
    now_utc: datetime | None = None,
    require_client_utc: bool = True,
    enforce_slot_step: bool = True,
    business: BusinessHours = BUSINESS_HOURS,
) -> tuple[datetime, datetime]:
    """
    Validates booking business rules and returns (start_utc, end_utc).

    - Enforces tz-aware datetime
    - Optionally enforces that client sent UTC (offset 0)
    - Converts to UTC for storage
    - Validates business hours + lunch in Europe/Madrid (DST-safe)
    """
    if start_time.tzinfo is None or start_time.utcoffset() is None:
        _raise_400("La hora de inicio debe incluir zona horaria (formato ISO).")

    # If you want to force clients to send 'Z' / UTC specifically:
    if require_client_utc and start_time.utcoffset() != timedelta(0):
        _raise_400("La hora de inicio debe estar en UTC (terminar en 'Z').")

    start_utc = start_time.astimezone(timezone.utc)

    now_utc = now_utc or datetime.now(timezone.utc)
    if start_utc < now_utc:
        _raise_400("No se pueden hacer reservas en el pasado.")

    if duration_minutes <= 0:
        _raise_400("La duración del servicio no es válida.")

    if enforce_slot_step:
        if (start_utc.minute % business.slot_step_minutes) != 0 or start_utc.second != 0 or start_utc.microsecond != 0:
            _raise_400(f"La hora de inicio debe ser en intervalos de {business.slot_step_minutes} minutos.")

    end_utc = start_utc + timedelta(minutes=duration_minutes)

    # Validate business rules in local salon time (Europe/Madrid)
    start_local = start_utc.astimezone(MADRID_TZ)
    end_local = end_utc.astimezone(MADRID_TZ)

    # Sanity: booking should not go backwards
    if end_local <= start_local:
        _raise_400("La reserva no es válida.")

    # Business day boundaries (same local date as start)
    day = start_local.date()
    open_dt = datetime.combine(day, business.open_time, tzinfo=MADRID_TZ)
    close_dt = datetime.combine(day, business.close_time, tzinfo=MADRID_TZ)

    # Must be fully inside opening hours
    # Note: allow start exactly at open, allow end exactly at close.
    if not (open_dt <= start_local and end_local <= close_dt):
        _raise_400("La reserva está fuera del horario comercial (11:00–21:30).")

    # Lunch block [15:00, 16:00)
    lunch_start_dt = datetime.combine(day, business.lunch_start, tzinfo=MADRID_TZ)
    lunch_end_dt = datetime.combine(day, business.lunch_end, tzinfo=MADRID_TZ)

    # Overlap check: ranges intersect if start < lunch_end AND end > lunch_start
    if start_local < lunch_end_dt and end_local > lunch_start_dt:
        _raise_400("La reserva coincide con la pausa de comida (15:00–16:00).")

    return start_utc, end_utc
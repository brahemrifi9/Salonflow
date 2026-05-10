from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from app import models


MADRID_TZ = ZoneInfo("Europe/Madrid")

_SLOT_STEP_MINUTES = 15


def _raise_400(msg: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


def validate_and_compute_end_time_utc(
    start_time: datetime,
    duration_minutes: int,
    *,
    now_utc: datetime | None = None,
    require_client_utc: bool = True,
    enforce_slot_step: bool = True,
    business: models.Business,
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

    if require_client_utc and start_time.utcoffset() != timedelta(0):
        _raise_400("La hora de inicio debe estar en UTC (terminar en 'Z').")

    start_utc = start_time.astimezone(timezone.utc)

    now_utc = now_utc or datetime.now(timezone.utc)
    if start_utc < now_utc:
        _raise_400("No se pueden hacer reservas en el pasado.")

    if duration_minutes <= 0:
        _raise_400("La duración del servicio no es válida.")

    if enforce_slot_step:
        if (start_utc.minute % _SLOT_STEP_MINUTES) != 0 or start_utc.second != 0 or start_utc.microsecond != 0:
            _raise_400(f"La hora de inicio debe ser en intervalos de {_SLOT_STEP_MINUTES} minutos.")

    end_utc = start_utc + timedelta(minutes=duration_minutes)

    start_local = start_utc.astimezone(MADRID_TZ)
    end_local = end_utc.astimezone(MADRID_TZ)

    if end_local <= start_local:
        _raise_400("La reserva no es válida.")

    day = start_local.date()
    open_dt = datetime.combine(day, business.open_time, tzinfo=MADRID_TZ)
    close_dt = datetime.combine(day, business.close_time, tzinfo=MADRID_TZ)

    if not (open_dt <= start_local and end_local <= close_dt):
        _raise_400(
            f"La reserva está fuera del horario comercial "
            f"({business.open_time.strftime('%H:%M')}–{business.close_time.strftime('%H:%M')})."
        )

    lunch_start_dt = datetime.combine(day, business.lunch_start, tzinfo=MADRID_TZ)
    lunch_end_dt = datetime.combine(day, business.lunch_end, tzinfo=MADRID_TZ)

    if start_local < lunch_end_dt and end_local > lunch_start_dt:
        _raise_400(
            f"La reserva coincide con la pausa de comida "
            f"({business.lunch_start.strftime('%H:%M')}–{business.lunch_end.strftime('%H:%M')})."
        )

    return start_utc, end_utc

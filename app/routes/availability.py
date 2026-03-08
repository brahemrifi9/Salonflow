from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import database, models
from app.schemas.bookings import AvailabilityOut, AvailabilitySlot

router = APIRouter(prefix="/api/v1", tags=["availability"])

# Business hours (EVERY DAY)
WORK_START = time(11, 0)      # 11:00
WORK_END = time(21, 30)       # 21:30

# Lunch break (NO BOOKINGS)
BREAK_START = time(15, 0)     # 15:00
BREAK_END = time(16, 0)       # 16:00

SLOT_STEP_MINUTES = 15


def _ceil_to_step(dt: datetime, step_minutes: int) -> datetime:
    """Round up dt to the next step boundary (UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    step = step_minutes * 60
    ts = int(dt.timestamp())
    rounded = ((ts + step - 1) // step) * step
    return datetime.fromtimestamp(rounded, tz=timezone.utc)


@router.get("/availability", response_model=AvailabilityOut)
def get_availability(
    barber_id: int = Query(..., gt=0),
    service_id: int = Query(..., gt=0),
    date_: date = Query(..., alias="date"),
    db: Session = Depends(database.get_db),
):
    barber = db.query(models.Barber).filter(models.Barber.id == barber_id).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Barber not found")

    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    duration = int(service.duration_minutes)
    if duration <= 0:
        raise HTTPException(status_code=400, detail="Service duration must be > 0")

    # Working window (UTC-aware)
    day_start = datetime.combine(date_, WORK_START, tzinfo=timezone.utc)
    day_end = datetime.combine(date_, WORK_END, tzinfo=timezone.utc)

    # Lunch break window (UTC-aware)
    break_start = datetime.combine(date_, BREAK_START, tzinfo=timezone.utc)
    break_end = datetime.combine(date_, BREAK_END, tzinfo=timezone.utc)

    now_utc = datetime.now(timezone.utc)

    # If the whole day is already in the past, return empty
    if day_end <= now_utc:
        return schemas.AvailabilityOut(
            barber_id=barber_id,
            service_id=service_id,
            date=date_,
            slots=[],
        )

    # Clamp start to "now" for today's date, and round up to next slot boundary
    effective_start = day_start
    if date_ == now_utc.date():
        effective_start = max(day_start, now_utc)
        effective_start = _ceil_to_step(effective_start, SLOT_STEP_MINUTES)

    # Fetch existing bookings that overlap the working window (ignore cancelled)
    bookings = (
        db.query(models.Booking)
        .filter(models.Booking.barber_id == barber_id)
        .filter(models.Booking.cancelled_at.is_(None))
        .filter(models.Booking.start_time < day_end)
        .filter(models.Booking.end_time > day_start)
        .order_by(models.Booking.start_time.asc())
        .all()
    )

    busy = [(b.start_time, b.end_time) for b in bookings]

    def overlaps(a_start: datetime, a_end: datetime) -> bool:
        for b_start, b_end in busy:
            if a_start < b_end and a_end > b_start:
                return True
        return False

    slots = []
    step = timedelta(minutes=SLOT_STEP_MINUTES)
    dur = timedelta(minutes=duration)

    t = effective_start
    last_start = day_end - dur

    while t <= last_start:
        t_end = t + dur

        # Skip slots in the past (extra safety)
        if t < now_utc:
            t += step
            continue

        # Skip lunch break overlap (15:00–16:00)
        if t < break_end and t_end > break_start:
            t += step
            continue

        # Skip overlaps with existing bookings
        if not overlaps(t, t_end):
            slots.append(AvailabilitySlot(start_time=t, end_time=t_end))

        t += step

    return AvailabilityOut(
        barber_id=barber_id,
        service_id=service_id,
        date=date_,
        slots=slots,
    )
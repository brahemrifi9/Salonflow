from datetime import datetime, timezone, timedelta, time, date as date_type
from typing import List

from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models

from app.schemas.bookings import (
    BookingCreate,
    BookingResponse,
    BookingOut,
    AvailabilityOut,
    AvailabilitySlot,
)
from app.schemas.public import (
    PublicBookingCreate,
    PublicBookingConfirmation,
    PublicBookingLookup,
    PublicBookingCancelRequest,
)

from app.core.deps import get_current_user, require_admin
from app.domain.booking_rules import validate_and_compute_end_time_utc
from app.utils.booking_ref import generate_booking_ref
from app.core.rate_limit import limiter

router = APIRouter(prefix="/api/v1", tags=["Bookings"])

UTC = ZoneInfo("UTC")


# ----------------------
# Helper: resolve business from query param (used by public endpoints)
# ----------------------
def _get_business_or_404(db: Session, business_id: int) -> models.Business:
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.is_active == True,  # noqa: E712
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found.")
    return business


# ----------------------
# Create Booking (Authenticated user required)
# ----------------------
@router.post(
    "/bookings/",
    status_code=status.HTTP_201_CREATED,
    response_model=BookingResponse,
)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    business_id = current_user.business_id
    business = _get_business_or_404(db, business_id)

    cliente = db.query(models.Cliente).filter(
        models.Cliente.id == booking.cliente_id,
        models.Cliente.business_id == business_id,
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    barber = db.query(models.Barber).filter(
        models.Barber.id == booking.barber_id,
        models.Barber.business_id == business_id,
    ).first()
    if not barber or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barbero no encontrado o inactivo.")

    service = db.query(models.Service).filter(
        models.Service.id == booking.service_id,
        models.Service.business_id == business_id,
    ).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo.")

    start_utc, end_utc = validate_and_compute_end_time_utc(
        booking.start_time,
        service.duration_minutes,
        require_client_utc=True,
        enforce_slot_step=True,
        business=business,
    )

    new_booking = models.Booking(
        booking_ref=generate_booking_ref(),
        cliente_id=booking.cliente_id,
        barber_id=booking.barber_id,
        service_id=booking.service_id,
        start_time=start_utc,
        end_time=end_utc,
        duration_minutes=service.duration_minutes,
        business_id=business_id,
    )

    db.add(new_booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este horario ya no está disponible.")

    db.refresh(new_booking)
    return new_booking


# ----------------------
# Create Booking (PUBLIC) - identified by business_id query param
# POST /api/v1/public/bookings?business_id=1
# ----------------------
@router.post(
    "/public/bookings",
    status_code=status.HTTP_201_CREATED,
    response_model=PublicBookingConfirmation,
)
@limiter.limit("5/minute")
def create_public_booking(
    request: Request,
    booking: PublicBookingCreate,
    business_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, business_id)

    cliente = db.query(models.Cliente).filter(
        models.Cliente.telefono == booking.telefono,
        models.Cliente.business_id == business_id,
    ).first()

    if cliente is None:
        if not booking.nombre or not booking.nombre.strip():
            raise HTTPException(
                status_code=422,
                detail="El campo 'nombre' es obligatorio si el cliente no existe.",
            )
        cliente = models.Cliente(
            nombre=booking.nombre.strip(),
            telefono=booking.telefono.strip(),
            business_id=business_id,
        )
        db.add(cliente)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            cliente = db.query(models.Cliente).filter(
                models.Cliente.telefono == booking.telefono,
                models.Cliente.business_id == business_id,
            ).first()
            if cliente is None:
                raise HTTPException(status_code=409, detail="No se pudo crear el cliente.")
        else:
            db.refresh(cliente)

    barber = db.query(models.Barber).filter(
        models.Barber.id == booking.barber_id,
        models.Barber.business_id == business_id,
    ).first()
    if not barber or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barbero no encontrado o inactivo.")

    service = db.query(models.Service).filter(
        models.Service.id == booking.service_id,
        models.Service.business_id == business_id,
    ).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo.")

    start_utc, end_utc = validate_and_compute_end_time_utc(
        booking.start_time,
        service.duration_minutes,
        require_client_utc=True,
        enforce_slot_step=True,
        business=business,
    )

    new_booking = models.Booking(
        booking_ref=generate_booking_ref(),
        cliente_id=cliente.id,
        barber_id=barber.id,
        service_id=service.id,
        start_time=start_utc,
        end_time=end_utc,
        duration_minutes=service.duration_minutes,
        business_id=business_id,
    )
    db.add(new_booking)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este horario ya no está disponible.")

    db.refresh(new_booking)

    return PublicBookingConfirmation(
        booking_id=new_booking.id,
        booking_ref=new_booking.booking_ref,
        start_time=new_booking.start_time,
        end_time=new_booking.end_time,
        barber={"id": barber.id, "name": barber.name},
        service={
            "id": service.id,
            "name": service.name,
            "duration_minutes": service.duration_minutes,
            "price_cents": service.price_cents,
        },
        cliente_nombre=cliente.nombre,
        cliente_telefono=cliente.telefono,
        message="Reserva confirmada.",
    )


# ----------------------
# Public: Get booking by ref (no business_id needed — booking_ref is globally unique)
# ----------------------
@router.get("/public/bookings/{booking_ref}", response_model=PublicBookingLookup)
@limiter.limit("10/minute")
def get_public_booking(
    request: Request,
    booking_ref: str,
    db: Session = Depends(get_db),
):
    booking = (
        db.query(models.Booking)
        .filter(models.Booking.booking_ref == booking_ref)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")

    barber = booking.barber
    service = booking.service
    cliente = booking.cliente

    status_value = "cancelled" if booking.cancelled_at else "confirmed"
    telefono = cliente.telefono or ""
    masked_telefono = f"{'*' * max(0, len(telefono) - 3)}{telefono[-3:] if telefono else ''}"

    return PublicBookingLookup(
        booking_ref=booking.booking_ref,
        start_time=booking.start_time,
        end_time=booking.end_time,
        cancelled_at=booking.cancelled_at,
        barber={"id": barber.id, "name": barber.name},
        service={
            "id": service.id,
            "name": service.name,
            "duration_minutes": service.duration_minutes,
            "price_cents": service.price_cents,
        },
        cliente_nombre=cliente.nombre,
        cliente_telefono=masked_telefono,
        status=status_value,
    )


# ----------------------
# Public: Cancel booking by ref
# ----------------------
@router.patch("/public/bookings/{booking_ref}/cancel")
@limiter.limit("5/minute")
def cancel_public_booking(
    request: Request,
    booking_ref: str,
    payload: PublicBookingCancelRequest,
    db: Session = Depends(get_db),
):
    booking = (
        db.query(models.Booking)
        .filter(models.Booking.booking_ref == booking_ref)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")

    if booking.cliente.telefono != payload.telefono:
        raise HTTPException(status_code=403, detail="Teléfono incorrecto.")

    if booking.cancelled_at is not None:
        raise HTTPException(status_code=409, detail="La reserva ya está cancelada.")

    booking.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(booking)

    return {
        "booking_ref": booking.booking_ref,
        "status": "cancelled",
        "message": "Reserva cancelada correctamente.",
    }


# ----------------------
# Public Availability — scoped by business_id
# GET /api/v1/public/availability?business_id=1&barber_id=1&service_id=2&date=2026-03-10
# ----------------------
@router.get("/public/availability", response_model=AvailabilityOut)
def get_public_availability(
    business_id: int = Query(..., ge=1),
    barber_id: int = Query(..., ge=1),
    service_id: int = Query(..., ge=1),
    date: date_type = Query(...),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, business_id)

    barber = db.query(models.Barber).filter(
        models.Barber.id == barber_id,
        models.Barber.business_id == business_id,
        models.Barber.is_active == True,  # noqa: E712
    ).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Barbero no encontrado o inactivo.")

    service = db.query(models.Service).filter(
        models.Service.id == service_id,
        models.Service.business_id == business_id,
        models.Service.is_active == True,  # noqa: E712
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo.")

    duration_minutes = service.duration_minutes
    if not duration_minutes:
        raise HTTPException(status_code=500, detail="Servicio sin duración configurada.")

    duration = timedelta(minutes=int(duration_minutes))
    step = timedelta(minutes=15)
    shop_tz = ZoneInfo(business.timezone)

    day_start_local = datetime.combine(date, time(0, 0), tzinfo=shop_tz)
    day_end_local = day_start_local + timedelta(days=1)
    day_start_utc = day_start_local.astimezone(UTC)
    day_end_utc = day_end_local.astimezone(UTC)

    existing = (
        db.query(models.Booking)
        .filter(
            models.Booking.barber_id == barber_id,
            models.Booking.business_id == business_id,
            models.Booking.cancelled_at.is_(None),
            models.Booking.start_time < day_end_utc,
            models.Booking.end_time > day_start_utc,
        )
        .all()
    )

    busy: list[tuple[datetime, datetime]] = []
    for b in existing:
        s = b.start_time if b.start_time.tzinfo else b.start_time.replace(tzinfo=timezone.utc)
        e = b.end_time if b.end_time.tzinfo else b.end_time.replace(tzinfo=timezone.utc)
        busy.append((s.astimezone(UTC), e.astimezone(UTC)))

    barber_blocks = (
        db.query(models.BarberBlock)
        .filter(
            models.BarberBlock.barber_id == barber_id,
            models.BarberBlock.business_id == business_id,
            models.BarberBlock.date == date,
        )
        .all()
    )
    blocks: list[tuple[datetime, datetime]] = [
        (
            datetime.combine(date, blk.start_time, tzinfo=shop_tz).astimezone(UTC),
            datetime.combine(date, blk.end_time, tzinfo=shop_tz).astimezone(UTC),
        )
        for blk in barber_blocks
    ]

    open_local = datetime.combine(date, business.open_time, tzinfo=shop_tz)
    close_local = datetime.combine(date, business.close_time, tzinfo=shop_tz)
    lunch_start = datetime.combine(date, business.lunch_start, tzinfo=shop_tz)
    lunch_end = datetime.combine(date, business.lunch_end, tzinfo=shop_tz)

    last_start = close_local - duration
    if last_start < open_local:
        return AvailabilityOut(barber_id=barber_id, service_id=service_id, date=date, slots=[])

    slots: list[AvailabilitySlot] = []
    t = open_local

    while t <= last_start:
        start_m = t
        end_m = t + duration

        if (start_m < lunch_end) and (end_m > lunch_start):
            t += step
            continue

        start_u = start_m.astimezone(UTC)
        end_u = end_m.astimezone(UTC)

        conflict = (
            any((start_u < be) and (end_u > bs) for (bs, be) in busy)
            or any((start_u < blk_e) and (end_u > blk_s) for (blk_s, blk_e) in blocks)
        )
        if not conflict:
            slots.append(
                AvailabilitySlot(
                    start_time_utc=start_u,
                    end_time_utc=end_u,
                    start_time_madrid=start_m.astimezone(shop_tz),
                    end_time_madrid=end_m.astimezone(shop_tz),
                )
            )

        t += step

    return AvailabilityOut(barber_id=barber_id, service_id=service_id, date=date, slots=slots)


# ----------------------
# List Bookings (ADMIN ONLY) — scoped to admin's business
# ----------------------
@router.get(
    "/bookings/",
    response_model=List[BookingResponse],
)
def list_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    return (
        db.query(models.Booking)
        .filter(models.Booking.business_id == current_user.business_id)
        .order_by(models.Booking.start_time.asc())
        .all()
    )


# ----------------------
# Cancel Booking (ADMIN ONLY) — scoped to admin's business
# ----------------------
@router.patch(
    "/bookings/{booking_id}/cancel",
    response_model=BookingOut,
)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.business_id == current_user.business_id,
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")

    if booking.cancelled_at is not None:
        raise HTTPException(status_code=409, detail="La reserva ya está cancelada.")

    booking.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(booking)
    return booking


# ----------------------
# Admin Dedicated Endpoint — scoped to admin's business
# ----------------------
@router.get("/admin/bookings")
def admin_list_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    return (
        db.query(models.Booking)
        .options(
            joinedload(models.Booking.cliente),
            joinedload(models.Booking.barber),
            joinedload(models.Booking.service),
        )
        .filter(models.Booking.business_id == current_user.business_id)
        .order_by(models.Booking.start_time.asc())
        .all()
    )

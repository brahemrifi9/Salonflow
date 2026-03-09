from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

from app.domain.booking_rules import validate_and_compute_end_time_utc

from app.schemas.public import (
    PublicBarber,
    PublicService,
    PublicBookingCreate,
)

router = APIRouter(prefix="/api/v1/public", tags=["Public"])


@router.get("/barbers", response_model=list[PublicBarber])
def list_active_barbers(db: Session = Depends(get_db)):
    return (
        db.query(models.Barber)
        .filter(models.Barber.is_active == True)
        .all()
    )


@router.get("/services", response_model=list[PublicService])
def list_active_services(db: Session = Depends(get_db)):
    return (
        db.query(models.Service)
        .filter(models.Service.is_active == True)
        .all()
    )


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_public_booking(payload: PublicBookingCreate, db: Session = Depends(get_db)):
    # 1) Validate barber exists + active
    barber = db.query(models.Barber).filter(models.Barber.id == payload.barber_id).first()
    if not barber or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barbero no encontrado o inactivo.")

    # 2) Validate service exists + active
    service = db.query(models.Service).filter(models.Service.id == payload.service_id).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo.")

    # 3) Get-or-create cliente by telefono (WhatsApp-first)
    cliente = (
        db.query(models.Cliente)
        .filter(models.Cliente.telefono == payload.telefono)
        .first()
    )

    if not cliente:
        if not payload.nombre:
            raise HTTPException(status_code=400, detail="Falta el nombre del cliente.")
        cliente = models.Cliente(
            nombre=payload.nombre,
            telefono=payload.telefono,
            email=None,
        )
        db.add(cliente)
        db.flush()  # assigns cliente.id without commit

    # 4) Hard validate business rules + compute end time (UTC stored)
    start_utc, end_utc = validate_and_compute_end_time_utc(
        payload.start_time,
        service.duration_minutes,
        require_client_utc=True,
        enforce_slot_step=True,
    )

    # 5) Create booking (DB overlap protected by EXCLUDE constraint)
    booking = models.Booking(
        cliente_id=cliente.id,
        barber_id=payload.barber_id,
        service_id=payload.service_id,
        start_time=start_utc,
        end_time=end_utc,
        duration_minutes=service.duration_minutes,
    )

    db.add(booking)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este horario ya no está disponible."
        )

    db.refresh(booking)
    return booking
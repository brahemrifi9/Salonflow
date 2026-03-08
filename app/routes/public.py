from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db_errors import raise_http_for_integrity_error
from app import models
from app.database import get_db
from app.domain.booking_rules import validate_and_compute_end_time_utc
from app.schemas.public import PublicBarber, PublicService, PublicBookingCreate


router = APIRouter(prefix="/api/v1/public", tags=["Public"])


# ----------------------
# Public Endpoints: Barbers / Services
# ----------------------
@router.get("/barbers", response_model=List[PublicBarber])
def public_list_barbers(
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False, description="If true, includes inactive barbers (dev/debug only)."),
):
    q = db.query(models.Barber)
    if not include_inactive:
        q = q.filter(models.Barber.is_active == True)  # noqa: E712
    return q.order_by(models.Barber.name.asc()).all()


@router.get("/services", response_model=List[PublicService])
def public_list_services(
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False, description="If true, includes inactive services (dev/debug only)."),
):
    q = db.query(models.Service)
    if not include_inactive:
        q = q.filter(models.Service.is_active == True)  # noqa: E712
    return q.order_by(models.Service.name.asc()).all()


# ----------------------
# Public Endpoint: Create booking via WhatsApp phone
# ----------------------
@router.post("/bookings", status_code=status.HTTP_201_CREATED)
def public_create_booking(payload: PublicBookingCreate, db: Session = Depends(get_db)):
    # 1) Validate barber exists + active
    barber = db.query(models.Barber).filter(models.Barber.id == payload.barber_id).first()
    if not barber or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barbero no encontrado o inactivo.")

    # 2) Validate service exists + active
    service = db.query(models.Service).filter(models.Service.id == payload.service_id).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo.")

    # 3) Normalize telefono
    telefono = payload.telefono.strip().replace(" ", "")
    if not telefono:
        raise HTTPException(status_code=422, detail="Teléfono es obligatorio.")

    # 4) Find or create client by telefono
    cliente = db.query(models.Cliente).filter(models.Cliente.telefono == telefono).first()

    if cliente is None:
        if payload.nombre is None or not payload.nombre.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Nombre es obligatorio para un cliente nuevo.",
            )

        cliente = models.Cliente(
            nombre=payload.nombre.strip(),
            telefono=telefono,
            email=None,
        )
        db.add(cliente)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            # race condition: created by another request
            cliente = db.query(models.Cliente).filter(models.Cliente.telefono == telefono).first()
            if cliente is None:
                raise HTTPException(status_code=409, detail="No se pudo crear el cliente.")
        db.refresh(cliente)

    # 5) Apply business rules + compute end_time
    # validate_and_compute_end_time_utc in your project already enforces:
    # - UTC input
    # - future
    # - slot step
    # - business hours
    # - lunch break
    start_utc, end_utc = validate_and_compute_end_time_utc(
        payload.start_time,
        service.duration_minutes,
        require_client_utc=True,
        enforce_slot_step=True,
    )

    # 6) Create booking (DB overlap constraint -> 409)
    booking = models.Booking(
        cliente_id=cliente.id,
        barber_id=payload.barber_id,
        service_id=payload.service_id,
        start_time=start_utc,
        end_time=end_utc,
    )

    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este horario ya no está disponible.")
    db.refresh(booking)

    return booking
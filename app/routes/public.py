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


def _get_business_or_404(db: Session, business_id: int) -> models.Business:
    business = db.query(models.Business).filter(
        models.Business.id == business_id,
        models.Business.is_active == True,  # noqa: E712
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found.")
    return business


# ----------------------
# Public Endpoints: Barbers / Services
# Require business_id as query param: /api/v1/public/barbers?business_id=1
# ----------------------

@router.get("/barbers", response_model=List[PublicBarber])
def public_list_barbers(
    business_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False),
):
    _get_business_or_404(db, business_id)
    q = db.query(models.Barber).filter(models.Barber.business_id == business_id)
    if not include_inactive:
        q = q.filter(models.Barber.is_active == True)  # noqa: E712
    return q.order_by(models.Barber.name.asc()).all()


@router.get("/services", response_model=List[PublicService])
def public_list_services(
    business_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False),
):
    _get_business_or_404(db, business_id)
    q = db.query(models.Service).filter(models.Service.business_id == business_id)
    if not include_inactive:
        q = q.filter(models.Service.is_active == True)  # noqa: E712
    return q.order_by(models.Service.name.asc()).all()


# ----------------------
# Public Endpoint: Create booking via WhatsApp phone
# ----------------------
@router.post("/bookings", status_code=status.HTTP_201_CREATED)
def public_create_booking(
    payload: PublicBookingCreate,
    business_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    _get_business_or_404(db, business_id)

    barber = db.query(models.Barber).filter(
        models.Barber.id == payload.barber_id,
        models.Barber.business_id == business_id,
    ).first()
    if not barber or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barbero no encontrado o inactivo.")

    service = db.query(models.Service).filter(
        models.Service.id == payload.service_id,
        models.Service.business_id == business_id,
    ).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo.")

    telefono = payload.telefono.strip().replace(" ", "")
    if not telefono:
        raise HTTPException(status_code=422, detail="Teléfono es obligatorio.")

    cliente = db.query(models.Cliente).filter(
        models.Cliente.telefono == telefono,
        models.Cliente.business_id == business_id,
    ).first()

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
            business_id=business_id,
        )
        db.add(cliente)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            cliente = db.query(models.Cliente).filter(
                models.Cliente.telefono == telefono,
                models.Cliente.business_id == business_id,
            ).first()
            if cliente is None:
                raise HTTPException(status_code=409, detail="No se pudo crear el cliente.")
        db.refresh(cliente)

    start_utc, end_utc = validate_and_compute_end_time_utc(
        payload.start_time,
        service.duration_minutes,
        require_client_utc=True,
        enforce_slot_step=True,
    )

    booking = models.Booking(
        cliente_id=cliente.id,
        barber_id=payload.barber_id,
        service_id=payload.service_id,
        start_time=start_utc,
        end_time=end_utc,
        business_id=business_id,
    )

    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este horario ya no está disponible.")
    db.refresh(booking)

    return booking

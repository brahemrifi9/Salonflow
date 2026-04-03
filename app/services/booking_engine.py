from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app import models
from app.domain.booking_rules import validate_and_compute_end_time_utc
from app.utils.booking_ref import generate_booking_ref


def create_booking_from_whatsapp(
    db: Session,
    telefono: str,
    nombre: str,
    barber_id: int,
    service_id: int,
    start_time,
    business_id: int,  # REQUIRED — every WhatsApp booking must be scoped
):
    """
    Reusable booking creation from WhatsApp flow.
    All queries scoped to business_id.
    """

    # 1. Validate barber belongs to this business
    barber = db.query(models.Barber).filter(
        models.Barber.id == barber_id,
        models.Barber.business_id == business_id,
    ).first()
    if not barber or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barbero no encontrado.")

    # 2. Validate service belongs to this business
    service = db.query(models.Service).filter(
        models.Service.id == service_id,
        models.Service.business_id == business_id,
    ).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")

    telefono = telefono.strip().replace(" ", "")

    # 3. Find or create cliente scoped to this business
    cliente = db.query(models.Cliente).filter(
        models.Cliente.telefono == telefono,
        models.Cliente.business_id == business_id,
    ).first()

    if cliente is None:
        cliente = models.Cliente(
            nombre=nombre.strip(),
            telefono=telefono,
            email=None,
            business_id=business_id,
        )
        db.add(cliente)
        try:
            db.commit()
            db.refresh(cliente)
        except IntegrityError:
            db.rollback()
            cliente = db.query(models.Cliente).filter(
                models.Cliente.telefono == telefono,
                models.Cliente.business_id == business_id,
            ).first()
            if cliente is None:
                raise HTTPException(status_code=409, detail="No se pudo crear el cliente.")

    # 4. Apply business rules
    start_utc, end_utc = validate_and_compute_end_time_utc(
        start_time,
        service.duration_minutes,
        require_client_utc=True,
        enforce_slot_step=True,
    )

    # 5. Create booking
    booking = models.Booking(
        booking_ref=generate_booking_ref(),
        cliente_id=cliente.id,
        barber_id=barber_id,
        service_id=service_id,
        start_time=start_utc,
        end_time=end_utc,
        duration_minutes=service.duration_minutes,
        business_id=business_id,
    )

    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese horario ya no está disponible.",
        )

    db.refresh(booking)
    return booking

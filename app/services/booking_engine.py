from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app import models
from app.domain.booking_rules import validate_and_compute_end_time_utc


def create_booking_from_whatsapp(
    db: Session,
    telefono: str,
    nombre: str,
    barber_id: int,
    service_id: int,
    start_time,
):
    """
    Same logic as public booking endpoint but reusable from WhatsApp.
    """

    # 1 Validate barber
    barber = db.query(models.Barber).filter(models.Barber.id == barber_id).first()
    if not barber or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barbero no encontrado.")

    # 2 Validate service
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")

    telefono = telefono.strip().replace(" ", "")

    # 3 Find or create cliente
    cliente = db.query(models.Cliente).filter(models.Cliente.telefono == telefono).first()

    if cliente is None:
        cliente = models.Cliente(
            nombre=nombre.strip(),
            telefono=telefono,
            email=None,
        )

        db.add(cliente)
        db.commit()
        db.refresh(cliente)

    # 4 Apply business rules
    start_utc, end_utc = validate_and_compute_end_time_utc(
        start_time,
        service.duration_minutes,
        require_client_utc=True,
        enforce_slot_step=True,
    )

    # 5 Create booking
    booking = models.Booking(
        cliente_id=cliente.id,
        barber_id=barber_id,
        service_id=service_id,
        start_time=start_utc,
        end_time=end_utc,
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
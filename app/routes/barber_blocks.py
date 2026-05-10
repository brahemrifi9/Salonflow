from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import require_admin
from app import models
from app.schemas.barber_blocks import BarberBlockCreate, BarberBlockOut, ConflictingBookingOut

router = APIRouter(prefix="/api/v1/barbers", tags=["barber-blocks"])


def _get_barber_for_admin(
    barber_id: int,
    current_user: models.User,
    db: Session,
) -> models.Barber:
    barber = (
        db.query(models.Barber)
        .filter(
            models.Barber.id == barber_id,
            models.Barber.business_id == current_user.business_id,
        )
        .first()
    )
    if not barber:
        raise HTTPException(status_code=404, detail="Barber not found")
    return barber


@router.get("/{barber_id}/blocks", response_model=list[BarberBlockOut])
def list_barber_blocks(
    barber_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    _get_barber_for_admin(barber_id, current_user, db)
    return (
        db.query(models.BarberBlock)
        .filter(
            models.BarberBlock.barber_id == barber_id,
            models.BarberBlock.business_id == current_user.business_id,
        )
        .order_by(models.BarberBlock.date.asc(), models.BarberBlock.start_time.asc())
        .all()
    )


@router.post("/{barber_id}/blocks", response_model=BarberBlockOut, status_code=201)
def create_barber_block(
    barber_id: int,
    payload: BarberBlockCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    barber = _get_barber_for_admin(barber_id, current_user, db)
    business = (
        db.query(models.Business)
        .filter(models.Business.id == current_user.business_id)
        .first()
    )

    shop_tz = ZoneInfo(business.timezone)
    block_start_local = datetime.combine(payload.date, payload.start_time, tzinfo=shop_tz)
    block_end_local = datetime.combine(payload.date, payload.end_time, tzinfo=shop_tz)
    block_start_utc = block_start_local.astimezone(ZoneInfo("UTC"))
    block_end_utc = block_end_local.astimezone(ZoneInfo("UTC"))

    conflicting = (
        db.query(models.Booking)
        .filter(
            models.Booking.barber_id == barber_id,
            models.Booking.business_id == current_user.business_id,
            models.Booking.cancelled_at.is_(None),
            models.Booking.start_time < block_end_utc,
            models.Booking.end_time > block_start_utc,
        )
        .all()
    )

    if conflicting:
        conflicts = [
            ConflictingBookingOut(
                id=b.id,
                booking_ref=b.booking_ref,
                start_time=b.start_time,
                end_time=b.end_time,
                cliente_nombre=b.cliente.nombre,
                cliente_telefono=b.cliente.telefono,
            )
            for b in conflicting
        ]
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Cannot create block: conflicting bookings exist",
                "conflicts": [c.model_dump(mode="json") for c in conflicts],
            },
        )

    block = models.BarberBlock(
        business_id=current_user.business_id,
        barber_id=barber_id,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        reason=payload.reason,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@router.delete("/{barber_id}/blocks/{block_id}", status_code=204)
def delete_barber_block(
    barber_id: int,
    block_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    _get_barber_for_admin(barber_id, current_user, db)
    block = (
        db.query(models.BarberBlock)
        .filter(
            models.BarberBlock.id == block_id,
            models.BarberBlock.barber_id == barber_id,
            models.BarberBlock.business_id == current_user.business_id,
        )
        .first()
    )
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    db.delete(block)
    db.commit()

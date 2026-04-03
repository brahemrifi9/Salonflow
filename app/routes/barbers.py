from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import require_admin
from app import models
from app.schemas.barbers import BarberCreate, BarberOut

router = APIRouter(prefix="/api/v1/admin/barbers", tags=["admin-barbers"])


@router.get("", response_model=list[BarberOut])
def list_barbers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    return (
        db.query(models.Barber)
        .filter(models.Barber.business_id == current_user.business_id)
        .order_by(models.Barber.name.asc())
        .all()
    )


@router.post("", response_model=BarberOut)
def create_barber(
    payload: BarberCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    b = models.Barber(
        name=payload.name,
        is_active=True,
        business_id=current_user.business_id,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

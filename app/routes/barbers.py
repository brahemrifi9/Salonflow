from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import require_admin
from app import models
from app.schemas.barbers import BarberCreate, BarberOut

router = APIRouter(prefix="/api/v1/admin/barbers", tags=["admin-barbers"])

@router.get("", response_model=list[BarberOut], dependencies=[Depends(require_admin)])
def list_barbers(db: Session = Depends(get_db)):
    return db.query(models.Barber).order_by(models.Barber.name.asc()).all()

@router.post("", response_model=BarberOut, dependencies=[Depends(require_admin)])
def create_barber(payload: BarberCreate, db: Session = Depends(get_db)):
    b = models.Barber(name=payload.name, is_active=True)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b
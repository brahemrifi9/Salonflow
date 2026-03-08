from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import require_admin
from app import models
from app.schemas.services import ServiceCreate, ServiceOut

router = APIRouter(prefix="/api/v1/admin/services", tags=["admin-services"])

@router.get("", response_model=list[ServiceOut], dependencies=[Depends(require_admin)])
def list_services(db: Session = Depends(get_db)):
    return db.query(models.Service).order_by(models.Service.name.asc()).all()

@router.post("", response_model=ServiceOut, dependencies=[Depends(require_admin)])
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    # simple validation
    if payload.duration_minutes <= 0:
        raise HTTPException(status_code=422, detail="duration_minutes must be > 0")

    s = models.Service(
        name=payload.name,
        duration_minutes=payload.duration_minutes,
        price_cents=payload.price_cents,
        is_active=True,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s
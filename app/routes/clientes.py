from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import database, models
from app.schemas.clientes import ClienteCreate, ClienteOut
from app.core.deps import require_admin

router = APIRouter(prefix="/api/v1", tags=["Clientes"])


@router.post("/clientes/", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def crear_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_admin),
):
    telefono = cliente.telefono.strip().replace(" ", "")
    if not telefono:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Teléfono es obligatorio.",
        )

    nuevo_cliente = models.Cliente(
        nombre=cliente.nombre.strip(),
        telefono=telefono,
        email=cliente.email,
        business_id=current_user.business_id,
    )

    db.add(nuevo_cliente)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un cliente con ese teléfono o email.",
        )

    db.refresh(nuevo_cliente)
    return nuevo_cliente


@router.get("/clientes/", response_model=List[ClienteOut])
def listar_clientes(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_admin),
):
    return (
        db.query(models.Cliente)
        .filter(models.Cliente.business_id == current_user.business_id)
        .all()
    )

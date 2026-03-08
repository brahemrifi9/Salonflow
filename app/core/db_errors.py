from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError


def raise_http_for_integrity_error(e: IntegrityError) -> None:
    """
    Convert common PostgreSQL integrity errors into clean HTTP responses.
    """
    msg = str(e.orig).lower()

    # Unique violations
    if "unique" in msg or "duplicate key value violates unique constraint" in msg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un registro con esos datos.",
        )

    # Not-null violations
    if "not null" in msg or "null value in column" in msg:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Faltan campos obligatorios.",
        )

    # Exclusion constraint overlap (booking conflict)
    if "exclusion constraint" in msg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este horario ya no está disponible.",
        )

    # Fallback
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Datos inválidos.",
    )
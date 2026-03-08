from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PublicBarber(BaseModel):
    id: int
    name: str


class PublicService(BaseModel):
    id: int
    name: str
    duration_minutes: int
    price_cents: int | None


class PublicBookingCreate(BaseModel):
    telefono: str
    nombre: Optional[str] = None
    barber_id: int
    service_id: int
    start_time: datetime


class PublicBookingConfirmation(BaseModel):
    booking_id: int
    booking_ref: str
    start_time: datetime
    end_time: datetime

    barber: PublicBarber
    service: PublicService

    cliente_nombre: Optional[str]
    cliente_telefono: str

    message: str

    model_config = ConfigDict(from_attributes=True)
    
    
class PublicBookingLookup(BaseModel):
    booking_ref: str
    start_time: datetime
    end_time: datetime
    cancelled_at: Optional[datetime] = None

    barber: PublicBarber
    service: PublicService

    cliente_nombre: Optional[str]
    cliente_telefono: str

    status: str

    model_config = ConfigDict(from_attributes=True)


class PublicBookingCancelRequest(BaseModel):
    telefono: str
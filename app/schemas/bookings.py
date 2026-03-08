from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

# Importamos los otros esquemas que usa la reserva
from app.schemas.clientes import ClienteResponse
from app.schemas.barbers import BarberResponse
from app.schemas.services import ServiceResponse

class BookingCreate(BaseModel):
    cliente_id: int
    barber_id: int
    service_id: int
    start_time: datetime

class BookingOut(BaseModel):
    id: int
    cliente_id: int
    barber_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    cancelled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class BookingResponse(BaseModel):
    id: int
    booking_ref: str
    cliente_id: int
    barber_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    cancelled_at: Optional[datetime] = None

    cliente: ClienteResponse
    barber: BarberResponse
    service: ServiceResponse

    model_config = ConfigDict(from_attributes=True)
       
class AvailabilitySlot(BaseModel):
    start_time_utc: datetime
    end_time_utc: datetime

    start_time_madrid: datetime
    end_time_madrid: datetime

class AvailabilityOut(BaseModel):
    barber_id: int
    service_id: int
    date: date
    slots: List[AvailabilitySlot]
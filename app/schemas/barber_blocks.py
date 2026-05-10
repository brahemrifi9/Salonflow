from datetime import date, datetime, time
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator


class BarberBlockCreate(BaseModel):
    date: date
    start_time: time
    end_time: time
    reason: Optional[str] = None

    @model_validator(mode="after")
    def check_times(self) -> "BarberBlockCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ConflictingBookingOut(BaseModel):
    id: int
    booking_ref: str
    start_time: datetime
    end_time: datetime
    cliente_nombre: str
    cliente_telefono: str

    model_config = ConfigDict(from_attributes=True)


class BarberBlockOut(BaseModel):
    id: int
    barber_id: int
    date: date
    start_time: time
    end_time: time
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

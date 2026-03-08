from pydantic import BaseModel, ConfigDict
from typing import Optional

class ServiceCreate(BaseModel):
    name: str
    duration_minutes: int
    price_cents: Optional[int] = None

class ServiceOut(BaseModel):
    id: int
    name: str
    duration_minutes: int
    price_cents: Optional[int]
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class ServiceResponse(BaseModel):
    id: int
    name: str
    duration_minutes: int
    price_cents: Optional[int]
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
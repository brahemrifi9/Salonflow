from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.networks import EmailStr


class ClienteCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    telefono: str = Field(..., min_length=6, max_length=20)  # REQUIRED (WhatsApp-first)
    email: Optional[EmailStr] = None


class ClienteOut(BaseModel):
    id: int
    nombre: str
    telefono: str
    email: Optional[EmailStr] = None
    model_config = ConfigDict(from_attributes=True)


class ClienteResponse(BaseModel):
    id: int
    nombre: str
    telefono: str
    email: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
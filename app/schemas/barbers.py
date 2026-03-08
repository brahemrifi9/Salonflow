from pydantic import BaseModel, ConfigDict

class BarberCreate(BaseModel):
    name: str

class BarberOut(BaseModel):
    id: int
    name: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class BarberResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
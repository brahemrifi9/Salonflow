from pydantic import BaseModel, ConfigDict, Field
from pydantic.networks import EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    # business_id is NOT accepted from the registration payload for security.
    # It is assigned server-side (e.g. by an admin or invite flow).
    # For now, the register endpoint requires the admin to set it directly.


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    business_id: int  # Frontend needs this to scope public API calls

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if v == "supersecret":
            raise ValueError("Insecure SECRET_KEY. Set a strong one in environment variables.")
        return v


settings = Settings()
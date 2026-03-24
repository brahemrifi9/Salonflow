import os

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.rate_limit import limiter
from app.routes import (
    whatsapp,
    auth,
    admin,
    bookings,
    clientes,
    availability,
    public,
    barbers,
    services,
    health,
)
from app import database

# Create app
app = FastAPI(title="SalonFlow MVP")

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ------------------------
# CORS CONFIG
# ------------------------

allowed_origins = os.getenv("CORS_ORIGINS", "")

origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]

# Fallback (optional but useful for safety/debug)
if not origins:
    origins = [
        "http://localhost:5173",
        "https://admin.salonflowapp.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# ROUTERS
# ------------------------

app.include_router(bookings.router)
app.include_router(clientes.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(barbers.router)
app.include_router(services.router)
app.include_router(availability.router)
app.include_router(public.router)
app.include_router(health.router)
app.include_router(whatsapp.router)

# ------------------------
# BASIC ROUTES
# ------------------------

@app.get("/")
def read_root():
    return {"status": "online", "database": "connected"}


@app.get("/check-db")
def check_db(db: Session = Depends(database.get_db)):
    return {"message": "Conexión con la base de datos exitosa!"}
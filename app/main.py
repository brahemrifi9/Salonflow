import os

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi import FastAPI, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

from app.core.rate_limit import limiter
from app.routes import whatsapp
from app.routes import auth, admin, bookings, clientes, availability, public
from app.routes import barbers, services
from app import database
from app.routes import health

app = FastAPI(title="SalonFlow MVP")

# Attach limiter to app state
app.state.limiter = limiter

# Register exception handler for 429
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = os.getenv("CORS_ORIGINS", "")
origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]

# If CORS_ORIGINS is empty, default to no origins (secure).
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
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


@app.get("/")
def read_root():
    return {"status": "online", "database": "connected"}


@app.get("/check-db")
def check_db(db: Session = Depends(database.get_db)):
    return {"message": "Conexión con la base de datos exitosa!"}
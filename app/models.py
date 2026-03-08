import json
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime, Text

from .database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    telefono = Column(String(32), nullable=False, unique=True, index=True)
    email = Column(String, nullable=True)

    bookings = relationship("Booking", back_populates="cliente")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)


class Barber(Base):
    __tablename__ = "barbers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    bookings = relationship("Booking", back_populates="barber")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    bookings = relationship("Booking", back_populates="service")


class Booking(Base):
    __tablename__ = "bookings"

    __table_args__ = (
        UniqueConstraint("cliente_id", "start_time", name="uq_cliente_start"),
    )

    id = Column(Integer, primary_key=True, index=True)
    booking_ref = Column(String(12), unique=True, index=True, nullable=False)

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    barber_id = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    duration_minutes = Column(Integer, default=30, nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    cliente = relationship("Cliente", back_populates="bookings")
    barber = relationship("Barber", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")


class WhatsappSession(Base):
    __tablename__ = "whatsapp_sessions"

    id = Column(Integer, primary_key=True, index=True)
    telefono = Column(String(32), nullable=False, unique=True, index=True)
    state = Column(String(64), nullable=False, default="MENU")
    data_json = Column(Text, nullable=False, default="{}")
    last_message_id = Column(String(128), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def get_data(self) -> dict:
        try:
            return json.loads(self.data_json or "{}")
        except Exception:
            return {}

    def set_data(self, value: dict) -> None:
        self.data_json = json.dumps(value or {}, ensure_ascii=False)
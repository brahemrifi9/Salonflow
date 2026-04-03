import json
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime, Text

from .database import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    country = Column(String(64), nullable=False, default="ES")
    language = Column(String(8), nullable=False, default="es")
    currency = Column(String(8), nullable=False, default="EUR")
    timezone = Column(String(64), nullable=False, default="Europe/Madrid")

    # The Meta WhatsApp phone number ID assigned to this business.
    # Used to route incoming webhooks to the correct business.
    whatsapp_phone_number_id = Column(String(64), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships (optional, useful for admin queries)
    users = relationship("User", back_populates="business")
    barbers = relationship("Barber", back_populates="business")
    services = relationship("Service", back_populates="business")
    clientes = relationship("Cliente", back_populates="business")
    bookings = relationship("Booking", back_populates="business")
    whatsapp_sessions = relationship("WhatsappSession", back_populates="business")


class Cliente(Base):
    __tablename__ = "clientes"

    # REMOVED: unique=True on telefono alone — two businesses can share a phone number
    # ADDED: composite unique (business_id, telefono) via __table_args__
    __table_args__ = (
        UniqueConstraint("business_id", "telefono", name="uq_clientes_business_telefono"),
    )

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    nombre = Column(String, nullable=False)
    telefono = Column(String(32), nullable=False, index=True)  # no longer globally unique
    email = Column(String, nullable=True)

    business = relationship("Business", back_populates="clientes")
    bookings = relationship("Booking", back_populates="cliente")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    business = relationship("Business", back_populates="users")


class Barber(Base):
    __tablename__ = "barbers"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    business = relationship("Business", back_populates="barbers")
    bookings = relationship("Booking", back_populates="barber")


class Service(Base):
    __tablename__ = "services"

    # REMOVED: unique=True on name alone
    # ADDED: composite unique (business_id, name)
    __table_args__ = (
        UniqueConstraint("business_id", "name", name="uq_services_business_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String, nullable=False)  # no longer globally unique
    duration_minutes = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    business = relationship("Business", back_populates="services")
    bookings = relationship("Booking", back_populates="service")


class Booking(Base):
    __tablename__ = "bookings"

    __table_args__ = (
        UniqueConstraint("cliente_id", "start_time", name="uq_cliente_start"),
    )

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    booking_ref = Column(String(12), unique=True, index=True, nullable=False)

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    barber_id = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    duration_minutes = Column(Integer, default=30, nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    business = relationship("Business", back_populates="bookings")
    cliente = relationship("Cliente", back_populates="bookings")
    barber = relationship("Barber", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")


class WhatsappSession(Base):
    __tablename__ = "whatsapp_sessions"

    # REMOVED: unique=True on telefono alone
    # ADDED: composite unique (business_id, telefono)
    __table_args__ = (
        UniqueConstraint("business_id", "telefono", name="uq_whatsapp_sessions_business_telefono"),
    )

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    telefono = Column(String(32), nullable=False, index=True)  # no longer globally unique
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

    business = relationship("Business", back_populates="whatsapp_sessions")

    def get_data(self) -> dict:
        try:
            return json.loads(self.data_json or "{}")
        except Exception:
            return {}

    def set_data(self, value: dict) -> None:
        self.data_json = json.dumps(value or {}, ensure_ascii=False)

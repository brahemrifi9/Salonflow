"""
WhatsApp flow — multi-tenant aware.

Business resolution strategy:
  Each incoming webhook message contains the receiving WhatsApp phone number ID
  (value["metadata"]["phone_number_id"]). We look up which Business has that
  phone_number_id and route all queries to that business.

  If no business matches, we silently ignore the message (it's not ours).

  Each Business row has: whatsapp_phone_number_id = Column(String(64))
  Set this in the DB for each business from the Meta dashboard.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.domain.booking_rules import validate_and_compute_end_time_utc
from app.utils.booking_ref import generate_booking_ref
from app.services.meta_whatsapp import (
    send_text_message,
    send_whatsapp_buttons,
    send_whatsapp_list,
)

MADRID_TZ = ZoneInfo("Europe/Madrid")

MENU_TEXT = (
    "Bienvenido a SalonFlow 💈\n\n"
    "Responde con un número:\n"
    "1. Reservar\n"
    "2. Ver reserva\n"
    "3. Cancelar"
)


# ─────────────────────────────────────────────
# Business resolution
# ─────────────────────────────────────────────

def resolve_business_from_webhook(db: Session, payload: dict) -> models.Business | None:
    """
    Extracts the receiving WhatsApp phone_number_id from the webhook payload
    and looks up the matching Business.

    Returns None if no business matches (webhook not for us, or misconfigured).
    """
    try:
        phone_number_id = (
            payload["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
        )
    except (KeyError, IndexError):
        return None

    if not phone_number_id:
        return None

    return db.query(models.Business).filter(
        models.Business.whatsapp_phone_number_id == phone_number_id,
        models.Business.is_active == True,  # noqa: E712
    ).first()


# ─────────────────────────────────────────────
# Session management — scoped by business_id
# ─────────────────────────────────────────────

def get_or_create_session(
    db: Session,
    telefono: str,
    business_id: int,
) -> models.WhatsappSession:
    session = (
        db.query(models.WhatsappSession)
        .filter(
            models.WhatsappSession.telefono == telefono,
            models.WhatsappSession.business_id == business_id,
        )
        .first()
    )
    if session:
        return session

    session = models.WhatsappSession(
        telefono=telefono,
        state="MENU",
        data_json="{}",
        is_active=True,
        business_id=business_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# ─────────────────────────────────────────────
# Message extraction (unchanged)
# ─────────────────────────────────────────────

def extract_text_message(payload: dict) -> tuple[str | None, str | None, str | None]:
    """Returns: (telefono, text_body, message_id)"""
    try:
        entry = payload["entry"][0]
    except (KeyError, IndexError):
        return None, None, None

    change = entry["changes"][0]
    value = change["value"]
    messages = value.get("messages", [])
    if not messages:
        return None, None, None

    msg = messages[0]
    telefono = msg.get("from")
    message_id = msg.get("id")
    msg_type = msg.get("type")

    if msg_type == "text":
        body = msg["text"]["body"].strip()
        return telefono, body, message_id

    if msg_type == "interactive":
        interactive = msg.get("interactive", {})
        interactive_type = interactive.get("type")
        if interactive_type == "button_reply":
            return telefono, interactive["button_reply"]["id"], message_id
        if interactive_type == "list_reply":
            return telefono, interactive["list_reply"]["id"], message_id

    return telefono, None, message_id


def reset_to_menu(session: models.WhatsappSession) -> None:
    session.state = "MENU"
    session.set_data({})


def normalize_phone(telefono: str) -> str:
    return telefono.strip().replace(" ", "")


def parse_madrid_datetime_to_utc(date_str: str, time_str: str) -> datetime:
    try:
        local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fecha u hora inválida.",
        )
    madrid_dt = local_dt.replace(tzinfo=MADRID_TZ)
    return madrid_dt.astimezone(timezone.utc)


# ─────────────────────────────────────────────
# Data fetchers — all scoped by business_id
# ─────────────────────────────────────────────

def get_active_services(db: Session, business_id: int) -> list[models.Service]:
    return (
        db.query(models.Service)
        .filter(
            models.Service.business_id == business_id,
            models.Service.is_active == True,  # noqa: E712
        )
        .order_by(models.Service.id.asc())
        .all()
    )


def get_active_barbers(db: Session, business_id: int) -> list[models.Barber]:
    return (
        db.query(models.Barber)
        .filter(
            models.Barber.business_id == business_id,
            models.Barber.is_active == True,  # noqa: E712
        )
        .order_by(models.Barber.id.asc())
        .all()
    )


def get_active_bookings_for_phone(
    db: Session,
    telefono: str,
    business_id: int,
    limit: int = 10,
) -> list[models.Booking]:
    telefono = normalize_phone(telefono)
    return (
        db.query(models.Booking)
        .join(models.Cliente)
        .filter(
            models.Cliente.telefono == telefono,
            models.Cliente.business_id == business_id,
            models.Booking.business_id == business_id,
            models.Booking.cancelled_at.is_(None),
            models.Booking.start_time > datetime.now(timezone.utc),
        )
        .order_by(models.Booking.start_time.asc())
        .limit(limit)
        .all()
    )


# ─────────────────────────────────────────────
# Menu / UI builders (unchanged logic, pass business_id through)
# ─────────────────────────────────────────────

def build_services_list(services: list[models.Service]) -> list[dict]:
    items = []
    for service in services:
        description = f"{service.duration_minutes} min"
        if service.price_cents is not None:
            description += f" · €{service.price_cents / 100:.2f}"
        items.append({
            "id": f"SERVICE_{service.id}",
            "title": service.name[:24],
            "description": description[:72],
        })
    return items


def build_barbers_menu(barbers: list[models.Barber]) -> tuple[str, dict]:
    option_map = {}
    lines = ["Elige barbero:"]
    for idx, barber in enumerate(barbers, start=1):
        option_map[str(idx)] = barber.id
        lines.append(f"{idx}. {barber.name}")
    lines.append("")
    lines.append("Responde con el número del barbero.")
    return "\n".join(lines), option_map


def format_booking_row_title(booking: models.Booking) -> str:
    start_madrid = booking.start_time.astimezone(MADRID_TZ)
    return f"{booking.service.name} · {start_madrid.strftime('%d/%m %H:%M')}"[:24]


SPANISH_DAYS = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo",
}


def format_booking_row_description(booking: models.Booking) -> str:
    start_madrid = booking.start_time.astimezone(MADRID_TZ)
    day = SPANISH_DAYS[start_madrid.weekday()]
    t = start_madrid.strftime("%H:%M")
    return f"{booking.barber.name} · {day} {t}"[:72]


def build_bookings_list_items(bookings: list[models.Booking], prefix: str) -> list[dict]:
    return [
        {
            "id": f"{prefix}_{booking.id}",
            "title": format_booking_row_title(booking),
            "description": format_booking_row_description(booking),
        }
        for booking in bookings
    ]


def format_booking_details(booking: models.Booking) -> str:
    start_madrid = booking.start_time.astimezone(MADRID_TZ)
    end_madrid = booking.end_time.astimezone(MADRID_TZ)
    status_text = "cancelada" if booking.cancelled_at else "confirmada"
    return (
        f"Reserva {booking.booking_ref}\n"
        f"Estado: {status_text}\n"
        f"Cliente: {booking.cliente.nombre}\n"
        f"Teléfono: {booking.cliente.telefono}\n"
        f"Barbero: {booking.barber.name}\n"
        f"Servicio: {booking.service.name}\n"
        f"Fecha: {start_madrid.strftime('%Y-%m-%d')}\n"
        f"Hora: {start_madrid.strftime('%H:%M')} - {end_madrid.strftime('%H:%M')} (Madrid)\n\n"
        "Escribe menú para volver."
    )


def format_human_booking_datetime(dt: datetime) -> str:
    madrid_dt = dt.astimezone(MADRID_TZ)
    now_madrid = datetime.now(MADRID_TZ).date()
    target_date = madrid_dt.date()
    if target_date == now_madrid:
        day_label = "Hoy"
    elif target_date == now_madrid.fromordinal(now_madrid.toordinal() + 1):
        day_label = "Mañana"
    else:
        day_label = madrid_dt.strftime("%d/%m/%Y")
    return f"{day_label} a las {madrid_dt.strftime('%H:%M')}"


# ─────────────────────────────────────────────
# Booking creation from session data — scoped
# ─────────────────────────────────────────────

def create_booking_from_session_data(
    db: Session,
    session: models.WhatsappSession,
) -> models.Booking:
    data = session.get_data()
    business_id = session.business_id  # already set on session

    telefono = normalize_phone(session.telefono)
    nombre = (data.get("nombre") or "").strip()
    barber_id = data.get("barber_id")
    service_id = data.get("service_id")
    date_str = data.get("date")
    time_str = data.get("time")

    if not nombre:
        raise HTTPException(status_code=422, detail="Nombre obligatorio.")
    if not barber_id or not service_id or not date_str or not time_str:
        raise HTTPException(status_code=422, detail="Faltan datos de la reserva.")

    barber = db.query(models.Barber).filter(
        models.Barber.id == barber_id,
        models.Barber.business_id == business_id,
    ).first()
    if not barber or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barbero no encontrado o inactivo.")

    service = db.query(models.Service).filter(
        models.Service.id == service_id,
        models.Service.business_id == business_id,
    ).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo.")

    cliente = db.query(models.Cliente).filter(
        models.Cliente.telefono == telefono,
        models.Cliente.business_id == business_id,
    ).first()

    if cliente is None:
        cliente = models.Cliente(
            nombre=nombre,
            telefono=telefono,
            email=None,
            business_id=business_id,
        )
        db.add(cliente)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            cliente = db.query(models.Cliente).filter(
                models.Cliente.telefono == telefono,
                models.Cliente.business_id == business_id,
            ).first()
            if cliente is None:
                raise HTTPException(status_code=409, detail="No se pudo crear el cliente.")
        db.refresh(cliente)
    elif not cliente.nombre and nombre:
        cliente.nombre = nombre
        db.commit()
        db.refresh(cliente)

    requested_start_utc = parse_madrid_datetime_to_utc(date_str, time_str)

    start_utc, end_utc = validate_and_compute_end_time_utc(
        requested_start_utc,
        service.duration_minutes,
        require_client_utc=True,
        enforce_slot_step=True,
    )

    booking = models.Booking(
        booking_ref=generate_booking_ref(),
        cliente_id=cliente.id,
        barber_id=barber.id,
        service_id=service.id,
        start_time=start_utc,
        end_time=end_utc,
        duration_minutes=service.duration_minutes,
        business_id=business_id,
    )

    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este horario ya no está disponible.")

    db.refresh(booking)
    return booking


# ─────────────────────────────────────────────
# Flow processors — all receive business_id via session
# ─────────────────────────────────────────────

def process_menu_selection(db: Session, session: models.WhatsappSession, incoming_text: str) -> str:
    text = incoming_text.strip().lower()
    business_id = session.business_id

    if text in ["hola", "menu", "menú", "start", "hi", "hello"]:
        reset_to_menu(session)
        return MENU_TEXT

    if text in ["1", "book"]:
        services = get_active_services(db, business_id)
        if not services:
            reset_to_menu(session)
            return "No hay servicios disponibles ahora mismo."
        session.state = "BOOKING_SERVICE"
        session.set_data({})
        return "__SEND_SERVICE_LIST__"

    if text in ["2", "view"]:
        bookings = get_active_bookings_for_phone(db, session.telefono, business_id)
        if not bookings:
            reset_to_menu(session)
            return "No tienes reservas activas en este número."
        session.state = "LOOKUP_SELECT"
        session.set_data({})
        return "__SEND_VIEW_BOOKINGS_LIST__"

    if text in ["3", "cancel"]:
        bookings = get_active_bookings_for_phone(db, session.telefono, business_id)
        if not bookings:
            reset_to_menu(session)
            return "No tienes reservas activas para cancelar."
        session.state = "CANCEL_SELECT"
        session.set_data({})
        return "__SEND_CANCEL_BOOKINGS_LIST__"

    return MENU_TEXT


def process_lookup_select_flow(db: Session, session: models.WhatsappSession, incoming_text: str) -> str:
    text = incoming_text.strip()
    business_id = session.business_id

    booking_id = None
    if text.startswith("VIEWBOOKING_"):
        raw_id = text.replace("VIEWBOOKING_", "", 1)
        if raw_id.isdigit():
            booking_id = int(raw_id)

    if not booking_id:
        return "Selección no válida. Abre la lista y elige una reserva."

    telefono = normalize_phone(session.telefono)

    booking = (
        db.query(models.Booking)
        .join(models.Cliente)
        .filter(
            models.Booking.id == booking_id,
            models.Booking.business_id == business_id,
            models.Cliente.telefono == telefono,
        )
        .first()
    )

    if not booking:
        reset_to_menu(session)
        return "No he encontrado esa reserva en este número."

    reset_to_menu(session)
    return format_booking_details(booking)


def process_cancel_select_flow(db: Session, session: models.WhatsappSession, incoming_text: str) -> str:
    data = session.get_data()
    text = incoming_text.strip()
    business_id = session.business_id

    if session.state == "CANCEL_SELECT":
        booking_id = None
        if text.startswith("CANCELBOOKING_"):
            raw_id = text.replace("CANCELBOOKING_", "", 1)
            if raw_id.isdigit():
                booking_id = int(raw_id)

        if not booking_id:
            return "Selección no válida. Abre la lista y elige una reserva."

        telefono = normalize_phone(session.telefono)
        booking = (
            db.query(models.Booking)
            .join(models.Cliente)
            .filter(
                models.Booking.id == booking_id,
                models.Booking.business_id == business_id,
                models.Cliente.telefono == telefono,
                models.Booking.cancelled_at.is_(None),
            )
            .first()
        )

        if not booking:
            reset_to_menu(session)
            return "No he encontrado esa reserva activa en este número."

        data["cancel_booking_id"] = booking.id
        session.set_data(data)
        session.state = "CANCEL_CONFIRM"

        start_text = format_human_booking_datetime(booking.start_time)
        return (
            "¿Seguro que quieres cancelar esta reserva?\n\n"
            f"{booking.service.name}\n"
            f"{booking.barber.name}\n"
            f"{start_text}\n\n"
            "Responde SI para confirmar o NO para volver."
        )

    if session.state == "CANCEL_CONFIRM":
        lowered = text.lower()

        if lowered == "no":
            reset_to_menu(session)
            return "Cancelación abortada. Escribe menú para volver."

        if lowered != "si":
            return "Responde SI para confirmar o NO para volver."

        booking_id = data.get("cancel_booking_id")
        telefono = normalize_phone(session.telefono)

        booking = (
            db.query(models.Booking)
            .join(models.Cliente)
            .filter(
                models.Booking.id == booking_id,
                models.Booking.business_id == business_id,
                models.Cliente.telefono == telefono,
            )
            .first()
        )

        if not booking:
            reset_to_menu(session)
            return "No he encontrado esa reserva."

        if booking.cancelled_at is not None:
            reset_to_menu(session)
            return "Esa reserva ya estaba cancelada."

        booking.cancelled_at = datetime.now(timezone.utc)
        db.commit()
        reset_to_menu(session)
        return "Reserva cancelada correctamente."

    reset_to_menu(session)
    return MENU_TEXT


def process_booking_flow(db: Session, session: models.WhatsappSession, incoming_text: str) -> str:
    data = session.get_data()
    text = incoming_text.strip()
    business_id = session.business_id

    if session.state == "BOOKING_SERVICE":
        service_id = None
        if text.startswith("SERVICE_"):
            raw_id = text.replace("SERVICE_", "", 1)
            if raw_id.isdigit():
                service_id = int(raw_id)
        elif text.isdigit():
            service_id = int(text)

        if not service_id:
            return "Servicio no válido. Abre la lista y elige un servicio."

        service = db.query(models.Service).filter(
            models.Service.id == service_id,
            models.Service.business_id == business_id,
        ).first()
        if not service or not service.is_active:
            return "Servicio no disponible ahora mismo."

        active_barbers = get_active_barbers(db, business_id)
        if not active_barbers:
            reset_to_menu(session)
            return "No hay barberos disponibles ahora mismo."

        barbers_message, barber_options = build_barbers_menu(active_barbers)
        data["service_id"] = service.id
        data["service_name"] = service.name
        data["barber_options"] = barber_options
        session.set_data(data)
        session.state = "BOOKING_BARBER"
        return barbers_message

    if session.state == "BOOKING_BARBER":
        barber_options = data.get("barber_options", {})
        barber_id = barber_options.get(text)
        if not barber_id:
            return "Barbero no válido. Responde con uno de los números mostrados."

        barber = db.query(models.Barber).filter(
            models.Barber.id == barber_id,
            models.Barber.business_id == business_id,
        ).first()
        if not barber or not barber.is_active:
            return "Barbero no encontrado o inactivo."

        data["barber_id"] = barber.id
        data["barber_name"] = barber.name
        session.set_data(data)
        session.state = "BOOKING_DATE"
        return "Escribe la fecha en formato YYYY-MM-DD. Ejemplo: 2026-03-12"

    if session.state == "BOOKING_DATE":
        try:
            datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return "Fecha inválida. Usa formato YYYY-MM-DD. Ejemplo: 2026-03-12"
        data["date"] = text
        session.set_data(data)
        session.state = "BOOKING_SLOT"
        return "Escribe la hora en formato HH:MM en horario de Madrid.\nEjemplo: 12:30"

    if session.state == "BOOKING_SLOT":
        try:
            datetime.strptime(text, "%H:%M")
        except ValueError:
            return "Hora inválida. Usa formato HH:MM. Ejemplo: 12:30"
        data["time"] = text
        session.set_data(data)
        session.state = "BOOKING_NAME"
        return "Escribe tu nombre para la reserva."

    if session.state == "BOOKING_NAME":
        nombre = text.strip()
        if not nombre:
            return "Nombre no válido. Escribe tu nombre para la reserva."
        data["nombre"] = nombre
        session.set_data(data)
        session.state = "BOOKING_CONFIRM"
        return (
            "Confirma tu reserva:\n"
            f"Servicio: {data.get('service_name')}\n"
            f"Barbero: {data.get('barber_name')}\n"
            f"Fecha: {data.get('date')}\n"
            f"Hora: {data.get('time')} (Madrid)\n"
            f"Nombre: {data.get('nombre')}\n"
            f"Teléfono: {normalize_phone(session.telefono)}\n\n"
            "Responde SI para confirmar o NO para cancelar."
        )

    if session.state == "BOOKING_CONFIRM":
        lowered = text.lower()
        if lowered == "no":
            reset_to_menu(session)
            return "Reserva cancelada. Escribe menú para volver."
        if lowered != "si":
            return "Responde SI para confirmar o NO para cancelar."

        try:
            booking = create_booking_from_session_data(db, session)
        except HTTPException as exc:
            reset_to_menu(session)
            return f"No se pudo crear la reserva: {exc.detail}"
        except Exception:
            reset_to_menu(session)
            return "No se pudo crear la reserva por un error inesperado."

        start_madrid = booking.start_time.astimezone(MADRID_TZ)
        reset_to_menu(session)
        return (
            "✅ Reserva confirmada\n\n"
            f"Código: {booking.booking_ref}\n"
            f"Fecha: {start_madrid.strftime('%Y-%m-%d')}\n"
            f"Hora: {start_madrid.strftime('%H:%M')} (Madrid)\n"
            f"Barbero: {booking.barber.name}\n"
            f"Servicio: {booking.service.name}\n\n"
            "Guarda este código para consultar o cancelar tu cita."
        )

    reset_to_menu(session)
    return MENU_TEXT


# ─────────────────────────────────────────────
# Main entry point — called from routes/whatsapp.py
# ─────────────────────────────────────────────

def process_incoming_whatsapp_event(db: Session, payload: dict) -> None:
    # 1. Resolve which business this webhook is for
    business = resolve_business_from_webhook(db, payload)
    if business is None:
        # Not configured or not our webhook — ignore silently
        return

    telefono, body, message_id = extract_text_message(payload)
    if not telefono:
        return

    # 2. Get or create session scoped to this business
    session = get_or_create_session(db, telefono, business.id)

    # 3. Deduplicate repeated webhook deliveries
    if message_id and session.last_message_id == message_id:
        return

    session.last_message_id = message_id

    # 4. Route message to correct flow
    if not body:
        reply = "Por ahora solo entiendo mensajes de texto. Escribe menú."
    else:
        text = body.strip()
        if text.lower() in ["menu", "menú", "hola", "start"]:
            reset_to_menu(session)
            reply = MENU_TEXT
        elif session.state == "MENU":
            reply = process_menu_selection(db, session, text)
        elif session.state == "LOOKUP_SELECT":
            reply = process_lookup_select_flow(db, session, text)
        elif session.state in ["CANCEL_SELECT", "CANCEL_CONFIRM"]:
            reply = process_cancel_select_flow(db, session, text)
        elif session.state.startswith("BOOKING_"):
            reply = process_booking_flow(db, session, text)
        else:
            reset_to_menu(session)
            reply = MENU_TEXT

    db.add(session)
    db.commit()

    # 5. Send response
    if reply == MENU_TEXT:
        send_whatsapp_buttons(
            telefono,
            "Bienvenido a SalonFlow 💈\n¿Qué deseas hacer?",
            [
                {"id": "BOOK", "title": "Reservar"},
                {"id": "VIEW", "title": "Ver"},
                {"id": "CANCEL", "title": "Cancelar"},
            ],
        )
    elif reply == "__SEND_SERVICE_LIST__":
        services = get_active_services(db, business.id)
        items = build_services_list(services)
        send_whatsapp_list(
            telefono, "SalonFlow 💈", "Selecciona un servicio", "Ver servicios", items,
        )
    elif reply == "__SEND_VIEW_BOOKINGS_LIST__":
        bookings = get_active_bookings_for_phone(db, telefono, business.id)
        items = build_bookings_list_items(bookings, "VIEWBOOKING")
        send_whatsapp_list(
            telefono, "Tus reservas 💈", "Selecciona una reserva para ver los detalles", "Ver reservas", items,
        )
    elif reply == "__SEND_CANCEL_BOOKINGS_LIST__":
        bookings = get_active_bookings_for_phone(db, telefono, business.id)
        items = build_bookings_list_items(bookings, "CANCELBOOKING")
        send_whatsapp_list(
            telefono, "Cancelar reserva 💈", "Selecciona la reserva que quieres cancelar", "Ver reservas", items,
        )
    else:
        send_text_message(telefono, reply)

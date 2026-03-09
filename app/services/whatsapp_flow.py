from datetime import datetime, timezone
from pyexpat.errors import messages
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.domain.booking_rules import validate_and_compute_end_time_utc
from app.services.meta_whatsapp import send_text_message
from app.utils.booking_ref import generate_booking_ref
from app.services.meta_whatsapp import send_whatsapp_buttons


MADRID_TZ = ZoneInfo("Europe/Madrid")

MENU_TEXT = (
    "Bienvenido a SalonFlow 💈\n\n"
    "Responde con un número:\n"
    "1. Reservar\n"
    "2. Ver reserva\n"
    "3. Cancelar"
)


def get_or_create_session(db: Session, telefono: str) -> models.WhatsappSession:
    session = (
        db.query(models.WhatsappSession)
        .filter(models.WhatsappSession.telefono == telefono)
        .first()
    )
    if session:
        return session

    session = models.WhatsappSession(
        telefono=telefono,
        state="MENU",
        data_json="{}",
        is_active=True,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def extract_text_message(payload: dict) -> tuple[str | None, str | None, str | None]:
    """
    Returns: (telefono, text_body, message_id)
    """
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

    # Handle normal text messages
    if msg_type == "text":
        body = msg["text"]["body"].strip()
        return telefono, body, message_id

    # Handle interactive messages (buttons / lists)
    if msg_type == "interactive":
        interactive = msg.get("interactive", {})
        interactive_type = interactive.get("type")

        # Button replies
        if interactive_type == "button_reply":
            body = interactive["button_reply"]["id"]
            return telefono, body, message_id

        # List replies
        if interactive_type == "list_reply":
            body = interactive["list_reply"]["id"]
            return telefono, body, message_id

    # Fallback
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


def get_active_services(db: Session) -> list[models.Service]:
    return (
        db.query(models.Service)
        .filter(models.Service.is_active == True)  # noqa: E712
        .order_by(models.Service.id.asc())
        .all()
    )


def get_active_barbers(db: Session) -> list[models.Barber]:
    return (
        db.query(models.Barber)
        .filter(models.Barber.is_active == True)  # noqa: E712
        .order_by(models.Barber.id.asc())
        .all()
    )


def build_services_menu(services: list[models.Service]) -> tuple[str, dict]:
    option_map = {}
    lines = ["Reserva de cita ✂️", "", "Elige servicio:"]

    for idx, service in enumerate(services, start=1):
        option_map[str(idx)] = service.id
        price_text = ""
        if service.price_cents is not None:
            price_text = f" - €{service.price_cents / 100:.2f}"
        lines.append(
            f"{idx}. {service.name} ({service.duration_minutes} min{price_text})"
        )

    lines.append("")
    lines.append("Responde con el número del servicio.")
    return "\n".join(lines), option_map


def build_barbers_menu(barbers: list[models.Barber]) -> tuple[str, dict]:
    option_map = {}
    lines = ["Elige barbero:"]

    for idx, barber in enumerate(barbers, start=1):
        option_map[str(idx)] = barber.id
        lines.append(f"{idx}. {barber.name}")

    lines.append("")
    lines.append("Responde con el número del barbero.")
    return "\n".join(lines), option_map


def create_booking_from_session_data(
    db: Session,
    session: models.WhatsappSession,
) -> models.Booking:
    data = session.get_data()

    telefono = normalize_phone(session.telefono)
    nombre = (data.get("nombre") or "").strip()
    barber_id = data.get("barber_id")
    service_id = data.get("service_id")
    date_str = data.get("date")
    time_str = data.get("time")

    if not nombre:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nombre obligatorio.",
        )

    if not barber_id or not service_id or not date_str or not time_str:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Faltan datos de la reserva.",
        )

    barber = db.query(models.Barber).filter(models.Barber.id == barber_id).first()
    if not barber or not barber.is_active:
        raise HTTPException(status_code=404, detail="Barbero no encontrado o inactivo.")

    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo.")

    cliente = db.query(models.Cliente).filter(models.Cliente.telefono == telefono).first()
    if cliente is None:
        cliente = models.Cliente(
            nombre=nombre,
            telefono=telefono,
            email=None,
        )
        db.add(cliente)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            cliente = (
                db.query(models.Cliente)
                .filter(models.Cliente.telefono == telefono)
                .first()
            )
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
    )

    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Este horario ya no está disponible.",
        )

    db.refresh(booking)
    return booking


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


def process_menu_selection(db: Session, session: models.WhatsappSession, incoming_text: str) -> str:
    text = incoming_text.strip().lower()

    if text in ["hola", "menu", "menú", "start", "hi", "hello"]:
        reset_to_menu(session)
        return MENU_TEXT

    if text in ["1", "book"]:
        services = get_active_services(db)
        if not services:
            reset_to_menu(session)
            return "No hay servicios disponibles ahora mismo."

        message, option_map = build_services_menu(services)
        session.state = "BOOKING_SERVICE"
        session.set_data({"service_options": option_map})
        return message

    if text in ["2", "view"]:
        session.state = "LOOKUP_REF"
        session.set_data({})
        return "Escribe tu código de reserva. Ejemplo: SF-ABCDE"

    if text in ["3", "cancel"]:
        session.state = "CANCEL_REF"
        session.set_data({})
        return "Escribe tu código de reserva para cancelarla. Ejemplo: SF-ABCDE"

    return MENU_TEXT


def process_lookup_flow(db: Session, session: models.WhatsappSession, incoming_text: str) -> str:
    booking_ref = incoming_text.strip().upper()
    telefono = normalize_phone(session.telefono)

    booking = (
        db.query(models.Booking)
        .join(models.Cliente)
        .filter(
            models.Booking.booking_ref == booking_ref,
            models.Cliente.telefono == telefono,
        )
        .first()
    )

    if not booking:
        return (
            "No he encontrado una reserva con ese código asociada a este número de WhatsApp.\n"
            "Revisa el código o escribe menú."
        )

    return format_booking_details(booking)


def process_cancel_flow(db: Session, session: models.WhatsappSession, incoming_text: str) -> str:
    booking_ref = incoming_text.strip().upper()
    telefono = normalize_phone(session.telefono)

    booking = (
        db.query(models.Booking)
        .join(models.Cliente)
        .filter(
            models.Booking.booking_ref == booking_ref,
            models.Cliente.telefono == telefono,
        )
        .first()
    )

    if not booking:
        return (
            "No he encontrado una reserva con ese código asociada a este número de WhatsApp.\n"
            "Revisa el código o escribe menú."
        )

    if booking.cancelled_at is not None:
        reset_to_menu(session)
        return "Esa reserva ya estaba cancelada."

    booking.cancelled_at = datetime.now(timezone.utc)
    db.commit()

    reset_to_menu(session)
    return f"Reserva {booking.booking_ref} cancelada correctamente."

def process_booking_flow(db: Session, session: models.WhatsappSession, incoming_text: str) -> str:
    data = session.get_data()
    text = incoming_text.strip()

    if session.state == "BOOKING_SERVICE":
        service_options = data.get("service_options", {})
        service_id = service_options.get(text)

        if not service_id:
            return "Servicio no válido. Responde con uno de los números mostrados."

        service = db.query(models.Service).filter(models.Service.id == service_id).first()
        if not service or not service.is_active:
            return "Servicio no disponible ahora mismo."

        active_barbers = get_active_barbers(db)
        if not active_barbers:
            reset_to_menu(session)
            return "No hay barberos disponibles ahora mismo."

        barbers_message, barber_options = build_barbers_menu(active_barbers)

        data["service_id"] = service.id
        data["service_name"] = service.name
        data["service_options"] = service_options
        data["barber_options"] = barber_options
        session.set_data(data)
        session.state = "BOOKING_BARBER"
        return barbers_message

    if session.state == "BOOKING_BARBER":
        barber_options = data.get("barber_options", {})
        barber_id = barber_options.get(text)

        if not barber_id:
            return "Barbero no válido. Responde con uno de los números mostrados."

        barber = db.query(models.Barber).filter(models.Barber.id == barber_id).first()
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
        return (
            "Escribe la hora en formato HH:MM en horario de Madrid.\n"
            "Ejemplo: 12:30"
        )

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


def process_incoming_whatsapp_event(db: Session, payload: dict) -> None:
    telefono, body, message_id = extract_text_message(payload)

    if not telefono:
        return

    session = get_or_create_session(db, telefono)

    if message_id and session.last_message_id == message_id:
        return

    session.last_message_id = message_id

    if not body:
        reply = "Por ahora solo entiendo mensajes de texto. Escribe menú."
    else:
        text = body.strip()

        if text.lower() in ["menu", "menú", "hola", "start"]:
            reset_to_menu(session)
            reply = MENU_TEXT
        elif session.state == "MENU":
            reply = process_menu_selection(db, session, text)
        elif session.state == "LOOKUP_REF":
            reply = process_lookup_flow(db, session, text)
            reset_to_menu(session)
        elif session.state == "CANCEL_REF":
            reply = process_cancel_flow(db, session, text)
        elif session.state.startswith("BOOKING_"):
            reply = process_booking_flow(db, session, text)
        else:
            reset_to_menu(session)
            reply = MENU_TEXT

        
    db.add(session)
    db.commit()

    if reply == MENU_TEXT:
        buttons = [
            {"id": "BOOK", "title": "Reservar cita"},
            {"id": "VIEW", "title": "Ver reserva"},
            {"id": "CANCEL", "title": "Cancelar reserva"},
        ]
        send_whatsapp_buttons(
            telefono,
            "Bienvenido a SalonFlow 💈\n¿Qué deseas hacer?",
            buttons,
        )
    else:
        send_text_message(telefono, reply)
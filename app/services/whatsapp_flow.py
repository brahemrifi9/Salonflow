"""
WhatsApp flow — multi-tenant aware, bilingual (ES / EN).

Business resolution strategy:
  Each incoming webhook message contains the receiving WhatsApp phone number ID
  (value["metadata"]["phone_number_id"]). We look up which Business has that
  phone_number_id and route all queries to that business.

  If no business matches, we silently ignore the message (it's not ours).

  Each Business row has: whatsapp_phone_number_id = Column(String(64))
  Set this in the DB for each business from the Meta dashboard.

Language detection (once per webhook event):
  Always uses business.language field (default 'es').
"""

import logging
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.domain.booking_rules import validate_and_compute_end_time_utc
from app.utils.booking_ref import generate_booking_ref
from app.services.i18n import t, day_short, day_long, month_short
from app.services.meta_whatsapp import (
    send_text_message,
    send_whatsapp_buttons,
    send_whatsapp_list,
    send_whatsapp_list_sections,
)

logger = logging.getLogger(__name__)


_SLOT_STEP = timedelta(minutes=15)

# Internal sentinel — its text value is never sent to users.
MENU_TEXT = "__MENU__"


# ─────────────────────────────────────────────
# Language detection
# ─────────────────────────────────────────────

def detect_language(telefono: str, business: models.Business) -> str:
    return business.language or "es"


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
# Message extraction
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


def parse_local_datetime_to_utc(date_str: str, time_str: str, tz: ZoneInfo) -> datetime:
    try:
        local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fecha u hora inválida.",
        )
    return local_dt.replace(tzinfo=tz).astimezone(timezone.utc)


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
# Menu / UI builders
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


def build_barbers_menu(barbers: list[models.Barber], lang: str = "es") -> tuple[str, dict]:
    option_map = {}
    lines = [t(lang, "choose_barber_prompt")]
    for idx, barber in enumerate(barbers, start=1):
        option_map[str(idx)] = barber.id
        lines.append(f"{idx}. {barber.name}")
    lines.append("")
    lines.append(t(lang, "choose_barber_hint"))
    return "\n".join(lines), option_map


def format_booking_row_title(booking: models.Booking, tz: ZoneInfo) -> str:
    start_local = booking.start_time.astimezone(tz)
    return f"{booking.service.name} · {start_local.strftime('%d/%m %H:%M')}"[:24]


def format_booking_row_description(booking: models.Booking, tz: ZoneInfo, lang: str = "es") -> str:
    start_local = booking.start_time.astimezone(tz)
    day = day_long(lang, start_local.weekday())
    time_str = start_local.strftime("%H:%M")
    return f"{booking.barber.name} · {day} {time_str}"[:72]


def build_bookings_list_items(
    bookings: list[models.Booking],
    prefix: str,
    lang: str = "es",
    tz: ZoneInfo = ZoneInfo("Europe/Madrid"),
) -> list[dict]:
    return [
        {
            "id": f"{prefix}_{booking.id}",
            "title": format_booking_row_title(booking, tz),
            "description": format_booking_row_description(booking, tz, lang),
        }
        for booking in bookings
    ]


def build_date_list_items(page: int = 1, lang: str = "es", tz: ZoneInfo = ZoneInfo("Europe/Madrid")) -> list[dict]:
    """Next 18 days from today (shop local time) as WhatsApp list items, 9 per page."""
    today = datetime.now(tz).date()
    all_items = []
    for i in range(18):
        d = today + timedelta(days=i)
        label = f"{day_short(lang, d.weekday())} {d.day} {month_short(lang, d.month)}"
        all_items.append({"id": f"DATE_{d.strftime('%Y-%m-%d')}", "title": label})

    if len(all_items) <= 9:
        return all_items

    start = (page - 1) * 9
    page_items = list(all_items[start:start + 9])
    if page == 1:
        page_items.append({"id": "PAGE_DATE_2", "title": t(lang, "nav_more_dates")})
    else:
        page_items.append({"id": "PAGE_DATE_1", "title": t(lang, "nav_prev_dates")})
    return page_items


def get_available_slots_for_date(
    db: Session,
    barber_id: int,
    service_id: int,
    date_str: str,
    business: models.Business,
) -> list[str]:
    """Returns available HH:MM slot strings (Madrid time) for barber+service on date_str."""
    logger.debug(
        "get_available_slots_for_date: barber_id=%s service_id=%s date=%s business_id=%s",
        barber_id, service_id, date_str, business.id,
    )
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        logger.warning("get_available_slots_for_date: invalid date_str=%r", date_str)
        return []

    service = db.query(models.Service).filter(
        models.Service.id == service_id,
        models.Service.business_id == business.id,
        models.Service.is_active == True,  # noqa: E712
    ).first()
    if not service:
        logger.warning(
            "get_available_slots_for_date: service not found service_id=%s business_id=%s",
            service_id, business.id,
        )
        return []

    duration = timedelta(minutes=service.duration_minutes)
    shop_tz = ZoneInfo(business.timezone)
    day_start = datetime.combine(target_date, business.open_time, tzinfo=shop_tz)
    day_end = datetime.combine(target_date, business.close_time, tzinfo=shop_tz)
    break_start = datetime.combine(target_date, business.lunch_start, tzinfo=shop_tz)
    break_end = datetime.combine(target_date, business.lunch_end, tzinfo=shop_tz)

    day_start_utc = day_start.astimezone(timezone.utc)
    day_end_utc = day_end.astimezone(timezone.utc)
    now_utc = datetime.now(timezone.utc)

    existing = (
        db.query(models.Booking)
        .filter(
            models.Booking.barber_id == barber_id,
            models.Booking.business_id == business.id,
            models.Booking.cancelled_at.is_(None),
            models.Booking.start_time < day_end_utc,
            models.Booking.end_time > day_start_utc,
        )
        .all()
    )
    busy = [(b.start_time, b.end_time) for b in existing]

    barber_blocks = (
        db.query(models.BarberBlock)
        .filter(
            models.BarberBlock.barber_id == barber_id,
            models.BarberBlock.business_id == business.id,
            models.BarberBlock.date == target_date,
        )
        .all()
    )
    blocks = [
        (
            datetime.combine(blk.date, blk.start_time, tzinfo=shop_tz),
            datetime.combine(blk.date, blk.end_time, tzinfo=shop_tz),
        )
        for blk in barber_blocks
    ]

    def overlaps(s: datetime, e: datetime) -> bool:
        for b_s, b_e in busy:
            if s < b_e and e > b_s:
                return True
        for blk_s, blk_e in blocks:
            if s < blk_e and e > blk_s:
                return True
        return False

    slots = []
    slot_t = day_start
    last_start = day_end - duration

    while slot_t <= last_start:
        slot_end = slot_t + duration
        slot_t_utc = slot_t.astimezone(timezone.utc)
        slot_end_utc = slot_end.astimezone(timezone.utc)

        if slot_t_utc <= now_utc:
            slot_t += _SLOT_STEP
            continue

        if slot_t < break_end and slot_end > break_start:
            slot_t += _SLOT_STEP
            continue

        if not overlaps(slot_t_utc, slot_end_utc):
            slots.append(slot_t.strftime("%H:%M"))

        slot_t += _SLOT_STEP

    return slots


def build_slots_list_sections(
    slots: list[str],
    page: int = 1,
    lang: str = "es",
) -> list[dict]:
    """
    Paginates slots into Mañana/Tarde sections.
    WhatsApp hard limit: 10 rows total across all sections (nav buttons count).
      ≤10 total slots  → single page, no navigation
      first page       → 9 slots + "Más horas →"
      middle pages     → 8 slots + "← Horas anteriores" + "Más horas →"
      last page        → "← Horas anteriores" + up to 9 slots
    """
    total = len(slots)

    if total <= 10:
        page_slots = slots
        prev_item = None
        next_item = None
    else:
        # Page 1 starts at 0 and holds 9 slots (only "next" nav button needed).
        # Each subsequent page starts after the first 9, then advances by 8
        # (middle pages need both nav buttons).
        if page == 1:
            start = 0
        else:
            start = 9 + (page - 2) * 8

        has_prev = page > 1
        # Tentatively reserve 2 rows for both nav buttons (8 slots).
        end = start + 8
        has_next = end < total

        # Last page only needs the "prev" button — can fit one extra slot.
        if has_prev and not has_next:
            end = min(start + 9, total)

        page_slots = slots[start:end]
        # Recompute after any end-adjustment.
        has_next = (start + len(page_slots)) < total

        prev_item = {"id": f"PAGE_SLOT_{page - 1}", "title": t(lang, "nav_prev_slots")} if has_prev else None
        next_item = {"id": f"PAGE_SLOT_{page + 1}", "title": t(lang, "nav_more_slots")} if has_next else None

    morning = []
    afternoon = []
    for slot in page_slots:
        item = {"id": f"TIME_{slot}", "title": slot}
        if int(slot.split(":")[0]) < 15:
            morning.append(item)
        else:
            afternoon.append(item)

    sections = []
    if morning:
        sections.append({"title": t(lang, "section_morning"), "rows": morning})
    if afternoon:
        sections.append({"title": t(lang, "section_afternoon"), "rows": afternoon})

    nav_rows = [item for item in (prev_item, next_item) if item]
    if nav_rows:
        sections.append({"title": t(lang, "section_nav"), "rows": nav_rows})

    return sections


def get_saved_client_nombre(db: Session, telefono: str, business_id: int) -> str | None:
    """Returns the saved name for this phone+business, or None if not found."""
    telefono = normalize_phone(telefono)
    cliente = db.query(models.Cliente).filter(
        models.Cliente.telefono == telefono,
        models.Cliente.business_id == business_id,
    ).first()
    if cliente and cliente.nombre:
        return cliente.nombre
    return None


def format_booking_details(booking: models.Booking, tz: ZoneInfo, lang: str = "es") -> str:
    start_madrid = booking.start_time.astimezone(tz)
    end_madrid = booking.end_time.astimezone(tz)
    status_key = "booking_status_cancelled" if booking.cancelled_at else "booking_status_confirmed"
    return (
        f"{t(lang, 'booking_details_label')} {booking.booking_ref}\n"
        f"{t(lang, 'booking_details_status')}: {t(lang, status_key)}\n"
        f"{t(lang, 'booking_details_client')}: {booking.cliente.nombre}\n"
        f"{t(lang, 'booking_details_phone')}: {booking.cliente.telefono}\n"
        f"{t(lang, 'booking_details_barber')}: {booking.barber.name}\n"
        f"{t(lang, 'booking_details_service')}: {booking.service.name}\n"
        f"{t(lang, 'booking_details_date')}: {start_madrid.strftime('%Y-%m-%d')}\n"
        f"{t(lang, 'booking_details_time')}: {start_madrid.strftime('%H:%M')} - {end_madrid.strftime('%H:%M')} (Madrid)\n\n"
        f"{t(lang, 'booking_details_footer')}"
    )


def format_human_booking_datetime(dt: datetime, tz: ZoneInfo, lang: str = "es") -> str:
    madrid_dt = dt.astimezone(tz)
    now_madrid = datetime.now(tz).date()
    target_date = madrid_dt.date()
    if target_date == now_madrid:
        day_label = t(lang, "today")
    elif target_date == now_madrid.fromordinal(now_madrid.toordinal() + 1):
        day_label = t(lang, "tomorrow")
    else:
        day_label = madrid_dt.strftime("%d/%m/%Y")
    return f"{day_label} a las {madrid_dt.strftime('%H:%M')}" if lang == "es" else f"{day_label} at {madrid_dt.strftime('%H:%M')}"


# ─────────────────────────────────────────────
# Booking creation from session data — scoped
# ─────────────────────────────────────────────

def create_booking_from_session_data(
    db: Session,
    session: models.WhatsappSession,
) -> models.Booking:
    data = session.get_data()
    business_id = session.business_id

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

    business = db.query(models.Business).filter(models.Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found.")

    requested_start_utc = parse_local_datetime_to_utc(date_str, time_str, ZoneInfo(business.timezone))

    start_utc, end_utc = validate_and_compute_end_time_utc(
        requested_start_utc,
        service.duration_minutes,
        require_client_utc=True,
        enforce_slot_step=True,
        business=business,
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

def process_menu_selection(
    db: Session,
    session: models.WhatsappSession,
    incoming_text: str,
    lang: str = "es",
) -> str:
    text = incoming_text.strip().lower()
    business_id = session.business_id

    if text in ["hola", "menu", "menú", "start", "hi", "hello"]:
        reset_to_menu(session)
        return MENU_TEXT

    if text in ["1", "book"]:
        services = get_active_services(db, business_id)
        if not services:
            reset_to_menu(session)
            return t(lang, "no_services")
        session.state = "BOOKING_SERVICE"
        session.set_data({})
        return "__SEND_SERVICE_LIST__"

    if text in ["2", "view"]:
        bookings = get_active_bookings_for_phone(db, session.telefono, business_id)
        if not bookings:
            reset_to_menu(session)
            return t(lang, "no_active_bookings")
        session.state = "LOOKUP_SELECT"
        session.set_data({})
        return "__SEND_VIEW_BOOKINGS_LIST__"

    if text in ["3", "cancel"]:
        bookings = get_active_bookings_for_phone(db, session.telefono, business_id)
        if not bookings:
            reset_to_menu(session)
            return t(lang, "no_bookings_to_cancel")
        session.state = "CANCEL_SELECT"
        session.set_data({})
        return "__SEND_CANCEL_BOOKINGS_LIST__"

    return MENU_TEXT


def process_lookup_select_flow(
    db: Session,
    session: models.WhatsappSession,
    incoming_text: str,
    lang: str = "es",
    business: models.Business | None = None,
) -> str:
    text = incoming_text.strip()
    business_id = session.business_id
    shop_tz = ZoneInfo(business.timezone) if business else ZoneInfo("Europe/Madrid")

    booking_id = None
    if text.startswith("VIEWBOOKING_"):
        raw_id = text.replace("VIEWBOOKING_", "", 1)
        if raw_id.isdigit():
            booking_id = int(raw_id)

    if not booking_id:
        return t(lang, "booking_selection_invalid")

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
        return t(lang, "booking_not_found")

    reset_to_menu(session)
    return format_booking_details(booking, shop_tz, lang)


def process_cancel_select_flow(
    db: Session,
    session: models.WhatsappSession,
    incoming_text: str,
    lang: str = "es",
    business: models.Business | None = None,
) -> str:
    data = session.get_data()
    text = incoming_text.strip()
    shop_tz = ZoneInfo(business.timezone) if business else ZoneInfo("Europe/Madrid")
    business_id = session.business_id

    if session.state == "CANCEL_SELECT":
        booking_id = None
        if text.startswith("CANCELBOOKING_"):
            raw_id = text.replace("CANCELBOOKING_", "", 1)
            if raw_id.isdigit():
                booking_id = int(raw_id)

        if not booking_id:
            return t(lang, "booking_selection_invalid")

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
            return t(lang, "cancel_booking_not_found")

        data["cancel_booking_id"] = booking.id
        session.set_data(data)
        session.state = "CANCEL_CONFIRM"

        start_text = format_human_booking_datetime(booking.start_time, shop_tz, lang)
        return t(lang, "cancel_confirm_prompt",
                 service=booking.service.name,
                 barber=booking.barber.name,
                 start_text=start_text)

    if session.state == "CANCEL_CONFIRM":
        lowered = text.lower()

        if lowered == "no":
            reset_to_menu(session)
            return t(lang, "cancel_aborted")

        # Accept both language-specific confirm word and the other language's word.
        if lowered not in ("si", "yes"):
            return t(lang, "cancel_confirm_invalid")

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
            return t(lang, "booking_generic_not_found")

        if booking.cancelled_at is not None:
            reset_to_menu(session)
            return t(lang, "already_cancelled")

        booking.cancelled_at = datetime.now(timezone.utc)
        db.commit()
        reset_to_menu(session)
        return t(lang, "cancel_success")

    reset_to_menu(session)
    return MENU_TEXT


def process_booking_flow(
    db: Session,
    session: models.WhatsappSession,
    incoming_text: str,
    lang: str = "es",
    business: models.Business | None = None,
) -> str:
    data = session.get_data()
    text = incoming_text.strip()
    business_id = session.business_id
    shop_tz = ZoneInfo(business.timezone) if business else ZoneInfo("Europe/Madrid")

    if session.state == "BOOKING_SERVICE":
        service_id = None
        if text.startswith("SERVICE_"):
            raw_id = text.replace("SERVICE_", "", 1)
            if raw_id.isdigit():
                service_id = int(raw_id)
        elif text.isdigit():
            service_id = int(text)

        if not service_id:
            return t(lang, "service_invalid")

        service = db.query(models.Service).filter(
            models.Service.id == service_id,
            models.Service.business_id == business_id,
        ).first()
        if not service or not service.is_active:
            return t(lang, "service_unavailable")

        active_barbers = get_active_barbers(db, business_id)
        if not active_barbers:
            reset_to_menu(session)
            return t(lang, "no_barbers")

        barbers_message, barber_options = build_barbers_menu(active_barbers, lang)
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
            return t(lang, "barber_invalid")

        barber = db.query(models.Barber).filter(
            models.Barber.id == barber_id,
            models.Barber.business_id == business_id,
        ).first()
        if not barber or not barber.is_active:
            return t(lang, "barber_not_found")

        data["barber_id"] = barber.id
        data["barber_name"] = barber.name
        session.set_data(data)
        session.state = "BOOKING_DATE"
        return "__SEND_DATE_LIST_PAGE_1__"

    if session.state == "BOOKING_DATE":
        if text == "PAGE_DATE_2":
            return "__SEND_DATE_LIST_PAGE_2__"
        if text == "PAGE_DATE_1":
            return "__SEND_DATE_LIST_PAGE_1__"

        logger.debug(
            "BOOKING_DATE: telefono=%s text=%r data_keys=%s",
            session.telefono, text, list(data.keys()),
        )
        date_str = None
        if text.startswith("DATE_"):
            candidate = text[5:]
            try:
                datetime.strptime(candidate, "%Y-%m-%d")
                date_str = candidate
            except ValueError:
                logger.warning("BOOKING_DATE: invalid DATE_ candidate %r", candidate)
        else:
            try:
                datetime.strptime(text, "%Y-%m-%d")
                date_str = text
            except ValueError:
                logger.warning("BOOKING_DATE: text %r not parseable as date", text)

        if not date_str:
            logger.debug("BOOKING_DATE: no valid date_str, re-sending date list")
            return "__SEND_DATE_LIST_PAGE_1__"

        if datetime.strptime(date_str, "%Y-%m-%d").date() < datetime.now(shop_tz).date():
            logger.debug("BOOKING_DATE: date %s is in the past", date_str)
            return "__SEND_DATE_LIST_PAST__"

        logger.debug(
            "BOOKING_DATE: accepted date=%s barber_id=%s service_id=%s",
            date_str, data.get("barber_id"), data.get("service_id"),
        )
        data["date"] = date_str
        session.set_data(data)
        session.state = "BOOKING_SLOT"
        return "__SEND_SLOT_LIST_PAGE_1__"

    if session.state == "BOOKING_SLOT":
        if text.startswith("PAGE_SLOT_"):
            page_num_str = text[len("PAGE_SLOT_"):]
            if page_num_str.isdigit() and int(page_num_str) >= 1:
                return f"__SEND_SLOT_LIST_PAGE_{int(page_num_str)}__"

        time_str = None
        if text.startswith("TIME_"):
            candidate = text[5:]
            try:
                datetime.strptime(candidate, "%H:%M")
                time_str = candidate
            except ValueError:
                pass
        else:
            try:
                datetime.strptime(text, "%H:%M")
                time_str = text
            except ValueError:
                pass

        if not time_str:
            return "__SEND_SLOT_LIST_PAGE_1__"

        data["time"] = time_str
        saved_nombre = get_saved_client_nombre(db, session.telefono, session.business_id)
        if saved_nombre:
            data["nombre"] = saved_nombre
            session.set_data(data)
            session.state = "BOOKING_CONFIRM"
            return t(lang, "booking_confirm_prompt",
                     service=data.get("service_name", ""),
                     barber=data.get("barber_name", ""),
                     date=data.get("date", ""),
                     time=data.get("time", ""),
                     nombre=saved_nombre,
                     phone=normalize_phone(session.telefono))
        session.set_data(data)
        session.state = "BOOKING_NAME"
        return t(lang, "ask_name")

    if session.state == "BOOKING_NAME":
        nombre = text.strip()
        if not nombre:
            return t(lang, "name_invalid")
        data["nombre"] = nombre
        session.set_data(data)
        session.state = "BOOKING_CONFIRM"
        return t(lang, "booking_confirm_prompt",
                 service=data.get("service_name", ""),
                 barber=data.get("barber_name", ""),
                 date=data.get("date", ""),
                 time=data.get("time", ""),
                 nombre=nombre,
                 phone=normalize_phone(session.telefono))

    if session.state == "BOOKING_CONFIRM":
        lowered = text.lower()
        if lowered == "no":
            reset_to_menu(session)
            return t(lang, "booking_cancelled_by_user")
        # Accept both language-specific confirm word and the other language's word.
        if lowered not in ("si", "yes"):
            return t(lang, "booking_confirm_invalid")

        try:
            booking = create_booking_from_session_data(db, session)
        except HTTPException as exc:
            if exc.status_code == 409:
                session.state = "BOOKING_SLOT"
                return "__SLOT_CONFLICT__"  # always re-shows page 1
            reset_to_menu(session)
            return t(lang, "booking_error", detail=exc.detail)
        except Exception:
            reset_to_menu(session)
            return t(lang, "booking_unexpected_error")

        start_madrid = booking.start_time.astimezone(shop_tz)
        reset_to_menu(session)
        return t(lang, "booking_confirmed",
                 ref=booking.booking_ref,
                 date=start_madrid.strftime("%Y-%m-%d"),
                 time=start_madrid.strftime("%H:%M"),
                 barber=booking.barber.name,
                 service=booking.service.name)

    reset_to_menu(session)
    return MENU_TEXT


# ─────────────────────────────────────────────
# Main entry point — called from routes/whatsapp.py
# ─────────────────────────────────────────────

def process_incoming_whatsapp_event(db: Session, payload: dict) -> None:
    # 1. Resolve which business this webhook is for
    business = resolve_business_from_webhook(db, payload)
    if business is None:
        return

    telefono, body, message_id = extract_text_message(payload)
    if not telefono:
        return

    # 2. Detect language once for the entire event
    lang = detect_language(telefono, business)
    logger.info(
        "Language detection: telefono=%s business.language=%r detected_lang=%r",
        telefono, business.language, lang,
    )

    # 3. Get or create session scoped to this business
    session = get_or_create_session(db, telefono, business.id)

    # 4. Deduplicate repeated webhook deliveries
    if message_id and session.last_message_id == message_id:
        return

    session.last_message_id = message_id

    # 5. Route message to correct flow
    if not body:
        reply = t(lang, "text_only")
    else:
        text = body.strip()
        if text.lower() in ["menu", "menú", "hola", "start"]:
            reset_to_menu(session)
            reply = MENU_TEXT
        elif session.state == "MENU":
            reply = process_menu_selection(db, session, text, lang)
        elif session.state == "LOOKUP_SELECT":
            reply = process_lookup_select_flow(db, session, text, lang, business)
        elif session.state in ["CANCEL_SELECT", "CANCEL_CONFIRM"]:
            reply = process_cancel_select_flow(db, session, text, lang, business)
        elif session.state.startswith("BOOKING_"):
            reply = process_booking_flow(db, session, text, lang, business)
        else:
            reset_to_menu(session)
            reply = MENU_TEXT

    # Snapshot session data before commit so the __SEND_SLOT_LIST__ dispatcher can
    # use it without triggering a post-commit lazy-load on the expired instance.
    _slot_data = session.get_data() if (
        reply.startswith("__SEND_SLOT_LIST_PAGE_") or reply == "__SLOT_CONFLICT__"
    ) else None

    logger.debug(
        "WhatsApp flow: telefono=%s state=%s reply=%r lang=%s",
        session.telefono, session.state, reply, lang,
    )

    db.add(session)
    db.commit()

    # 6. Send response
    if reply == MENU_TEXT:
        send_whatsapp_buttons(
            telefono,
            t(lang, "menu_body"),
            [
                {"id": "BOOK",   "title": t(lang, "btn_book")},
                {"id": "VIEW",   "title": t(lang, "btn_view")},
                {"id": "CANCEL", "title": t(lang, "btn_cancel")},
            ],
        )
    elif reply == "__SEND_SERVICE_LIST__":
        services = get_active_services(db, business.id)
        items = build_services_list(services)
        send_whatsapp_list(
            telefono,
            t(lang, "services_header"),
            t(lang, "services_body"),
            t(lang, "services_button"),
            items,
        )
    elif reply == "__SEND_VIEW_BOOKINGS_LIST__":
        bookings = get_active_bookings_for_phone(db, telefono, business.id)
        items = build_bookings_list_items(bookings, "VIEWBOOKING", lang, ZoneInfo(business.timezone))
        send_whatsapp_list(
            telefono,
            t(lang, "view_bookings_header"),
            t(lang, "view_bookings_body"),
            t(lang, "view_bookings_button"),
            items,
        )
    elif reply == "__SEND_CANCEL_BOOKINGS_LIST__":
        bookings = get_active_bookings_for_phone(db, telefono, business.id)
        items = build_bookings_list_items(bookings, "CANCELBOOKING", lang, ZoneInfo(business.timezone))
        send_whatsapp_list(
            telefono,
            t(lang, "cancel_bookings_header"),
            t(lang, "cancel_bookings_body"),
            t(lang, "cancel_bookings_button"),
            items,
        )
    elif reply in ("__SEND_DATE_LIST_PAGE_1__", "__SEND_DATE_LIST_PAGE_2__", "__SEND_DATE_LIST_PAST__"):
        if reply == "__SEND_DATE_LIST_PAST__":
            send_text_message(telefono, t(lang, "date_in_past"))
        page = 2 if reply == "__SEND_DATE_LIST_PAGE_2__" else 1
        items = build_date_list_items(page=page, lang=lang, tz=ZoneInfo(business.timezone))
        send_whatsapp_list(
            telefono,
            t(lang, "dates_header"),
            t(lang, "dates_body"),
            t(lang, "dates_button"),
            items,
        )
    elif reply.startswith("__SEND_SLOT_LIST_PAGE_") or reply == "__SLOT_CONFLICT__":
        if reply == "__SLOT_CONFLICT__":
            send_text_message(telefono, t(lang, "slot_conflict"))
            slot_page = 1
        else:
            # Extract N from "__SEND_SLOT_LIST_PAGE_N__"
            raw = reply[len("__SEND_SLOT_LIST_PAGE_"):-len("__")]
            slot_page = int(raw) if raw.isdigit() else 1
        # Use the pre-commit snapshot — session attributes are expired after db.commit()
        data = _slot_data or {}
        barber_id = data.get("barber_id")
        service_id = data.get("service_id")
        date_str = data.get("date")
        logger.debug(
            "__SEND_SLOT_LIST__: barber_id=%s service_id=%s date=%s business_id=%s",
            barber_id, service_id, date_str, business.id,
        )
        if not barber_id or not service_id or not date_str:
            logger.error(
                "__SEND_SLOT_LIST__: missing session data — barber_id=%s service_id=%s date=%s",
                barber_id, service_id, date_str,
            )
            send_text_message(telefono, t(lang, "session_error"))
        else:
            slots = get_available_slots_for_date(db, barber_id, service_id, date_str, business)
            logger.debug("__SEND_SLOT_LIST__: found %d slots for %s", len(slots), date_str)
            if not slots:
                send_text_message(telefono, t(lang, "no_slots", date=date_str))
                session.state = "BOOKING_DATE"
                data.pop("date", None)
                session.set_data(data)
                db.add(session)
                db.commit()
                items = build_date_list_items(page=1, lang=lang, tz=ZoneInfo(business.timezone))
                send_whatsapp_list(
                    telefono,
                    t(lang, "dates_header"),
                    t(lang, "dates_body"),
                    t(lang, "dates_button"),
                    items,
                )
            else:
                sections = build_slots_list_sections(slots, page=slot_page, lang=lang)
                logger.debug("__SEND_SLOT_LIST__: sending %d sections (page %d)", len(sections), slot_page)
                send_whatsapp_list_sections(
                    telefono,
                    t(lang, "slots_header"),
                    t(lang, "slots_body"),
                    t(lang, "slots_button"),
                    sections,
                )
    else:
        send_text_message(telefono, reply)

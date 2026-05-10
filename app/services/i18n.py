"""Bilingual string table for the WhatsApp booking flow (ES / EN)."""

_STRINGS: dict[str, dict[str, str]] = {
    # ── Menu ─────────────────────────────────────────────────────────────
    "menu_body": {
        "es": "Bienvenido a SalonFlow 💈\n¿Qué deseas hacer?",
        "en": "Welcome to SalonFlow 💈\nWhat would you like to do?",
    },
    "btn_book":   {"es": "Reservar", "en": "Book"},
    "btn_view":   {"es": "Ver",      "en": "View"},
    "btn_cancel": {"es": "Cancelar", "en": "Cancel"},
    # ── Service list ──────────────────────────────────────────────────────
    "services_header": {"es": "SalonFlow 💈",          "en": "SalonFlow 💈"},
    "services_body":   {"es": "Selecciona un servicio", "en": "Select a service"},
    "services_button": {"es": "Ver servicios",          "en": "View services"},
    "no_services": {
        "es": "No hay servicios disponibles ahora mismo.",
        "en": "No services are available right now.",
    },
    # ── Barber ────────────────────────────────────────────────────────────
    "choose_barber_prompt": {"es": "Elige barbero:",                              "en": "Choose a barber:"},
    "choose_barber_hint":   {"es": "Responde con el número del barbero.",          "en": "Reply with the barber's number."},
    "no_barbers": {
        "es": "No hay barberos disponibles ahora mismo.",
        "en": "No barbers are available right now.",
    },
    "barber_invalid": {
        "es": "Barbero no válido. Responde con uno de los números mostrados.",
        "en": "Invalid barber. Reply with one of the numbers shown.",
    },
    "barber_not_found": {
        "es": "Barbero no encontrado o inactivo.",
        "en": "Barber not found or inactive.",
    },
    # ── Date list ─────────────────────────────────────────────────────────
    "dates_header": {"es": "SalonFlow 💈",                        "en": "SalonFlow 💈"},
    "dates_body":   {"es": "Selecciona una fecha para tu reserva", "en": "Choose a date for your appointment"},
    "dates_button": {"es": "Ver fechas",                          "en": "View dates"},
    "nav_more_dates": {"es": "Más fechas →",       "en": "More dates →"},
    "nav_prev_dates": {"es": "← Fechas anteriores", "en": "← Earlier dates"},
    "date_in_past": {
        "es": "Esa fecha ya pasó. Por favor elige una fecha disponible.",
        "en": "That date has already passed. Please choose an available date.",
    },
    # ── Slot list ─────────────────────────────────────────────────────────
    "slots_header": {"es": "Horarios disponibles 💈", "en": "Available times 💈"},
    "slots_body":   {"es": "Selecciona un horario",   "en": "Select a time slot"},
    "slots_button": {"es": "Ver horarios",             "en": "View times"},
    "section_morning":   {"es": "Mañana",     "en": "Morning"},
    "section_afternoon": {"es": "Tarde",      "en": "Afternoon"},
    "section_nav":       {"es": "Navegación", "en": "Navigation"},
    "nav_more_slots": {"es": "Más horas →",       "en": "More times →"},
    "nav_prev_slots": {"es": "← Horas anteriores", "en": "← Earlier times"},
    "no_slots": {
        "es": "No hay horarios disponibles el {date}. Por favor elige otra fecha.",
        "en": "No times are available on {date}. Please choose another date.",
    },
    "slot_conflict": {
        "es": "Lo sentimos, ese horario ya fue tomado. Por favor elige otro horario.",
        "en": "Sorry, that slot has just been taken. Please choose another time.",
    },
    "service_invalid": {
        "es": "Servicio no válido. Abre la lista y elige un servicio.",
        "en": "Invalid service. Open the list and choose a service.",
    },
    "service_unavailable": {
        "es": "Servicio no disponible ahora mismo.",
        "en": "That service is not available right now.",
    },
    # ── Bookings list (view / cancel) ─────────────────────────────────────
    "view_bookings_header": {"es": "Tus reservas 💈",                             "en": "Your bookings 💈"},
    "view_bookings_body":   {"es": "Selecciona una reserva para ver los detalles", "en": "Select a booking to view its details"},
    "view_bookings_button": {"es": "Ver reservas",                                "en": "View bookings"},
    "cancel_bookings_header": {"es": "Cancelar reserva 💈",                            "en": "Cancel booking 💈"},
    "cancel_bookings_body":   {"es": "Selecciona la reserva que quieres cancelar",     "en": "Select the booking you want to cancel"},
    "cancel_bookings_button": {"es": "Ver reservas",                                   "en": "View bookings"},
    "no_active_bookings": {
        "es": "No tienes reservas activas en este número.",
        "en": "You have no active bookings on this number.",
    },
    "no_bookings_to_cancel": {
        "es": "No tienes reservas activas para cancelar.",
        "en": "You have no active bookings to cancel.",
    },
    "booking_selection_invalid": {
        "es": "Selección no válida. Abre la lista y elige una reserva.",
        "en": "Invalid selection. Open the list and choose a booking.",
    },
    "booking_not_found": {
        "es": "No he encontrado esa reserva en este número.",
        "en": "I couldn't find that booking on this number.",
    },
    # ── Booking details (view) ────────────────────────────────────────────
    "booking_details_label":   {"es": "Reserva",   "en": "Booking"},
    "booking_details_status":  {"es": "Estado",    "en": "Status"},
    "booking_details_client":  {"es": "Cliente",   "en": "Client"},
    "booking_details_phone":   {"es": "Teléfono",  "en": "Phone"},
    "booking_details_barber":  {"es": "Barbero",   "en": "Barber"},
    "booking_details_service": {"es": "Servicio",  "en": "Service"},
    "booking_details_date":    {"es": "Fecha",     "en": "Date"},
    "booking_details_time":    {"es": "Hora",      "en": "Time"},
    "booking_details_footer":  {"es": "Escribe menú para volver.", "en": "Type menu to go back."},
    "booking_status_confirmed": {"es": "confirmada", "en": "confirmed"},
    "booking_status_cancelled": {"es": "cancelada",  "en": "cancelled"},
    # ── Cancel flow ───────────────────────────────────────────────────────
    "cancel_confirm_prompt": {
        "es": (
            "¿Seguro que quieres cancelar esta reserva?\n\n"
            "{service}\n{barber}\n{start_text}\n\n"
            "Responde SI para confirmar o NO para volver."
        ),
        "en": (
            "Are you sure you want to cancel this booking?\n\n"
            "{service}\n{barber}\n{start_text}\n\n"
            "Reply YES to confirm or NO to go back."
        ),
    },
    "cancel_confirm_invalid": {
        "es": "Responde SI para confirmar o NO para volver.",
        "en": "Reply YES to confirm or NO to go back.",
    },
    "cancel_aborted": {
        "es": "Cancelación abortada. Escribe menú para volver.",
        "en": "Cancellation aborted. Type menu to go back.",
    },
    "cancel_booking_not_found": {
        "es": "No he encontrado esa reserva activa en este número.",
        "en": "I couldn't find that active booking on this number.",
    },
    "already_cancelled": {
        "es": "Esa reserva ya estaba cancelada.",
        "en": "That booking was already cancelled.",
    },
    "cancel_success": {
        "es": "Reserva cancelada correctamente.",
        "en": "Booking cancelled successfully.",
    },
    "booking_generic_not_found": {
        "es": "No he encontrado esa reserva.",
        "en": "I couldn't find that booking.",
    },
    # ── Booking flow ──────────────────────────────────────────────────────
    "ask_name": {
        "es": "Escribe tu nombre para la reserva.",
        "en": "Please enter your name for the booking.",
    },
    "name_invalid": {
        "es": "Nombre no válido. Escribe tu nombre para la reserva.",
        "en": "Invalid name. Please enter your name for the booking.",
    },
    "booking_confirm_prompt": {
        "es": (
            "Confirma tu reserva:\n"
            "Servicio: {service}\nBarbero: {barber}\n"
            "Fecha: {date}\nHora: {time} (Madrid)\n"
            "Nombre: {nombre}\nTeléfono: {phone}\n\n"
            "Responde SI para confirmar o NO para cancelar."
        ),
        "en": (
            "Confirm your booking:\n"
            "Service: {service}\nBarber: {barber}\n"
            "Date: {date}\nTime: {time} (Madrid)\n"
            "Name: {nombre}\nPhone: {phone}\n\n"
            "Reply YES to confirm or NO to cancel."
        ),
    },
    "booking_confirm_invalid": {
        "es": "Responde SI para confirmar o NO para cancelar.",
        "en": "Reply YES to confirm or NO to cancel.",
    },
    "booking_cancelled_by_user": {
        "es": "Reserva cancelada. Escribe menú para volver.",
        "en": "Booking cancelled. Type menu to go back.",
    },
    "booking_error": {
        "es": "No se pudo crear la reserva: {detail}",
        "en": "Could not create the booking: {detail}",
    },
    "booking_unexpected_error": {
        "es": "No se pudo crear la reserva por un error inesperado.",
        "en": "Could not create the booking due to an unexpected error.",
    },
    "booking_confirmed": {
        "es": (
            "✅ Reserva confirmada\n\n"
            "Código: {ref}\nFecha: {date}\nHora: {time} (Madrid)\n"
            "Barbero: {barber}\nServicio: {service}\n\n"
            "Guarda este código para consultar o cancelar tu cita."
        ),
        "en": (
            "✅ Booking confirmed\n\n"
            "Ref: {ref}\nDate: {date}\nTime: {time} (Madrid)\n"
            "Barber: {barber}\nService: {service}\n\n"
            "Save this code to view or cancel your appointment."
        ),
    },
    # ── General ───────────────────────────────────────────────────────────
    "text_only": {
        "es": "Por ahora solo entiendo mensajes de texto. Escribe menú.",
        "en": "I can only understand text messages for now. Type menu.",
    },
    "session_error": {
        "es": "Hubo un error con tu sesión. Por favor escribe menú para empezar de nuevo.",
        "en": "There was a problem with your session. Please type menu to start again.",
    },
    # ── Date/time labels ──────────────────────────────────────────────────
    "today":    {"es": "Hoy",    "en": "Today"},
    "tomorrow": {"es": "Mañana", "en": "Tomorrow"},
    # ── Confirm word (lowercase) ──────────────────────────────────────────
    "confirm_word": {"es": "si", "en": "yes"},
}

_DAYS_SHORT = {
    "es": {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"},
    "en": {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"},
}
_DAYS_LONG = {
    "es": {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"},
    "en": {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"},
}
_MONTHS_SHORT = {
    "es": {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
           7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"},
    "en": {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
           7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"},
}


def t(lang: str, key: str, **kwargs: str) -> str:
    """Return the translated string for *key* in *lang*, formatted with **kwargs."""
    bucket = _STRINGS.get(key, {})
    text = bucket.get(lang) or bucket.get("es", key)
    return text.format(**kwargs) if kwargs else text


def day_short(lang: str, weekday: int) -> str:
    return _DAYS_SHORT.get(lang, _DAYS_SHORT["es"])[weekday]


def day_long(lang: str, weekday: int) -> str:
    return _DAYS_LONG.get(lang, _DAYS_LONG["es"])[weekday]


def month_short(lang: str, month: int) -> str:
    return _MONTHS_SHORT.get(lang, _MONTHS_SHORT["es"])[month]

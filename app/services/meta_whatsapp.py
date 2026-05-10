import logging
import os

import requests


logger = logging.getLogger(__name__)

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v23.0")


def _post_whatsapp_payload(payload: dict) -> dict:
    if not WHATSAPP_ACCESS_TOKEN:
        raise RuntimeError("WHATSAPP_ACCESS_TOKEN no configurado.")
    if not WHATSAPP_PHONE_NUMBER_ID:
        raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID no configurado.")

    url = (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        response_text = ""
        try:
            response_text = exc.response.text
        except Exception:
            response_text = "No response body"

        logger.exception(
            "Meta WhatsApp HTTP error. Response: %s",
            response_text,
        )
        raise RuntimeError(
            f"Error HTTP al enviar mensaje por WhatsApp Cloud API: {response_text}"
        ) from exc
    except requests.RequestException as exc:
        logger.exception("Network error sending WhatsApp message")
        raise RuntimeError(
            "Error de red al enviar mensaje por WhatsApp Cloud API."
        ) from exc


def send_text_message(to_phone: str, body: str) -> dict:
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {
            "body": body,
        },
    }
    return _post_whatsapp_payload(payload)


def send_whatsapp_buttons(to_phone: str, text: str, buttons: list[dict]) -> dict:
    button_payload = []
    for b in buttons[:3]:
        button_payload.append(
            {
                "type": "reply",
                "reply": {
                    "id": b["id"][:256],
                    "title": b["title"][:20],
                },
            }
        )

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": text[:1024],
            },
            "action": {
                "buttons": button_payload,
            },
        },
    }

    return _post_whatsapp_payload(payload)


def send_whatsapp_list(
    to_phone: str,
    header: str,
    body_text: str,
    button_text: str,
    items: list[dict],
) -> dict:
    rows = []
    for item in items[:10]:
        row = {
            "id": item["id"][:200],
            "title": item["title"][:24],
        }
        if item.get("description"):
            row["description"] = item["description"][:72]
        rows.append(row)

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": header[:60],
            },
            "body": {
                "text": body_text[:1024],
            },
            "action": {
                "button": button_text[:20],
                "sections": [
                    {
                        "title": "Opciones",
                        "rows": rows,
                    }
                ],
            },
        },
    }

    return _post_whatsapp_payload(payload)


def send_whatsapp_list_sections(
    to_phone: str,
    header: str,
    body_text: str,
    button_text: str,
    sections: list[dict],
) -> dict:
    """Like send_whatsapp_list but accepts multiple named sections."""
    _WHATSAPP_MAX_ROWS = 10
    formatted = []
    remaining = _WHATSAPP_MAX_ROWS
    for section in sections:
        if remaining <= 0:
            break
        rows = []
        for item in section["rows"][:remaining]:
            row = {
                "id": item["id"][:200],
                "title": item["title"][:24],
            }
            if item.get("description"):
                row["description"] = item["description"][:72]
            rows.append(row)
        remaining -= len(rows)
        if rows:
            formatted.append({
                "title": section.get("title", "")[:24],
                "rows": rows,
            })

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": header[:60],
            },
            "body": {
                "text": body_text[:1024],
            },
            "action": {
                "button": button_text[:20],
                "sections": formatted,
            },
        },
    }

    return _post_whatsapp_payload(payload)
import logging
import os

import requests


logger = logging.getLogger(__name__)

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v23.0")

def send_whatsapp_buttons(to_phone: str, text: str, buttons: list):
    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    button_payload = []
    for b in buttons:
        button_payload.append({
            "type": "reply",
            "reply": {
                "id": b["id"],
                "title": b["title"]
            }
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": text
            },
            "action": {
                "buttons": button_payload
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


def send_text_message(to_phone: str, body: str) -> dict:
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

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {
            "body": body,
        },
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
            "Meta WhatsApp HTTP error sending message to %s. Response: %s",
            to_phone,
            response_text,
        )
        raise RuntimeError(
            f"Error HTTP al enviar mensaje por WhatsApp Cloud API: {response_text}"
        ) from exc
    except requests.RequestException as exc:
        logger.exception(
            "Network error sending WhatsApp message to %s",
            to_phone,
        )
        raise RuntimeError(
            "Error de red al enviar mensaje por WhatsApp Cloud API."
        ) from exc
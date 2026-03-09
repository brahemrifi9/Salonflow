import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.whatsapp_flow import process_incoming_whatsapp_event

router = APIRouter(prefix="/api/v1/whatsapp", tags=["WhatsApp"])

logger = logging.getLogger(__name__)
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")


@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificación inválido.")


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await request.json()

    try:
        process_incoming_whatsapp_event(db, payload)
    except Exception:
        logger.exception("Error processing WhatsApp webhook payload")

    return {"status": "ok"}
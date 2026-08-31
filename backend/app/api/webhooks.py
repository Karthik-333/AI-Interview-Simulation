"""Optional webhook delivery for interview lifecycle events."""

import json
import logging
from urllib.request import Request as UrlRequest, urlopen

from fastapi import APIRouter

from app.core.settings import WEBHOOK_URL

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def notify(event_type: str, payload: dict) -> bool:
    """Deliver an event when configured; return False on unavailable optional service."""
    if not WEBHOOK_URL:
        return False
    request = UrlRequest(WEBHOOK_URL, data=json.dumps({"event": event_type, "payload": payload}).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=3):
            return True
    except Exception:
        logger.warning("webhook_delivery_failed", exc_info=True)
        return False


@router.get("/status")
def webhook_status():
    return {"configured": bool(WEBHOOK_URL)}

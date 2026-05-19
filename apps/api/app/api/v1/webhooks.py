from __future__ import annotations

import hashlib
import hmac
import json

import structlog
from fastapi import APIRouter, Header, HTTPException, Request, status

from app.api.deps import RedisClient
from app.core.config import get_settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
log = structlog.get_logger(__name__)
settings = get_settings()


def _verify_hikvision_hmac(payload: bytes, signature: str) -> bool:
    """Verify HMAC-SHA256 signature from Hikvision."""
    mac = hmac.new(
        key=settings.hikvision_hmac_secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256,
    )
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, signature.lower())


@router.post("/hikvision/attendance", status_code=202)
async def hikvision_attendance_webhook(
    request: Request,
    redis: RedisClient,
    x_hikvision_signature: str = Header(alias="X-Hikvision-Signature", default=""),
) -> dict[str, str]:
    raw_body = await request.body()

    if not _verify_hikvision_hmac(raw_body, x_hikvision_signature):
        log.warning("Invalid Hikvision HMAC signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from exc

    message = json.dumps(payload)
    await redis.xadd(
        settings.hikvision_attendance_stream,
        {"data": message},
        maxlen=100000,
        approximate=True,
    )

    log.info(
        "Attendance event pushed to stream",
        stream=settings.hikvision_attendance_stream,
    )

    return {"status": "accepted"}

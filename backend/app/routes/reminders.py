import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.schemas import MessageResponse
from app.services.reminder_service import ReminderService, ReminderType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


class ReminderResponse(BaseModel):
    id: str
    client_id: str
    message_id: str
    reminder_type: str
    scheduled_at: datetime
    sent_at: Optional[datetime]
    is_cancelled: bool
    created_at: datetime


@router.get("/", response_model=List[ReminderResponse])
async def list_reminders(
    client_id: Optional[str] = Query(None),
    include_sent: bool = Query(False),
    session: AsyncSession = Depends(get_session),
):
    """
    List reminders

    Query params:
        client_id: Filter by client ID
        include_sent: Include already sent reminders
    """
    reminder_service = ReminderService(session)

    if client_id:
        reminders = await reminder_service.get_client_reminders(
            client_id=client_id, include_sent=include_sent
        )
    else:
        reminders = await reminder_service.get_pending_reminders(limit=100)

    return [
        ReminderResponse(
            id=str(r.id),
            client_id=r.client_id,
            message_id=str(r.message_id),
            reminder_type=r.reminder_type.value,
            scheduled_at=r.scheduled_at,
            sent_at=r.sent_at,
            is_cancelled=r.is_cancelled,
            created_at=r.created_at,
        )
        for r in reminders
    ]


@router.post("/{client_id}/cancel")
async def cancel_reminders(
    client_id: str,
    after_message_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """
    Cancel pending reminders for a client

    Query params:
        after_message_id: Cancel reminders for messages after this ID
    """
    reminder_service = ReminderService(session)

    cancelled_count = await reminder_service.cancel_client_reminders(
        client_id=client_id, after_message_id=after_message_id
    )

    await session.commit()

    return {"success": True, "client_id": client_id, "cancelled_count": cancelled_count}


@router.post("/{reminder_id}/send")
async def send_reminder_manual(
    reminder_id: str, session: AsyncSession = Depends(get_session)
):
    """
    Manually trigger sending a reminder (admin function)
    """
    reminder_service = ReminderService(session)

    success = await reminder_service.mark_reminder_sent(reminder_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )

    await session.commit()

    return {
        "success": True,
        "reminder_id": reminder_id,
        "sent_at": datetime.utcnow().isoformat(),
    }

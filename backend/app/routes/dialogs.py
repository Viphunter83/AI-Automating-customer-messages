import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.database import ChatSession, DialogStatus, Message
from app.models.schemas import ChatSessionResponse, ChatSessionUpdate, DialogStatusEnum
from app.services.dialog_auto_close import DialogAutoCloseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dialogs", tags=["dialogs"])


@router.get("/", response_model=List[ChatSessionResponse])
async def list_dialogs(
    status: Optional[DialogStatusEnum] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List all chat sessions with optional filtering"""
    conditions = []
    if status:
        # Convert DialogStatusEnum to DialogStatus
        status_value = (
            DialogStatus(status.value)
            if isinstance(status, DialogStatusEnum)
            else DialogStatus(status)
        )
        conditions.append(ChatSession.status == status_value)

    query = select(ChatSession)
    if conditions:
        query = query.where(and_(*conditions))

    query = (
        query.order_by(ChatSession.last_activity_at.desc()).limit(limit).offset(offset)
    )

    result = await session.execute(query)
    sessions = result.scalars().all()

    # Get client IDs for batch loading messages
    client_ids = [s.client_id for s in sessions]
    
    # Batch load message counts and last messages
    message_counts = {}
    last_messages = {}
    
    if client_ids:
        # Get message counts
        count_result = await session.execute(
            select(Message.client_id, func.count(Message.id).label("count"))
            .where(Message.client_id.in_(client_ids))
            .group_by(Message.client_id)
        )
        for row in count_result.all():
            message_counts[row.client_id] = row.count
        
        # Get last messages for each client
        # Use a simpler approach: get last message per client
        for client_id in client_ids:
            last_msg_result = await session.execute(
                select(Message)
                .where(Message.client_id == client_id)
                .order_by(desc(Message.created_at))
                .limit(1)
            )
            last_msg = last_msg_result.scalar_one_or_none()
            if last_msg:
                preview = last_msg.content[:100] + "..." if len(last_msg.content) > 100 else last_msg.content
                last_messages[client_id] = {
                    "preview": preview,
                    "created_at": last_msg.created_at
                }

    # Convert DialogStatus enum to DialogStatusEnum for Pydantic
    return [
        ChatSessionResponse(
            id=str(s.id),
            client_id=s.client_id,
            status=DialogStatusEnum(s.status.value),
            last_activity_at=s.last_activity_at,
            closed_at=s.closed_at,
            farewell_sent_at=s.farewell_sent_at,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=message_counts.get(s.client_id, 0),
            last_message_preview=last_messages.get(s.client_id, {}).get("preview"),
            last_message_at=last_messages.get(s.client_id, {}).get("created_at"),
        )
        for s in sessions
    ]


@router.get("/{client_id}", response_model=ChatSessionResponse)
async def get_dialog(client_id: str, session: AsyncSession = Depends(get_session)):
    """Get chat session for a specific client"""
    dialog_service = DialogAutoCloseService(session)
    session_obj = await dialog_service.get_or_create_session(client_id)
    await session.commit()
    # Convert DialogStatus enum to DialogStatusEnum for Pydantic
    session_dict = {
        "id": str(session_obj.id),
        "client_id": session_obj.client_id,
        "status": DialogStatusEnum(session_obj.status.value),
        "last_activity_at": session_obj.last_activity_at,
        "closed_at": session_obj.closed_at,
        "farewell_sent_at": session_obj.farewell_sent_at,
        "created_at": session_obj.created_at,
        "updated_at": session_obj.updated_at,
    }
    return ChatSessionResponse(**session_dict)


@router.post("/{client_id}/close", status_code=status.HTTP_200_OK)
async def close_dialog(client_id: str, session: AsyncSession = Depends(get_session)):
    """Manually close a dialog"""
    dialog_service = DialogAutoCloseService(session)
    success = await dialog_service.close_session(client_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close dialog",
        )

    await session.commit()
    return {"status": "success", "message": f"Dialog for {client_id} closed"}


@router.post("/{client_id}/reopen", status_code=status.HTTP_200_OK)
async def reopen_dialog(client_id: str, session: AsyncSession = Depends(get_session)):
    """Reopen a closed dialog"""
    dialog_service = DialogAutoCloseService(session)
    await dialog_service.update_activity(client_id)  # This will reopen if closed
    await session.commit()
    return {"status": "success", "message": f"Dialog for {client_id} reopened"}


@router.get("/{client_id}/stats", response_model=dict)
async def get_dialog_stats(
    client_id: str, session: AsyncSession = Depends(get_session)
):
    """Get statistics for a dialog"""
    # Get message count
    result = await session.execute(
        select(func.count(Message.id)).where(Message.client_id == client_id)
    )
    message_count = result.scalar_one()

    # Get last message
    result = await session.execute(
        select(Message)
        .where(Message.client_id == client_id)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    last_message = result.scalar_one_or_none()

    # Get session info
    dialog_service = DialogAutoCloseService(session)
    session_obj = await dialog_service.get_or_create_session(client_id)

    return {
        "client_id": client_id,
        "status": session_obj.status.value,
        "message_count": message_count,
        "last_activity_at": session_obj.last_activity_at.isoformat(),
        "last_message_at": last_message.created_at.isoformat()
        if last_message
        else None,
        "created_at": session_obj.created_at.isoformat(),
        "closed_at": session_obj.closed_at.isoformat()
        if session_obj.closed_at
        else None,
    }

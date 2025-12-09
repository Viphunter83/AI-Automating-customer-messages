"""
Unread Messages API endpoints
Handles marking messages as read and getting unread counts
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.unread_tracker import UnreadTrackerService
from app.auth.dependencies import get_current_operator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/unread", tags=["unread"])


@router.post("/{client_id}/mark-read", status_code=status.HTTP_200_OK)
async def mark_messages_as_read(
    client_id: str,
    message_id: Optional[str] = Query(None, description="Specific message ID to mark as read. If not provided, marks all messages as read."),
    session: AsyncSession = Depends(get_session),
    operator_id: str = Depends(get_current_operator),
):
    """
    Mark messages as read for an operator-client pair
    
    If message_id is provided, marks that specific message and all previous as read.
    If not provided, marks all messages for this client as read.
    """
    try:
        unread_tracker = UnreadTrackerService(session)
        
        # Convert message_id string to UUID if provided
        message_uuid = None
        if message_id:
            try:
                message_uuid = UUID(message_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid message_id format"
                )
        
        read_record = await unread_tracker.mark_messages_as_read(
            operator_id=operator_id,
            client_id=client_id,
            message_id=message_uuid,
        )
        
        await session.commit()
        
        return {
            "status": "success",
            "operator_id": operator_id,
            "client_id": client_id,
            "last_read_message_id": str(read_record.last_read_message_id) if read_record.last_read_message_id else None,
            "last_read_at": read_record.last_read_at.isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Error marking messages as read: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark messages as read: {str(e)}"
        )


@router.get("/{client_id}/count", status_code=status.HTTP_200_OK)
async def get_unread_count(
    client_id: str,
    session: AsyncSession = Depends(get_session),
    operator_id: str = Depends(get_current_operator),
):
    """Get count of unread messages for an operator-client pair"""
    try:
        unread_tracker = UnreadTrackerService(session)
        count = await unread_tracker.get_unread_count(
            operator_id=operator_id,
            client_id=client_id,
        )
        
        return {
            "operator_id": operator_id,
            "client_id": client_id,
            "unread_count": count,
        }
    
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread count: {str(e)}"
        )


@router.get("/counts", status_code=status.HTTP_200_OK)
async def get_all_unread_counts(
    session: AsyncSession = Depends(get_session),
    operator_id: str = Depends(get_current_operator),
):
    """Get unread counts for all clients for an operator"""
    try:
        unread_tracker = UnreadTrackerService(session)
        counts = await unread_tracker.get_unread_counts_for_all_clients(
            operator_id=operator_id
        )
        
        return {
            "operator_id": operator_id,
            "unread_counts": counts,
        }
    
    except Exception as e:
        logger.error(f"Error getting unread counts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread counts: {str(e)}"
        )











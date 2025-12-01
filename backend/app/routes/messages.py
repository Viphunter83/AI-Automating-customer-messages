"""
Refactored Messages Router
Uses separate services for processing, response creation, and delivery
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_session
from app.models.database import (
    Classification,
    Message,
    MessageType,
    PriorityLevel,
)
from app.models.schemas import (
    ClassificationResponse,
    MessageCreate,
    MessageResponse,
    MessageTypeEnum,
)
from app.services.message_delivery_service import MessageDeliveryService
from app.services.message_processing_service import MessageProcessingService
from app.services.message_response_service import MessageResponseService

logger = logging.getLogger(__name__)
settings = get_settings()


def get_request_id(request: Request) -> str:
    """Get request ID from request state for correlation"""
    return getattr(request.state, "request_id", "no-request-id")


router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    x_webhook_url: Optional[str] = Header(None, alias="X-Webhook-URL"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
):
    """
    Create a new message with rate limiting per client_id.
    
    This endpoint processes incoming messages through the following flow:
    1. Rate limiting check
    2. Duplicate detection (idempotency)
    3. Message processing (text cleaning, classification, escalation)
    4. Response creation
    5. Reminder management
    6. Background delivery (webhook + WebSocket)
    
    Rate limits:
    - Per IP: 60/minute, 1000/hour (via slowapi middleware)
    - Per client_id: 10 messages/minute (custom check)
    
    Headers:
        X-Webhook-URL: Optional URL to send response back to
        X-Idempotency-Key: Optional idempotency key to prevent duplicate processing
    """
    request_id = get_request_id(request)
    
    try:
        logger.info(
            f"[{request_id}] 📨 Received message from {message_data.client_id}: "
            f"{message_data.content[:50]}..."
        )

        # Initialize services
        processing_service = MessageProcessingService(session)
        response_service = MessageResponseService(session)
        delivery_service = MessageDeliveryService(webhook_url=x_webhook_url)

        # ============ STEP 1: Rate limiting per client_id ============
        if settings.rate_limit_enabled:
            one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
            recent_messages_count = await session.execute(
                select(func.count(Message.id)).where(
                    Message.client_id == message_data.client_id,
                    Message.created_at >= one_minute_ago,
                )
            )
            count = recent_messages_count.scalar_one()

            if count >= settings.rate_limit_message_per_minute:
                logger.warning(
                    f"[{request_id}] ⚠️ Rate limit exceeded for client {message_data.client_id}: "
                    f"{count} messages in last minute"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: maximum {settings.rate_limit_message_per_minute} messages per minute per client",
                )

        # ============ STEP 2: Check for duplicate ============
        duplicate_message = await processing_service.check_duplicate(
            message_data.client_id, message_data.content
        )

        if duplicate_message:
            logger.warning(
                f"⚠️ Duplicate message detected for client {message_data.client_id}"
            )

            # Get the response message for this duplicate
            response_result = await session.execute(
                select(Message)
                .where(
                    Message.client_id == message_data.client_id,
                    Message.message_type.in_(
                        [MessageType.BOT_AUTO, MessageType.BOT_ESCALATED]
                    ),
                    Message.created_at >= duplicate_message.created_at,
                )
                .order_by(Message.created_at.asc())
                .limit(1)
            )
            response_message = response_result.scalar_one_or_none()

            # Get classification if exists
            classification_result = await session.execute(
                select(Classification)
                .where(Classification.message_id == duplicate_message.id)
                .order_by(Classification.created_at.desc())
                .limit(1)
            )
            classification = classification_result.scalar_one_or_none()

            return {
                "status": "duplicate",
                "original_message_id": str(duplicate_message.id),
                "message": "This message was already processed",
                "duplicate_detected_at": datetime.utcnow().isoformat(),
                "original_processed_at": duplicate_message.created_at.isoformat(),
                "response": {
                    "message_id": str(response_message.id) if response_message else None,
                    "text": response_message.content if response_message else None,
                    "type": response_message.message_type.value if response_message else None,
                } if response_message else None,
                "classification": {
                    "id": str(classification.id),
                    "scenario": classification.detected_scenario.value,
                    "confidence": classification.confidence,
                } if classification else None,
            }

        # ============ STEP 3: Process message (within transaction) ============
        try:
            # Process message (text cleaning, classification, escalation)
            # Skip duplicate check since we already checked above
            processed_message = await processing_service.process_message(
                message_data.client_id, message_data.content, skip_duplicate_check=True
            )

            # Create response
            message_response = await response_service.create_response(
                processed_message, message_data.client_id
            )

            # Finalize processing (reminders, mark as processed)
            await response_service.finalize_message_processing(processed_message)

            # Commit transaction
            await session.commit()
            logger.info(f"✅ Transaction committed for {message_data.client_id}")

        except ValueError as e:
            # Handle duplicate message error from processing service
            if "DUPLICATE_MESSAGE" in str(e):
                await session.rollback()
                # Return duplicate response (already handled above, but as fallback)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Duplicate message detected",
                )
            raise
        except Exception as e:
            # Rollback on error
            await session.rollback()
            logger.error(f"❌ Transaction rolled back: {str(e)}")
            raise

        # ============ STEP 4: Schedule delivery in background ============
        # Webhook and WebSocket delivery happens in background tasks
        # This allows API to return immediately without blocking
        delivery_result = delivery_service.schedule_delivery(
            background_tasks,
            processed_message,
            message_response,
        )

        # Prepare response
        classification_data = None
        if processed_message.classification:
            classification_data = {
                "id": str(processed_message.classification.id),
                "scenario": processed_message.scenario,
                "confidence": processed_message.confidence,
                "reasoning": processed_message.classification.reasoning,
            }

        # Determine status
        if not classification_data:
            response_status = "fallback"
        elif processed_message.requires_escalation:
            response_status = "escalated"
        else:
            response_status = "success"

        return {
            "status": response_status,
            "original_message_id": str(processed_message.original_message.id),
            "is_first_message": processed_message.is_first_message,
            "priority": processed_message.priority.value,
            "escalation_reason": (
                processed_message.escalation_reason.value
                if processed_message.escalation_reason
                else None
            ),
            "classification": classification_data,
            "response": {
                "message_id": str(message_response.response_message.id),
                "text": message_response.response_text,
                "type": message_response.response_message.message_type.value,
            },
            "webhook": {
                "success": True,
                "scheduled": True,
                "note": "Webhook delivery scheduled in background",
            },
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
        try:
            await session.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}",
        )


@router.get("/{client_id}", response_model=list[MessageResponse])
async def get_client_messages(
    client_id: str, limit: int = 50, session: AsyncSession = Depends(get_session)
):
    """Get message history for a specific client with eager loading"""
    try:
        # Use eager loading to prevent N+1 queries
        result = await session.execute(
            select(Message)
            .options(selectinload(Message.classifications))
            .where(Message.client_id == client_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()

        logger.info(f"Retrieved {len(messages)} messages for client {client_id}")

        return [
            MessageResponse(
                id=str(m.id),
                client_id=m.client_id,
                content=m.content,
                message_type=MessageTypeEnum(m.message_type.value),
                created_at=m.created_at,
            )
            for m in messages
        ]

    except Exception as e:
        logger.error(f"Error fetching messages for {client_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch messages",
        )


@router.get("/{client_id}/classifications")
async def get_client_classifications(
    client_id: str, session: AsyncSession = Depends(get_session)
):
    """Get classification history for a client"""
    try:
        result = await session.execute(
            select(Classification)
            .join(Message)
            .where(Message.client_id == client_id)
            .order_by(Classification.created_at.desc())
            .limit(50)
        )
        classifications = result.scalars().all()

        return [
            ClassificationResponse(
                id=str(c.id),
                message_id=str(c.message_id),
                detected_scenario=c.detected_scenario,
                confidence=c.confidence,
                ai_model=c.ai_model,
                created_at=c.created_at,
                reasoning=c.reasoning,
            )
            for c in classifications
        ]

    except Exception as e:
        logger.error(f"Error fetching classifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch classifications",
        )


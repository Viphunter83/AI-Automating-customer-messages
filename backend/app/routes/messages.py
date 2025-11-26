from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.schemas import MessageCreate, MessageResponse, ClassificationResponse, MessageTypeEnum
from app.models.database import Message, MessageType, Classification, ScenarioType, Reminder, PriorityLevel, EscalationReason
from app.database import get_session
from app.services.ai_classifier import AIClassifier
from app.services.text_processor import TextProcessor
from app.services.response_manager import ResponseManager
from app.services.webhook_sender import WebhookSender
from app.services.reminder_service import ReminderService, ReminderType
from app.services.dialog_auto_close import DialogAutoCloseService
from app.services.escalation_manager import EscalationManager, EscalationLevel
from app.routes.ws import notify_all_operators
from app.config import get_settings
from uuid import uuid4
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
settings = get_settings()

def get_request_id(request: Request) -> str:
    """Get request ID from request state for correlation"""
    return getattr(request.state, 'request_id', 'no-request-id')

def get_limiter(request: Request) -> Limiter:
    """Get rate limiter from app state"""
    return request.app.state.limiter if hasattr(request.app.state, 'limiter') else None

router = APIRouter(prefix="/api/messages", tags=["messages"])

# Initialize services
text_processor = TextProcessor()
ai_classifier = AIClassifier()
webhook_sender = WebhookSender()

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_webhook_url: Optional[str] = Header(None, alias="X-Webhook-URL"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
):
    """
    Create a new message with rate limiting per client_id.
    
    Rate limits:
    - Per IP: 60/minute, 1000/hour (via slowapi middleware)
    - Per client_id: 10 messages/minute (custom check)
    """
    # Rate limiting is handled by slowapi middleware automatically
    # Additional per-client_id rate limiting is checked below
    """
    Main webhook endpoint for receiving messages from chat platform.
    
    Headers:
        X-Webhook-URL: Optional URL to send response back to
        X-Idempotency-Key: Optional idempotency key to prevent duplicate processing
    
    Flow:
    1. Check for duplicate (idempotency)
    2. Save original message (within transaction)
    3. Clean and process text
    4. Classify using ИИ
    5. Create response (within transaction)
    6. Commit transaction
    7. Send webhook back to platform (after commit)
    8. Return result
    
    Expected JSON:
    {
        "client_id": "client_123",
        "content": "Привет, как работает реферальная программа?"
    }
    """
    # Store webhook result to send after transaction commit
    webhook_result = None
    webhook_data = None
    
    request_id = get_request_id(request)
    try:
        logger.info(
            f"[{request_id}] 📨 Received message from {message_data.client_id}: "
            f"{message_data.content[:50]}..."
        )
        
        # ============ STEP 0.1: Rate limiting per client_id ============
        if settings.rate_limit_enabled:
            # Check rate limit per client_id (custom check)
            one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
            recent_messages_count = await session.execute(
                select(func.count(Message.id))
                .where(
                    Message.client_id == message_data.client_id,
                    Message.created_at >= one_minute_ago
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
                    detail=f"Rate limit exceeded: maximum {settings.rate_limit_message_per_minute} messages per minute per client"
                )
        
        # ============ STEP 0: Check idempotency (before transaction) ============
        # Check for duplicate messages using multiple strategies:
        # 1. Idempotency key (if provided)
        # 2. Same client_id + content within time window (5 seconds)
        
        duplicate_message = None
        
        # Strategy 1: Check by idempotency key (if provided)
        if x_idempotency_key:
            # In a real implementation, you'd have a separate idempotency_keys table
            # For now, we'll check recent messages with same content
            logger.debug(f"Checking idempotency with key: {x_idempotency_key[:8]}...")
        
        # Strategy 2: Check for duplicate content from same client within time window
        time_window_seconds = 5
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window_seconds)
        
        duplicate_check_result = await session.execute(
            select(Message)
            .where(
                Message.client_id == message_data.client_id,
                Message.content == message_data.content,
                Message.created_at >= cutoff_time
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        duplicate_message = duplicate_check_result.scalar_one_or_none()
        
        if duplicate_message:
            logger.warning(
                f"⚠️ Duplicate message detected for client {message_data.client_id}: "
                f"same content within {time_window_seconds} seconds"
            )
            
            # Get the response message for this duplicate
            response_result = await session.execute(
                select(Message)
                .where(
                    Message.client_id == message_data.client_id,
                    Message.message_type.in_([MessageType.BOT_AUTO, MessageType.BOT_ESCALATED]),
                    Message.created_at >= duplicate_message.created_at
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
        
        # ============ START TRANSACTION ============
        # All database operations will be within this transaction
        # Note: session is already managed by get_session dependency,
        # so we use commit() instead of begin()
        try:
            # ============ STEP 1: Check if this is first message from client ============
            # Use SELECT FOR UPDATE to prevent race conditions
            # NOTE: Do NOT use skip_locked=True here - we need to wait for concurrent transactions
            # to complete to get accurate is_first_message check
            existing_messages_result = await session.execute(
                select(Message)
                .where(Message.client_id == message_data.client_id)
                .with_for_update()  # Wait for locks, don't skip - ensures accurate first message check
            )
            existing_messages = existing_messages_result.scalars().all()
            is_first_message = len(existing_messages) == 0
            
            # Update dialog activity (within transaction)
            dialog_service = DialogAutoCloseService(session)
            await dialog_service.update_activity(message_data.client_id)
            
            # ============ STEP 2: Save original message ============
            original_message = Message(
                id=uuid4(),
                client_id=message_data.client_id,
                content=message_data.content,
                message_type=MessageType.USER,
                is_processed=False,
                is_first_message=is_first_message,
            )
            session.add(original_message)
            await session.flush()
            logger.debug(f"✅ Saved original message: {original_message.id} (first_message={is_first_message})")
            
            # ============ STEP 3: Process text ============
            processed_text = text_processor.process(message_data.content)
            logger.debug(f"📝 Processed text: {processed_text}")
            
            if not processed_text:
                logger.warning("Processed text is empty (noise detected)")
                response_msg, response_text = await ResponseManager(session).create_fallback_response(
                    message_data.client_id,
                    reason="empty_text"
                )
                
                # Store webhook data to send after commit
                if response_msg:
                    webhook_data = {
                        "client_id": message_data.client_id,
                        "response_text": response_text,
                        "message_id": str(response_msg.id),
                        "classification": None,
                        "requires_escalation": False,
                        "response_data": {
                            "original_message_id": str(original_message.id),
                            "response_message_id": str(response_msg.id) if response_msg else None,
                            "response_text": response_text,
                            "response_type": response_msg.message_type.value if response_msg else "unknown",
                            "is_first_message": is_first_message,
                            "priority": "low",
                            "escalation_reason": None,
                        },
                    }
                else:
                    webhook_data = None
                
                # Commit transaction before early return
                await session.commit()
                # Continue to webhook sending after transaction
            
            # ============ STEP 4: Classify using ИИ ============
            # AI call is outside transaction (external service)
            classification_result = await ai_classifier.classify(
                message=processed_text,
                client_id=message_data.client_id
            )
            
            if not classification_result.get("success"):
                logger.error(f"❌ Classification failed: {classification_result.get('error')}")
                response_msg, response_text = await ResponseManager(session).create_fallback_response(
                    message_data.client_id,
                    reason="classification_error"
                )
                
                # Store webhook data
                if response_msg:
                    webhook_data = {
                        "client_id": message_data.client_id,
                        "response_text": response_text,
                        "message_id": str(response_msg.id),
                        "classification": None,
                        "requires_escalation": False,
                        "response_data": {
                            "original_message_id": str(original_message.id),
                            "response_message_id": str(response_msg.id) if response_msg else None,
                            "response_text": response_text,
                            "response_type": response_msg.message_type.value if response_msg else "unknown",
                            "is_first_message": is_first_message,
                            "priority": "low",
                            "escalation_reason": None,
                        },
                    }
                else:
                    webhook_data = None
                
                # Commit transaction before early return
                await session.commit()
                # Continue to webhook sending after transaction
            
            scenario = classification_result.get("scenario")
            confidence = classification_result.get("confidence")
            
            logger.info(f"🤖 Classification: {scenario} (confidence: {confidence:.2f})")
            
            # ============ STEP 5: Save classification ============
            classification = Classification(
                id=uuid4(),
                message_id=original_message.id,
                detected_scenario=ScenarioType[scenario],
                confidence=confidence,
                ai_model=classification_result.get("model"),
                reasoning=classification_result.get("reasoning"),
            )
            session.add(classification)
            await session.flush()
            logger.debug(f"✅ Saved classification: {classification.id}")
            
            # ============ STEP 6: Evaluate escalation and priority ============
            escalation_manager = EscalationManager(session)
            escalation_result = await escalation_manager.evaluate_escalation(
                message_id=str(original_message.id),
                scenario=scenario,
                confidence=confidence,
                client_id=message_data.client_id
            )
            
            # Determine if escalation is required
            escalation_scenarios = [
                "SCHEDULE_CHANGE", "COMPLAINT", "MISSING_TRAINER", 
                "CROSS_EXTENSION", "UNKNOWN"
            ]
            requires_escalation = (
                scenario in escalation_scenarios or
                (scenario == "REFERRAL" and any(char.isdigit() for char in message_data.content)) or
                escalation_result.get("should_escalate", False)
            )
            
            # Set priority and escalation reason with validation
            priority_level_str = escalation_result.get("level", "low")
            try:
                # Validate priority level before creating enum
                priority_level = PriorityLevel(priority_level_str)
            except ValueError:
                logger.warning(
                    f"Invalid priority level '{priority_level_str}' from escalation manager, "
                    f"defaulting to 'low'"
                )
                priority_level = PriorityLevel.LOW
            
            escalation_reason = None
            reasons = escalation_result.get("reasons")
            if reasons and isinstance(reasons, list) and len(reasons) > 0:
                try:
                    # Validate escalation reason before creating enum
                    escalation_reason = EscalationReason(reasons[0])
                except (ValueError, IndexError) as e:
                    logger.warning(
                        f"Invalid escalation reason '{reasons[0] if reasons else None}': {e}, "
                        f"skipping escalation reason"
                    )
                    escalation_reason = None
            
            original_message.priority = PriorityLevel(priority_level.value)
            original_message.escalation_reason = escalation_reason
            await session.flush()
            logger.debug(f"✅ Set priority: {priority_level.value}, escalation_reason: {escalation_reason.value if escalation_reason else None}")
            
            # ============ STEP 7: Create response ============
            response_manager = ResponseManager(session)
            response_msg, response_text = await response_manager.create_bot_response(
                scenario=scenario,
                client_id=message_data.client_id,
                original_message_id=str(original_message.id),
                params={"referral_link": f"https://example.com/ref/{message_data.client_id}"},
                message_type=MessageType.BOT_ESCALATED if requires_escalation else MessageType.BOT_AUTO
            )
            
            if not response_msg:
                logger.error(f"❌ Failed to create response: {response_text}")
                response_msg, response_text = await response_manager.create_fallback_response(
                    message_data.client_id,
                    reason="response_creation_error"
                )
            
            if not response_msg:
                logger.error(f"❌ Fallback response also failed: {response_text}")
                # Transaction will rollback automatically on exception
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create bot response after fallback"
                )
            
            logger.info(f"✅ Created response: {response_msg.id}")
            
            # Store webhook data and response data for sending after commit
            webhook_data = {
                "client_id": message_data.client_id,
                "response_text": response_text,
                "message_id": str(response_msg.id),
                "classification": {
                    "scenario": scenario,
                    "confidence": confidence,
                    "id": str(classification.id),
                    "reasoning": classification_result.get("reasoning"),
                },
                "requires_escalation": requires_escalation,
                "escalation_data": {
                    "priority": priority_level.value,
                    "escalation_reason": escalation_reason.value if escalation_reason else None,
                    "is_first_message": is_first_message,
                    "priority_queue": escalation_result.get("priority_queue", 10),
                } if requires_escalation else None,
                "response_data": {
                    "original_message_id": str(original_message.id),
                    "response_message_id": str(response_msg.id),
                    "response_text": response_text,
                    "response_type": response_msg.message_type.value,
                    "is_first_message": is_first_message,
                    "priority": priority_level.value,
                    "escalation_reason": escalation_reason.value if escalation_reason else None,
                },
            }
            
            # ============ STEP 8: Create reminders if needed ============
            reminder_service = ReminderService(session)
            
            if not requires_escalation and scenario not in ["FAREWELL", "UNKNOWN"]:
                await reminder_service.create_reminder(
                    client_id=message_data.client_id,
                    message_id=str(original_message.id),
                    reminder_type=ReminderType.REMINDER_15MIN
                )
                
                await reminder_service.create_reminder(
                    client_id=message_data.client_id,
                    message_id=str(original_message.id),
                    reminder_type=ReminderType.REMINDER_30MIN
                )
                
                logger.debug(f"Created reminders for message {original_message.id}")
            
            # Cancel pending reminders for messages created after this one
            # Pass the current message ID to only cancel reminders for future messages
            # This prevents cancelling reminders that should be kept
            cancelled = await reminder_service.cancel_client_reminders(
                client_id=message_data.client_id,
                after_message_id=str(original_message.id)  # Only cancel reminders for messages after this one
            )
            if cancelled > 0:
                logger.debug(f"Cancelled {cancelled} pending reminders for {message_data.client_id}")
            
            # ============ STEP 9: Mark original as processed ============
            original_message.is_processed = True
            
            # Commit transaction
            await session.commit()
            logger.info(f"✅ Transaction committed for {message_data.client_id}")
            
        except Exception as e:
            # Rollback on error
            await session.rollback()
            logger.error(f"❌ Transaction rolled back: {str(e)}")
            raise
        
        # ============ AFTER TRANSACTION: Send webhook ============
        # Webhook is sent AFTER transaction commit to ensure data consistency
        if webhook_data:
            try:
                webhook_sender_instance = WebhookSender(platform_webhook_url=x_webhook_url) if x_webhook_url else webhook_sender
                webhook_result = await webhook_sender_instance.send_response(
                    client_id=webhook_data["client_id"],
                    response_text=webhook_data["response_text"],
                    message_id=webhook_data["message_id"],
                    classification=webhook_data.get("classification"),
                )
                logger.info(f"📤 Webhook send result: {webhook_result}")
            except Exception as webhook_error:
                logger.error(f"❌ Webhook send failed (non-critical): {str(webhook_error)}")
                webhook_result = {
                    "success": False,
                    "error": str(webhook_error),
                    "note": "Message was saved successfully, but webhook failed"
                }
        else:
            webhook_result = {"success": False, "reason": "no_response_created"}
        
        # ============ AFTER TRANSACTION: Notify operators via WebSocket ============
        if webhook_data and webhook_data.get("requires_escalation"):
            try:
                escalation_data = webhook_data.get("escalation_data")
                if escalation_data:
                    await notify_all_operators({
                        "type": "escalation",
                        "client_id": webhook_data["client_id"],
                        "message": f"New escalation from {webhook_data['client_id']}",
                        "scenario": webhook_data.get("classification", {}).get("scenario", "UNKNOWN"),
                        "priority": escalation_data.get("priority", "low"),
                        "priority_queue": escalation_data.get("priority_queue", 10),
                        "escalation_reason": escalation_data.get("escalation_reason"),
                        "is_first_message": escalation_data.get("is_first_message", False),
                    })
            except Exception as ws_error:
                logger.error(f"❌ WebSocket notification failed (non-critical): {str(ws_error)}")
        
        # Prepare response
        if not webhook_data:
            # This shouldn't happen, but handle gracefully
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process message: webhook_data not set"
            )
        
        response_data = webhook_data.get("response_data", {})
        classification_data = webhook_data.get("classification", {})
        
        # Determine status based on response type
        if not classification_data:
            response_status = "fallback"
        elif webhook_data.get("requires_escalation"):
            response_status = "escalated"
        else:
            response_status = "success"
        
        return {
            "status": response_status,
            "original_message_id": response_data.get("original_message_id"),
            "is_first_message": response_data.get("is_first_message", False),
            "priority": response_data.get("priority", "low"),
            "escalation_reason": response_data.get("escalation_reason"),
            "classification": classification_data if classification_data else None,
            "response": {
                "message_id": response_data.get("response_message_id"),
                "text": response_data.get("response_text", ""),
                "type": response_data.get("response_type", "unknown"),
            },
            "webhook": webhook_result
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
        # Session rollback is handled by the context manager if transaction was started
        # But we need to ensure rollback if transaction wasn't started
        try:
            await session.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@router.get("/{client_id}", response_model=list[MessageResponse])
async def get_client_messages(
    client_id: str,
    limit: int = 50,
    session: AsyncSession = Depends(get_session)
):
    """Get message history for a specific client with eager loading"""
    try:
        # Use eager loading to prevent N+1 queries if classifications are needed later
        result = await session.execute(
            select(Message)
            .options(selectinload(Message.classifications))  # Eager load classifications
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
            detail="Failed to fetch messages"
        )

@router.get("/{client_id}/classifications")
async def get_client_classifications(
    client_id: str,
    session: AsyncSession = Depends(get_session)
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
            detail="Failed to fetch classifications"
        )

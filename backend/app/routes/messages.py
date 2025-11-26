from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.schemas import MessageCreate, MessageResponse, ClassificationResponse, MessageTypeEnum
from app.models.database import Message, MessageType, Classification, ScenarioType
from app.database import get_session
from app.services.ai_classifier import AIClassifier
from app.services.text_processor import TextProcessor
from app.services.response_manager import ResponseManager
from app.services.webhook_sender import WebhookSender
from app.routes.ws import notify_all_operators
from uuid import uuid4
import logging
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])

# Initialize services
text_processor = TextProcessor()
ai_classifier = AIClassifier()
webhook_sender = WebhookSender()

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    session: AsyncSession = Depends(get_session),
    x_webhook_url: Optional[str] = Header(None, alias="X-Webhook-URL"),
):
    """
    Main webhook endpoint for receiving messages from chat platform.
    
    Headers:
        X-Webhook-URL: Optional URL to send response back to
    
    Flow:
    1. Save original message
    2. Clean and process text
    3. Classify using ИИ
    4. Create response
    5. Send webhook back to platform
    6. Return result
    
    Expected JSON:
    {
        "client_id": "client_123",
        "content": "Привет, как работает реферальная программа?"
    }
    """
    try:
        logger.info(f"📨 Received message from {message_data.client_id}: {message_data.content[:50]}...")
        
        # ============ STEP 1: Save original message ============
        original_message = Message(
            id=uuid4(),
            client_id=message_data.client_id,
            content=message_data.content,
            message_type=MessageType.USER,
            is_processed=False,
        )
        session.add(original_message)
        await session.flush()
        logger.debug(f"✅ Saved original message: {original_message.id}")
        
        # ============ STEP 2: Process text ============
        processed_text = text_processor.process(message_data.content)
        logger.debug(f"📝 Processed text: {processed_text}")
        
        if not processed_text:
            logger.warning("Processed text is empty (noise detected)")
            response_msg, response_text = await ResponseManager(session).create_fallback_response(
                message_data.client_id,
                reason="empty_text"
            )
            
            # Send to webhook
            webhook_result = None
            if response_msg:
                webhook_sender_instance = WebhookSender(platform_webhook_url=x_webhook_url) if x_webhook_url else webhook_sender
                webhook_result = await webhook_sender_instance.send_response(
                    client_id=message_data.client_id,
                    response_text=response_text,
                    message_id=str(response_msg.id),
                )
            
            await session.commit()
            return {
                "status": "fallback",
                "original_message_id": str(original_message.id),
                "response_message_id": str(response_msg.id) if response_msg else None,
                "response_text": response_text,
                "reason": "Message is empty or noise",
                "webhook": webhook_result or {"success": False, "reason": "no_response_created"},
            }
        
        # ============ STEP 3: Classify using ИИ ============
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
            
            # Send to webhook
            webhook_result = None
            if response_msg:
                webhook_sender_instance = WebhookSender(platform_webhook_url=x_webhook_url) if x_webhook_url else webhook_sender
                webhook_result = await webhook_sender_instance.send_response(
                    client_id=message_data.client_id,
                    response_text=response_text,
                    message_id=str(response_msg.id),
                )
            
            await session.commit()
            return {
                "status": "fallback",
                "original_message_id": str(original_message.id),
                "response_message_id": str(response_msg.id) if response_msg else None,
                "response_text": response_text,
                "reason": "Classification error",
                "webhook": webhook_result or {"success": False, "reason": "no_response_created"},
            }
        
        scenario = classification_result.get("scenario")
        confidence = classification_result.get("confidence")
        
        logger.info(f"🤖 Classification: {scenario} (confidence: {confidence:.2f})")
        
        # ============ STEP 4: Save classification ============
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
        
        # ============ STEP 5: Create response ============
        response_manager = ResponseManager(session)
        response_msg, response_text = await response_manager.create_bot_response(
            scenario=scenario,
            client_id=message_data.client_id,
            original_message_id=str(original_message.id),
            params={"referral_link": f"https://example.com/ref/{message_data.client_id}"},
            message_type=MessageType.BOT_AUTO if scenario != "UNKNOWN" else MessageType.BOT_ESCALATED
        )
        
        if not response_msg:
            logger.error(f"❌ Failed to create response: {response_text}")
            # Fallback to UNKNOWN
            response_msg, response_text = await response_manager.create_fallback_response(
                message_data.client_id,
                reason="response_creation_error"
            )
        
        # Final check: if still None, return error response
        if not response_msg:
            logger.error(f"❌ Fallback response also failed: {response_text}")
            await session.commit()
            return {
                "status": "error",
                "original_message_id": str(original_message.id),
                "classification": {
                    "id": str(classification.id),
                    "scenario": scenario,
                    "confidence": confidence,
                    "reasoning": classification_result.get("reasoning"),
                },
                "response": {
                    "message_id": None,
                    "text": response_text or "Failed to create response",
                    "type": "error",
                },
                "error": "Failed to create bot response after fallback"
            }
        
        logger.info(f"✅ Created response: {response_msg.id if response_msg else 'None'}")
        
        # ============ STEP 6: Send to webhook ============
        webhook_result = None
        if response_msg:
            webhook_sender_instance = WebhookSender(platform_webhook_url=x_webhook_url) if x_webhook_url else webhook_sender
            webhook_result = await webhook_sender_instance.send_response(
                client_id=message_data.client_id,
                response_text=response_text,
                message_id=str(response_msg.id),
                classification={
                    "scenario": scenario,
                    "confidence": confidence,
                }
            )
            logger.info(f"📤 Webhook send result: {webhook_result}")
        
        # ============ STEP 7: Notify operators via WebSocket ============
        if scenario == "UNKNOWN":
            await notify_all_operators({
                "type": "escalation",
                "client_id": message_data.client_id,
                "message": f"New escalation from {message_data.client_id}",
                "scenario": scenario,
            })
        
        # ============ STEP 8: Mark original as processed ============
        original_message.is_processed = True
        await session.commit()
        
        logger.info(f"✅ Complete processing for {message_data.client_id}")
        
        return {
            "status": "success" if scenario != "UNKNOWN" else "escalated",
            "original_message_id": str(original_message.id),
            "classification": {
                "id": str(classification.id),
                "scenario": scenario,
                "confidence": confidence,
                "reasoning": classification_result.get("reasoning"),
            },
            "response": {
                "message_id": str(response_msg.id) if response_msg else None,
                "text": response_text,
                "type": response_msg.message_type.value if response_msg else "unknown",
            },
            "webhook": webhook_result or {"success": False, "reason": "no_webhook_configured"}
        }
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
        await session.rollback()
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
    """Get message history for a specific client"""
    try:
        result = await session.execute(
            select(Message)
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

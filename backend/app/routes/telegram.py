"""
Telegram Integration Routes
Webhook endpoint for receiving Telegram updates
"""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from telegram import Update
from telegram.error import TelegramError

from app.config import get_settings
from app.integrations.telegram.bot import TelegramBot

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/integrations/telegram", tags=["telegram"])

# Global bot instance (will be initialized on startup)
_telegram_bot: Optional[TelegramBot] = None


def get_telegram_bot() -> Optional[TelegramBot]:
    """Get global Telegram bot instance"""
    return _telegram_bot


def set_telegram_bot(bot: TelegramBot):
    """Set global Telegram bot instance"""
    global _telegram_bot
    _telegram_bot = _telegram_bot or bot


@router.post("/webhook")
async def telegram_webhook(
    update: dict,
    request: Request,
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: Optional[str] = Header(
        None, alias="X-Telegram-Bot-Api-Secret-Token"
    ),
):
    """
    Webhook endpoint for receiving Telegram updates
    
    This endpoint receives updates from Telegram and processes them asynchronously.
    """
    if not settings.telegram_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram integration is disabled",
        )
    
    bot = get_telegram_bot()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot is not initialized",
        )
    
    # Validate secret token if configured
    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            logger.warning("Invalid webhook secret token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid secret token",
            )
    
    try:
        # Parse Telegram Update
        telegram_update = Update.de_json(update, bot.bot)
        
        if not telegram_update:
            logger.warning("Invalid Telegram update received")
            return {"ok": False, "error": "Invalid update"}
        
        # Process update in background
        background_tasks.add_task(
            bot.application.process_update,
            telegram_update,
        )
        
        logger.debug(f"✅ Telegram webhook received: update_id={telegram_update.update_id}")
        return {"ok": True}
        
    except TelegramError as e:
        logger.error(f"❌ Telegram error processing webhook: {str(e)}")
        return {"ok": False, "error": str(e)}
    except Exception as e:
        logger.error(
            f"❌ Unexpected error processing Telegram webhook: {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        return {"ok": False, "error": "Internal server error"}


@router.post("/response")
async def telegram_response_webhook(
    response_data: dict,
    request: Request,
    x_chat_id: Optional[str] = Header(None, alias="X-Chat-ID"),
):
    """
    Internal webhook endpoint for sending responses back to Telegram
    
    This is called by MessageDeliveryService to send responses to Telegram users.
    
    Implements idempotency check to prevent duplicate message delivery.
    """
    if not settings.telegram_enabled:
        logger.warning("Telegram response received but integration is disabled")
        return {"ok": False, "error": "Telegram integration disabled"}
    
    bot = get_telegram_bot()
    if not bot:
        logger.error("Telegram bot not initialized")
        return {"ok": False, "error": "Bot not initialized"}
    
    try:
        message_id = response_data.get("message_id")
        
        # Check if message was already sent (idempotency check)
        if message_id:
            try:
                from app.utils.redis_cache import get_redis_cache
                redis_cache = await get_redis_cache()
                
                # Check if this message was already sent
                sent_key = f"telegram_sent:{message_id}"
                already_sent = await redis_cache.get(sent_key)
                
                if already_sent:
                    logger.info(
                        f"Message {message_id} already sent to Telegram, skipping duplicate delivery"
                    )
                    # Increment duplicate counter for monitoring
                    try:
                        duplicate_key = "metrics:telegram_duplicates"
                        current_count = await redis_cache.get(duplicate_key)
                        count = int(current_count) if current_count else 0
                        await redis_cache.set(duplicate_key, str(count + 1), ttl_seconds=86400)  # 24h TTL
                    except Exception as e:
                        logger.debug(f"Failed to increment duplicate counter: {e}")
                    
                    return {
                        "ok": True,
                        "success": True,
                        "skipped": True,
                        "reason": "already_sent",
                        "telegram_message_id": already_sent if isinstance(already_sent, str) else str(already_sent),
                    }
            except Exception as e:
                logger.warning(f"Failed to check idempotency for message {message_id}: {e}, continuing with send")
        
        # Get chat_id from header (set by bot when calling /api/messages/)
        # If not in header, try to extract from client_id format "telegram_123456"
        chat_id = x_chat_id
        
        if not chat_id:
            # Try to extract from client_id
            client_id = response_data.get("client_id", "")
            if client_id.startswith("telegram_"):
                # Extract numeric part: "telegram_123456" -> "123456"
                try:
                    chat_id = client_id.replace("telegram_", "")
                except Exception:
                    pass
        
        if not chat_id:
            logger.error("No chat_id in response data or header")
            return {"ok": False, "error": "Missing chat_id"}
        
        try:
            chat_id_int = int(chat_id)
        except ValueError:
            logger.error(f"Invalid chat_id format: {chat_id}")
            return {"ok": False, "error": f"Invalid chat_id format: {chat_id}"}
        response_text = response_data.get("response_text") or response_data.get("text", "")
        
        if not response_text:
            logger.warning("No response text provided")
            return {"ok": False, "error": "Missing response_text"}
        
        # Send response to Telegram
        result = await bot.sender.send_response(
            chat_id=chat_id_int,
            response_text=response_text,
            message_id=message_id,
        )
        
        # Mark as sent after successful delivery (idempotency)
        if result.get("success") and message_id:
            try:
                from app.utils.redis_cache import get_redis_cache
                redis_cache = await get_redis_cache()
                sent_key = f"telegram_sent:{message_id}"
                telegram_msg_id = result.get("telegram_message_id", "sent")
                # Store Telegram message ID for reference, TTL 1 hour
                await redis_cache.set(sent_key, str(telegram_msg_id), ttl_seconds=3600)
                logger.debug(f"Marked message {message_id} as sent to Telegram")
            except Exception as e:
                logger.warning(f"Failed to mark message {message_id} as sent: {e}")
        
        return {"ok": result["success"], **result}
        
    except ValueError as e:
        logger.error(f"Invalid chat_id format: {e}")
        return {"ok": False, "error": f"Invalid chat_id: {str(e)}"}
    except Exception as e:
        logger.error(
            f"❌ Error sending Telegram response: {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        return {"ok": False, "error": str(e)}


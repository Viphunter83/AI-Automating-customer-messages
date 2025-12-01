"""
Telegram Bot
Main bot class for handling Telegram messages
"""
import logging
import os
from typing import Optional

import httpx
from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import get_settings
from app.integrations.telegram.adapter import (
    extract_telegram_info,
    telegram_to_message,
)
from app.integrations.telegram.handlers import help_command, start_command
from app.integrations.telegram.sender import TelegramResponseSender

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramBot:
    """Telegram bot for testing the system"""
    
    def __init__(self, token: str):
        """
        Initialize Telegram bot
        
        Args:
            token: Telegram bot token
        """
        self.token = token
        self.bot = Bot(token=token)
        self.application = Application.builder().token(token).build()
        self.sender = TelegramResponseSender(self.bot)
        # Determine API URL: use internal Docker service name or localhost
        # In Docker, backend service is accessible as "backend:8000"
        # For local development, use "localhost:8000"
        docker_env = os.getenv("DOCKER_ENV", "false").lower() == "true"
        self.api_base_url = "http://backend:8000" if docker_env else "http://localhost:8000"
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        
        # Message handler (text messages and media)
        # Handle text messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        # Handle media messages (photos, documents, videos)
        # Note: In python-telegram-bot 20.7, use filters.Document.ALL for documents
        self.application.add_handler(
            MessageHandler(
                (filters.PHOTO | filters.Document.ALL | filters.VIDEO) & ~filters.COMMAND,
                self.handle_message
            )
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle incoming text message
        
        Args:
            update: Telegram Update object
            context: Context object
        """
        chat_id = None
        try:
            # Convert Telegram message to system format
            message_data = telegram_to_message(update)
            if not message_data:
                logger.debug("Skipping invalid message")
                return
            
            # Extract Telegram info for response
            telegram_info = extract_telegram_info(update)
            chat_id = telegram_info.get("chat_id")
            
            if not chat_id:
                logger.error("No chat_id in Telegram update")
                return
            
            logger.info(
                f"📨 Received Telegram message from user {telegram_info.get('user_id')}: "
                f"{message_data.content[:50]}..."
            )
            
            # Call system API to process message
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create webhook URL for Telegram response
                # Use localhost for webhook (accessible from host machine)
                # API call uses internal Docker service name if in Docker
                webhook_base = os.getenv("TELEGRAM_WEBHOOK_BASE_URL", "http://localhost:8000")
                webhook_url = f"{webhook_base}/api/integrations/telegram/response"
                
                # Serialize message data for JSON (convert datetime to ISO format)
                message_dict = message_data.model_dump(mode='json')
                
                response = await client.post(
                    f"{self.api_base_url}/api/messages/",
                    json=message_dict,
                    headers={
                        "X-Webhook-URL": webhook_url,
                        "X-Platform": "telegram",
                        "X-Chat-ID": str(chat_id),
                    },
                )
                
                if response.status_code == 201:
                    result = response.json()
                    logger.info(
                        f"✅ Message processed successfully: {result.get('status')}. "
                        f"Response will be sent via webhook by MessageDeliveryService"
                    )
                    # Response is sent via webhook by MessageDeliveryService in background
                    # No need to send directly here to avoid duplication
                else:
                    error_msg = f"API returned {response.status_code}: {response.text[:200]}"
                    logger.error(f"❌ API error: {error_msg}")
                    if chat_id:
                        await self.sender.send_response(
                            chat_id=chat_id,
                            response_text="Произошла ошибка при обработке сообщения. Попробуйте позже.",
                        )
                    
        except httpx.TimeoutException as e:
            logger.error(f"❌ API timeout: {str(e)}")
            if chat_id:
                await self.sender.send_response(
                    chat_id=chat_id,
                    response_text="Превышено время ожидания. Попробуйте позже.",
                )
        except Exception as e:
            logger.error(
                f"❌ Unexpected error handling message: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            if chat_id:
                try:
                    await self.sender.send_response(
                        chat_id=chat_id,
                        response_text="Произошла непредвиденная ошибка. Попробуйте позже.",
                    )
                except Exception as send_error:
                    logger.error(f"Failed to send error message to Telegram: {send_error}")
    
    async def start_polling(self):
        """Start bot in polling mode (for development)"""
        logger.info("🤖 Starting Telegram bot in polling mode...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("✅ Telegram bot started (polling mode)")
    
    async def stop_polling(self):
        """Stop bot polling"""
        logger.info("🛑 Stopping Telegram bot...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info("✅ Telegram bot stopped")
    
    def setup_webhook(self, webhook_url: str, secret_token: Optional[str] = None):
        """
        Setup webhook for production
        
        Args:
            webhook_url: Webhook URL
            secret_token: Secret token for webhook validation
        """
        self.application.bot.set_webhook(
            url=webhook_url,
            secret_token=secret_token,
        )
        logger.info(f"✅ Webhook set up: {webhook_url}")


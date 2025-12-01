"""
Telegram Response Sender
Sends responses back to Telegram users
"""
import logging
from typing import Dict, Optional

from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramResponseSender:
    """Send responses to Telegram users"""
    
    def __init__(self, bot: Bot):
        """
        Initialize Telegram Response Sender
        
        Args:
            bot: Telegram Bot instance
        """
        self.bot = bot
    
    async def send_response(
        self,
        chat_id: int,
        response_text: str,
        message_id: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Send response message to Telegram user
        
        Args:
            chat_id: Telegram chat ID
            response_text: Text to send
            message_id: System message ID (for tracking)
            
        Returns:
            Dict with success status and Telegram message ID
        """
        try:
            # Send message to Telegram
            sent_message = await self.bot.send_message(
                chat_id=chat_id,
                text=response_text,
            )
            
            logger.info(
                f"✅ Sent Telegram response to chat {chat_id}, "
                f"message_id={sent_message.message_id}, "
                f"system_message_id={message_id}"
            )
            
            return {
                "success": True,
                "telegram_message_id": sent_message.message_id,
                "chat_id": chat_id,
                "error": None,
            }
            
        except TelegramError as e:
            logger.error(
                f"❌ Telegram send error for chat {chat_id}: {str(e)}"
            )
            return {
                "success": False,
                "telegram_message_id": None,
                "chat_id": chat_id,
                "error": str(e),
            }
        except Exception as e:
            logger.error(
                f"❌ Unexpected error sending to Telegram chat {chat_id}: "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            return {
                "success": False,
                "telegram_message_id": None,
                "chat_id": chat_id,
                "error": f"Unexpected error: {str(e)}",
            }


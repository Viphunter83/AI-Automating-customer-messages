"""
Telegram Adapter
Converts between Telegram format and system format
"""
import logging
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.constants import ChatType

from app.models.schemas import MessageCreate

logger = logging.getLogger(__name__)


def telegram_to_message(update: Update) -> Optional[MessageCreate]:
    """
    Convert Telegram Update to MessageCreate
    
    Args:
        update: Telegram Update object
        
    Returns:
        MessageCreate object or None if message is invalid
    """
    if not update.message:
        return None
    
    message = update.message
    
    # Skip group chats (only handle private messages)
    if message.chat.type != ChatType.PRIVATE:
        logger.debug(f"Skipping non-private chat: {message.chat.type}")
        return None
    
    # Extract user info
    user = message.from_user
    if not user:
        logger.warning("Message has no user info")
        return None
    
    # Create client_id from Telegram user ID
    client_id = f"telegram_{user.id}"
    
    # Convert timestamp
    # message.date is already a datetime object in python-telegram-bot 20.7
    if message.date:
        if isinstance(message.date, datetime):
            timestamp = message.date
        else:
            # Fallback for older versions or if it's a timestamp
            timestamp = datetime.fromtimestamp(message.date)
    else:
        timestamp = datetime.utcnow()
    
    # Handle text messages
    if message.text:
        return MessageCreate(
            client_id=client_id,
            content=message.text,
            timestamp=timestamp,
        )
    
    # Handle media messages (photos, documents, etc.)
    content_parts = []
    has_media = False
    
    # Check for photo
    if message.photo:
        has_media = True
        photo = message.photo[-1]  # Get largest photo
        file_id = photo.file_id
        content_parts.append(f"[ФОТО получено, file_id: {file_id}]")
        if message.caption:
            content_parts.append(f"Подпись: {message.caption}")
        logger.info(f"Received photo from user {user.id}, file_id: {file_id}")
    
    # Check for document
    elif message.document:
        has_media = True
        doc = message.document
        file_id = doc.file_id
        file_name = doc.file_name or "документ"
        content_parts.append(f"[ДОКУМЕНТ получен: {file_name}, file_id: {file_id}]")
        if message.caption:
            content_parts.append(f"Подпись: {message.caption}")
        logger.info(f"Received document from user {user.id}, file: {file_name}, file_id: {file_id}")
    
    # Check for video
    elif message.video:
        has_media = True
        video = message.video
        file_id = video.file_id
        content_parts.append(f"[ВИДЕО получено, file_id: {file_id}]")
        if message.caption:
            content_parts.append(f"Подпись: {message.caption}")
        logger.info(f"Received video from user {user.id}, file_id: {file_id}")
    
    if has_media:
        # Combine all content parts
        content = "\n".join(content_parts) if content_parts else "[Медиа-файл получен]"
        return MessageCreate(
            client_id=client_id,
            content=content,
            timestamp=timestamp,
        )
    
    # Skip other message types (stickers, voice, etc.)
    logger.debug(f"Skipping unsupported message type: {message.message_id}")
    return None


def extract_telegram_info(update: Update) -> dict:
    """
    Extract Telegram-specific information from update
    
    Returns:
        Dict with chat_id, user_id, message_id, etc.
    """
    if not update.message:
        return {}
    
    message = update.message
    user = message.from_user
    
    return {
        "chat_id": message.chat.id,
        "user_id": user.id if user else None,
        "username": user.username if user else None,
        "first_name": user.first_name if user else None,
        "last_name": user.last_name if user else None,
        "message_id": message.message_id,
        "is_bot": user.is_bot if user else False,
    }


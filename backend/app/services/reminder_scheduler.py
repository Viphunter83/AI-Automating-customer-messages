import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session_maker
from app.services.reminder_service import ReminderService
from app.services.response_manager import ResponseManager
from app.services.webhook_sender import WebhookSender
from app.models.database import Message, MessageType, ReminderType, Reminder
from app.config import get_settings
import uuid

logger = logging.getLogger(__name__)

class ReminderScheduler:
    """Scheduler for sending reminders to clients"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.webhook_sender = WebhookSender()
        self.settings = get_settings()
    
    async def send_reminder(self, reminder_id: str, client_id: str, message_id: str):
        """
        Send a reminder message to a client
        
        Args:
            reminder_id: ID of the reminder
            client_id: Client ID
            message_id: ID of the original message
        """
        async with async_session_maker() as session:
            try:
                reminder_service = ReminderService(session)
                response_manager = ResponseManager(session)
                
                # Check if reminder still exists and is not cancelled
                result = await session.execute(
                    select(Reminder).where(Reminder.id == uuid.UUID(reminder_id))
                )
                reminder = result.scalar_one_or_none()
                
                if not reminder or reminder.is_cancelled or reminder.sent_at:
                    logger.debug(f"Reminder {reminder_id} already processed or cancelled")
                    return
                
                # Check if client has responded since reminder was created
                # If they have, cancel the reminder
                result = await session.execute(
                    select(Message).where(
                        Message.client_id == client_id,
                        Message.created_at > reminder.created_at,
                        Message.message_type == MessageType.USER
                    ).order_by(Message.created_at.desc()).limit(1)
                )
                recent_message = result.scalar_one_or_none()
                
                if recent_message:
                    logger.info(
                        f"Client {client_id} responded, cancelling reminder {reminder_id}"
                    )
                    await reminder_service.cancel_client_reminders(client_id)
                    await session.commit()
                    return
                
                # Create reminder response message
                response_msg, response_text = await response_manager.create_bot_response(
                    scenario="REMINDER",
                    client_id=client_id,
                    original_message_id=message_id,
                    message_type=MessageType.BOT_AUTO
                )
                
                if not response_msg:
                    logger.error(f"Failed to create reminder response for {client_id}")
                    return
                
                # Send via webhook
                webhook_result = await self.webhook_sender.send_response(
                    client_id=client_id,
                    response_text=response_text,
                    message_id=str(response_msg.id),
                    classification={"scenario": "REMINDER", "confidence": 1.0}
                )
                
                # Mark reminder as sent
                await reminder_service.mark_reminder_sent(reminder_id)
                await session.commit()
                
                logger.info(
                    f"Sent reminder {reminder_id} to client {client_id}, "
                    f"webhook_result={webhook_result.get('success', False)}"
                )
                
            except Exception as e:
                logger.error(
                    f"Error sending reminder {reminder_id}: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
    
    async def process_pending_reminders(self):
        """Process all pending reminders"""
        async with async_session_maker() as session:
            try:
                reminder_service = ReminderService(session)
                pending_reminders = await reminder_service.get_pending_reminders(limit=50)
                
                if not pending_reminders:
                    logger.debug("No pending reminders to process")
                    return
                
                logger.info(f"Processing {len(pending_reminders)} pending reminders")
                
                for reminder in pending_reminders:
                    await self.send_reminder(
                        str(reminder.id),
                        reminder.client_id,
                        str(reminder.message_id)
                    )
                
            except Exception as e:
                logger.error(
                    f"Error processing pending reminders: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
    
    def start(self):
        """Start the reminder scheduler"""
        # Run every minute to check for pending reminders
        self.scheduler.add_job(
            self.process_pending_reminders,
            trigger=IntervalTrigger(minutes=1),
            id="process_reminders",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("✅ Reminder scheduler started")
    
    def stop(self):
        """Stop the reminder scheduler"""
        self.scheduler.shutdown()
        logger.info("🛑 Reminder scheduler stopped")


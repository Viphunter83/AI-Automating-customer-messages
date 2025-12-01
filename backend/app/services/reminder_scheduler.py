import asyncio
import logging
import uuid
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import async_session_maker
from app.models.database import Message, MessageType, Reminder, ReminderType
from app.services.dialog_auto_close import DialogAutoCloseService
from app.services.reminder_service import ReminderService
from app.services.response_manager import ResponseManager
from app.services.webhook_sender import WebhookSender

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
                    logger.debug(
                        f"Reminder {reminder_id} already processed or cancelled"
                    )
                    return

                # Check if client has responded since reminder was created
                # If they have, cancel the reminder
                result = await session.execute(
                    select(Message)
                    .where(
                        Message.client_id == client_id,
                        Message.created_at > reminder.created_at,
                        Message.message_type == MessageType.USER,
                    )
                    .order_by(Message.created_at.desc())
                    .limit(1)
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
                (
                    response_msg,
                    response_text,
                ) = await response_manager.create_bot_response(
                    scenario="REMINDER",
                    client_id=client_id,
                    original_message_id=message_id,
                    message_type=MessageType.BOT_AUTO,
                )

                if not response_msg:
                    logger.error(f"Failed to create reminder response for {client_id}")
                    return

                # Send via webhook
                webhook_result = await self.webhook_sender.send_response(
                    client_id=client_id,
                    response_text=response_text,
                    message_id=str(response_msg.id),
                    classification={"scenario": "REMINDER", "confidence": 1.0},
                )

                # Mark reminder as sent
                await reminder_service.mark_reminder_sent(reminder_id)
                await session.commit()

                logger.info(
                    f"Sent reminder {reminder_id} to client {client_id}, "
                    f"webhook_result={webhook_result.get('success', False)}"
                )

            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                logger.error(
                    f"❌ Error sending reminder {reminder_id} to client {client_id}: "
                    f"{error_type}: {error_msg}",
                    exc_info=True,
                )

                # Try to mark reminder as failed (optional: could add failed_at field)
                try:
                    async with async_session_maker() as error_session:
                        reminder_service = ReminderService(error_session)
                        # Note: In future, we could add a failed_attempts counter
                        # For now, we just log the error
                        await error_session.commit()
                except Exception as cleanup_error:
                    logger.error(
                        f"Failed to cleanup after reminder error: {cleanup_error}"
                    )

    async def process_pending_reminders(self):
        """Process all pending reminders"""
        async with async_session_maker() as session:
            try:
                reminder_service = ReminderService(session)
                pending_reminders = await reminder_service.get_pending_reminders(
                    limit=50
                )

                if not pending_reminders:
                    logger.debug("No pending reminders to process")
                    return

                logger.info(f"Processing {len(pending_reminders)} pending reminders")

                for reminder in pending_reminders:
                    await self.send_reminder(
                        str(reminder.id), reminder.client_id, str(reminder.message_id)
                    )

            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                logger.error(
                    f"❌ Error processing pending reminders: {error_type}: {error_msg}",
                    exc_info=True,
                )
                # Don't re-raise - continue processing other reminders
                # This ensures one failed reminder doesn't stop all processing

    async def process_inactive_dialogs(self):
        """Job to process inactive dialogs: send farewell and close"""
        logger.debug("Checking for inactive dialogs...")
        async with async_session_maker() as session:
            try:
                dialog_service = DialogAutoCloseService(session)
                stats = await dialog_service.process_inactive_sessions()

                if stats["farewell_sent"] > 0 or stats["sessions_closed"] > 0:
                    logger.info(
                        f"Processed inactive dialogs: "
                        f"{stats['farewell_sent']} farewells sent, "
                        f"{stats['sessions_closed']} sessions closed"
                    )
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                logger.error(
                    f"❌ Error processing inactive dialogs: {error_type}: {error_msg}",
                    exc_info=True,
                )
                # Don't re-raise - continue processing other dialogs
                # This ensures one failed dialog doesn't stop all processing

    def start(self):
        """Start the reminder scheduler"""
        if not self.scheduler.running:
            # Add job for processing reminders
            self.scheduler.add_job(
                self.process_pending_reminders,
                IntervalTrigger(minutes=1),
                id="process_reminders_job",
                replace_existing=True,
            )
            # Add job for processing inactive dialogs
            self.scheduler.add_job(
                self.process_inactive_dialogs,
                IntervalTrigger(minutes=1),
                id="process_inactive_dialogs_job",
                replace_existing=True,
            )
            self.scheduler.start()
            logger.info("✅ Reminder scheduler started (with dialog auto-close)")
        else:
            logger.info("Reminder scheduler already running")

    def stop(self):
        """Stop the reminder scheduler"""
        self.scheduler.shutdown()
        logger.info("🛑 Reminder scheduler stopped")

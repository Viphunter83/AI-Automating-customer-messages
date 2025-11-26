import logging
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Reminder, ReminderType, Message, MessageType
import uuid

logger = logging.getLogger(__name__)

class ReminderService:
    """Service for managing reminders to clients"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_reminder(
        self,
        client_id: str,
        message_id: str,
        reminder_type: ReminderType,
        delay_minutes: Optional[int] = None
    ) -> Reminder:
        """
        Create a reminder for a client message
        
        Args:
            client_id: Client ID
            message_id: ID of the message to remind about
            reminder_type: Type of reminder (15min, 30min, 1day)
            delay_minutes: Optional custom delay in minutes (overrides default)
        
        Returns:
            Created Reminder object
        """
        # Calculate scheduled_at based on reminder_type
        if delay_minutes is not None:
            scheduled_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
        elif reminder_type == ReminderType.REMINDER_15MIN:
            scheduled_at = datetime.utcnow() + timedelta(minutes=15)
        elif reminder_type == ReminderType.REMINDER_30MIN:
            scheduled_at = datetime.utcnow() + timedelta(minutes=30)
        elif reminder_type == ReminderType.REMINDER_1DAY:
            scheduled_at = datetime.utcnow() + timedelta(days=1)
        else:
            scheduled_at = datetime.utcnow() + timedelta(minutes=30)  # Default
        
        reminder = Reminder(
            id=uuid.uuid4(),
            client_id=client_id,
            message_id=uuid.UUID(message_id),
            reminder_type=reminder_type,
            scheduled_at=scheduled_at,
            is_cancelled=False,
        )
        
        self.session.add(reminder)
        await self.session.flush()
        
        logger.info(
            f"Created reminder for client {client_id}, "
            f"type={reminder_type.value}, scheduled_at={scheduled_at}"
        )
        
        return reminder
    
    async def get_pending_reminders(self, limit: int = 100) -> List[Reminder]:
        """
        Get reminders that are due to be sent.
        Uses SELECT FOR UPDATE to prevent multiple schedulers from processing the same reminders.
        
        Args:
            limit: Maximum number of reminders to return
        
        Returns:
            List of Reminder objects that are due
        """
        now = datetime.utcnow()
        
        # Use SELECT FOR UPDATE SKIP LOCKED to allow multiple scheduler instances
        # to work in parallel without conflicts
        result = await self.session.execute(
            select(Reminder).where(
                and_(
                    Reminder.scheduled_at <= now,
                    Reminder.sent_at.is_(None),
                    Reminder.is_cancelled == False
                )
            )
            .order_by(Reminder.scheduled_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        
        reminders = result.scalars().all()
        logger.debug(f"Found {len(reminders)} pending reminders")
        
        return reminders
    
    async def mark_reminder_sent(self, reminder_id: str) -> bool:
        """
        Mark a reminder as sent
        
        Args:
            reminder_id: ID of the reminder
        
        Returns:
            True if updated, False if not found
        """
        result = await self.session.execute(
            select(Reminder).where(Reminder.id == uuid.UUID(reminder_id))
        )
        reminder = result.scalar_one_or_none()
        
        if not reminder:
            logger.warning(f"Reminder {reminder_id} not found")
            return False
        
        reminder.sent_at = datetime.utcnow()
        await self.session.flush()
        
        logger.info(f"Marked reminder {reminder_id} as sent")
        return True
    
    async def cancel_client_reminders(
        self,
        client_id: str,
        after_message_id: Optional[str] = None
    ) -> int:
        """
        Cancel pending reminders for a client (e.g., when they respond)
        Uses SELECT FOR UPDATE to prevent race conditions.
        
        Args:
            client_id: Client ID
            after_message_id: Optional message ID - cancel reminders for messages created after this message
        
        Returns:
            Number of cancelled reminders
        """
        conditions = [
            Reminder.client_id == client_id,
            Reminder.sent_at.is_(None),
            Reminder.is_cancelled == False
        ]
        
        if after_message_id:
            # Get the message to compare creation time
            from app.models.database import Message
            message_result = await self.session.execute(
                select(Message)
                .where(Message.id == uuid.UUID(after_message_id))
                .with_for_update(skip_locked=True)
            )
            message = message_result.scalar_one_or_none()
            
            if message:
                # Cancel reminders for messages created after this message
                # We need to join with messages table to compare created_at
                conditions.append(
                    Reminder.message_id.in_(
                        select(Message.id).where(
                            and_(
                                Message.client_id == client_id,
                                Message.created_at > message.created_at
                            )
                        )
                    )
                )
            else:
                # If message not found, cancel all reminders for this client
                logger.warning(f"Message {after_message_id} not found, cancelling all reminders for {client_id}")
        
        if not conditions:
            logger.debug(f"No conditions to cancel reminders for {client_id}")
            return 0
        
        # Use SELECT FOR UPDATE to prevent race conditions when cancelling reminders
        result = await self.session.execute(
            select(Reminder)
            .where(and_(*conditions))
            .with_for_update(skip_locked=True)
        )
        reminders = result.scalars().all()
        
        cancelled_count = 0
        for reminder in reminders:
            # Double-check that reminder wasn't already cancelled or sent
            if not reminder.is_cancelled and reminder.sent_at is None:
                reminder.is_cancelled = True
                cancelled_count += 1
        
        await self.session.flush()
        
        if cancelled_count > 0:
            logger.info(
                f"Cancelled {cancelled_count} reminders for client {client_id}"
            )
        
        return cancelled_count
    
    async def get_client_reminders(
        self,
        client_id: str,
        include_sent: bool = False
    ) -> List[Reminder]:
        """
        Get all reminders for a client
        
        Args:
            client_id: Client ID
            include_sent: Whether to include already sent reminders
        
        Returns:
            List of Reminder objects
        """
        conditions = [Reminder.client_id == client_id]
        
        if not include_sent:
            conditions.append(Reminder.sent_at.is_(None))
        
        result = await self.session.execute(
            select(Reminder).where(and_(*conditions)).order_by(
                Reminder.scheduled_at.desc()
            )
        )
        
        return result.scalars().all()


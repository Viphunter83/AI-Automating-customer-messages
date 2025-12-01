"""
Unit tests for ReminderService
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.database import Message, MessageType, Reminder, ReminderType
from app.services.reminder_service import ReminderService


@pytest.mark.asyncio
async def test_create_reminder(async_session, test_client_id):
    """Test creating a reminder"""
    service = ReminderService(async_session)
    
    # Create a message first
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test message",
        message_type=MessageType.USER,
    )
    async_session.add(message)
    await async_session.flush()
    
    reminder = await service.create_reminder(
        client_id=test_client_id,
        message_id=str(message.id),
        reminder_type=ReminderType.REMINDER_15MIN,
    )
    
    assert reminder.id is not None
    assert reminder.client_id == test_client_id
    assert reminder.message_id == message.id
    assert reminder.reminder_type == ReminderType.REMINDER_15MIN
    assert reminder.scheduled_at > datetime.utcnow()
    assert reminder.is_cancelled is False


@pytest.mark.asyncio
async def test_get_pending_reminders(async_session, test_client_id):
    """Test getting pending reminders"""
    service = ReminderService(async_session)
    
    # Create a message
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test",
        message_type=MessageType.USER,
    )
    async_session.add(message)
    await async_session.flush()
    
    # Create pending reminder (scheduled in the past)
    reminder = Reminder(
        id=uuid4(),
        client_id=test_client_id,
        message_id=message.id,
        reminder_type=ReminderType.REMINDER_15MIN,
        scheduled_at=datetime.utcnow() - timedelta(minutes=1),
        is_cancelled=False,
    )
    async_session.add(reminder)
    await async_session.commit()
    
    pending = await service.get_pending_reminders(limit=10)
    assert len(pending) >= 1
    assert any(r.id == reminder.id for r in pending)


@pytest.mark.asyncio
async def test_mark_reminder_sent(async_session, test_client_id):
    """Test marking reminder as sent"""
    service = ReminderService(async_session)
    
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test",
        message_type=MessageType.USER,
    )
    async_session.add(message)
    await async_session.flush()
    
    reminder = Reminder(
        id=uuid4(),
        client_id=test_client_id,
        message_id=message.id,
        reminder_type=ReminderType.REMINDER_15MIN,
        scheduled_at=datetime.utcnow(),
        is_cancelled=False,
    )
    async_session.add(reminder)
    await async_session.commit()
    
    result = await service.mark_reminder_sent(str(reminder.id))
    assert result is True
    
    await async_session.refresh(reminder)
    assert reminder.sent_at is not None


@pytest.mark.asyncio
async def test_cancel_client_reminders(async_session, test_client_id):
    """Test cancelling client reminders"""
    service = ReminderService(async_session)
    
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test",
        message_type=MessageType.USER,
    )
    async_session.add(message)
    await async_session.flush()
    
    # Create pending reminders
    reminder1 = Reminder(
        id=uuid4(),
        client_id=test_client_id,
        message_id=message.id,
        reminder_type=ReminderType.REMINDER_15MIN,
        scheduled_at=datetime.utcnow() + timedelta(minutes=15),
        is_cancelled=False,
    )
    reminder2 = Reminder(
        id=uuid4(),
        client_id=test_client_id,
        message_id=message.id,
        reminder_type=ReminderType.REMINDER_30MIN,
        scheduled_at=datetime.utcnow() + timedelta(minutes=30),
        is_cancelled=False,
    )
    async_session.add(reminder1)
    async_session.add(reminder2)
    await async_session.commit()
    
    cancelled_count = await service.cancel_client_reminders(test_client_id)
    assert cancelled_count >= 2
    
    await async_session.refresh(reminder1)
    await async_session.refresh(reminder2)
    assert reminder1.is_cancelled is True
    assert reminder2.is_cancelled is True


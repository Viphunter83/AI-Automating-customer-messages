"""
Unit tests for MessageProcessingService
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.database import Message, MessageType, PriorityLevel, EscalationReason
from app.services.message_processing_service import MessageProcessingService, ProcessedMessage


@pytest.mark.asyncio
async def test_check_duplicate_found(async_session, test_client_id):
    """Test duplicate message detection"""
    service = MessageProcessingService(async_session)
    
    # Create first message
    first_message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test message",
        message_type=MessageType.USER,
        created_at=datetime.utcnow(),
    )
    async_session.add(first_message)
    await async_session.commit()
    
    # Check for duplicate (should find it)
    duplicate = await service.check_duplicate(test_client_id, "Test message")
    assert duplicate is not None
    assert duplicate.id == first_message.id


@pytest.mark.asyncio
async def test_check_duplicate_not_found(async_session, test_client_id):
    """Test duplicate check when no duplicate exists"""
    service = MessageProcessingService(async_session)
    
    # Check for duplicate (should not find it)
    duplicate = await service.check_duplicate(test_client_id, "Unique message")
    assert duplicate is None


@pytest.mark.asyncio
async def test_determine_first_message_true(async_session, test_client_id):
    """Test first message detection when no messages exist"""
    service = MessageProcessingService(async_session)
    
    is_first = await service.determine_first_message(test_client_id)
    assert is_first is True


@pytest.mark.asyncio
async def test_determine_first_message_false(async_session, test_client_id):
    """Test first message detection when messages exist"""
    service = MessageProcessingService(async_session)
    
    # Create existing message
    existing_message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Previous message",
        message_type=MessageType.USER,
        created_at=datetime.utcnow(),
    )
    async_session.add(existing_message)
    await async_session.commit()
    
    is_first = await service.determine_first_message(test_client_id)
    assert is_first is False


@pytest.mark.asyncio
async def test_process_text(async_session):
    """Test text processing"""
    service = MessageProcessingService(async_session)
    
    # Test normal text
    processed = await service.process_text("Привет! Как дела?")
    assert processed is not None
    assert len(processed) > 0
    
    # Test empty text
    processed = await service.process_text("")
    assert processed is None or len(processed) == 0


@pytest.mark.asyncio
async def test_save_original_message(async_session, test_client_id):
    """Test saving original message"""
    service = MessageProcessingService(async_session)
    
    message = await service.save_original_message(
        test_client_id, "Test content", is_first_message=True
    )
    
    assert message.id is not None
    assert message.client_id == test_client_id
    assert message.content == "Test content"
    assert message.is_first_message is True
    assert message.message_type == MessageType.USER


@pytest.mark.asyncio
async def test_evaluate_escalation_low_confidence(async_session, test_client_id):
    """Test escalation evaluation with low confidence"""
    service = MessageProcessingService(async_session)
    
    # Create a message first
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test",
        message_type=MessageType.USER,
    )
    async_session.add(message)
    await async_session.flush()
    
    result = await service.evaluate_escalation(
        message_id=str(message.id),
        scenario="GREETING",
        confidence=0.5,  # Low confidence
        client_id=test_client_id,
        content="Test",
    )
    
    assert result["requires_escalation"] is True
    assert result["priority"] == PriorityLevel.MEDIUM or result["priority"] == PriorityLevel.HIGH


@pytest.mark.asyncio
async def test_evaluate_escalation_unknown_scenario(async_session, test_client_id):
    """Test escalation evaluation for unknown scenario"""
    service = MessageProcessingService(async_session)
    
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test",
        message_type=MessageType.USER,
    )
    async_session.add(message)
    await async_session.flush()
    
    result = await service.evaluate_escalation(
        message_id=str(message.id),
        scenario="UNKNOWN",
        confidence=0.9,
        client_id=test_client_id,
        content="Test",
    )
    
    assert result["requires_escalation"] is True
    assert result["priority"] == PriorityLevel.HIGH


@pytest.mark.asyncio
async def test_evaluate_escalation_with_media(async_session, test_client_id):
    """Test escalation evaluation when media is present"""
    service = MessageProcessingService(async_session)
    
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="[ФОТО получено]",
        message_type=MessageType.USER,
    )
    async_session.add(message)
    await async_session.flush()
    
    # Test escalation with media - content contains media marker
    result = await service.evaluate_escalation(
        message_id=str(message.id),
        scenario="TECH_SUPPORT_BASIC",
        confidence=0.9,
        client_id=test_client_id,
        content="[ФОТО получено]",
    )
    
    assert result["requires_escalation"] is True


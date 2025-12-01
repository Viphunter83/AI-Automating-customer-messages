"""
Unit tests for EscalationManager
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.database import Message, MessageType, Classification, ScenarioType
from app.services.escalation_manager import EscalationManager, EscalationLevel


@pytest.mark.asyncio
async def test_evaluate_escalation_low_confidence(async_session, test_client_id):
    """Test escalation for low confidence"""
    manager = EscalationManager(async_session)
    
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test",
        message_type=MessageType.USER,
    )
    async_session.add(message)
    await async_session.flush()
    
    result = await manager.evaluate_escalation(
        message_id=str(message.id),
        scenario="GREETING",
        confidence=0.5,  # Below threshold (0.85)
        client_id=test_client_id,
    )
    
    assert result["should_escalate"] is True
    assert result["level"] == EscalationLevel.MEDIUM.value
    assert "low_confidence" in result["reasons"]


@pytest.mark.asyncio
async def test_evaluate_escalation_unknown_scenario(async_session, test_client_id):
    """Test escalation for unknown scenario"""
    manager = EscalationManager(async_session)
    
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test",
        message_type=MessageType.USER,
    )
    async_session.add(message)
    await async_session.flush()
    
    result = await manager.evaluate_escalation(
        message_id=str(message.id),
        scenario="UNKNOWN",
        confidence=0.9,
        client_id=test_client_id,
    )
    
    assert result["should_escalate"] is True
    assert result["level"] == EscalationLevel.HIGH.value
    assert "unknown_scenario" in result["reasons"]


@pytest.mark.asyncio
async def test_evaluate_escalation_repeated_failures(async_session, test_client_id):
    """Test escalation for repeated failures"""
    manager = EscalationManager(async_session)
    
    # Create messages with low confidence classifications
    for i in range(2):
        message = Message(
            id=uuid4(),
            client_id=test_client_id,
            content=f"Test {i}",
            message_type=MessageType.USER,
            created_at=datetime.utcnow() - timedelta(minutes=30),
        )
        async_session.add(message)
        await async_session.flush()
        
        classification = Classification(
            id=uuid4(),
            message_id=message.id,
            detected_scenario=ScenarioType.UNKNOWN,
            confidence=0.5,  # Low confidence
            created_at=datetime.utcnow() - timedelta(minutes=30),
        )
        async_session.add(classification)
    
    await async_session.commit()
    
    # New message
    new_message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="New test",
        message_type=MessageType.USER,
    )
    async_session.add(new_message)
    await async_session.flush()
    
    result = await manager.evaluate_escalation(
        message_id=str(new_message.id),
        scenario="GREETING",
        confidence=0.6,
        client_id=test_client_id,
    )
    
    assert result["should_escalate"] is True
    assert "repeated_failed" in result["reasons"]


@pytest.mark.asyncio
async def test_evaluate_escalation_high_confidence_no_escalation(async_session, test_client_id):
    """Test no escalation for high confidence"""
    manager = EscalationManager(async_session)
    
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test",
        message_type=MessageType.USER,
    )
    async_session.add(message)
    await async_session.flush()
    
    result = await manager.evaluate_escalation(
        message_id=str(message.id),
        scenario="GREETING",
        confidence=0.95,  # High confidence
        client_id=test_client_id,
    )
    
    assert result["should_escalate"] is False or result["level"] == EscalationLevel.LOW.value


@pytest.mark.asyncio
async def test_priority_queue_mapping(async_session):
    """Test priority queue mapping"""
    manager = EscalationManager(async_session)
    
    # Test different escalation levels
    assert manager._get_priority_queue(EscalationLevel.CRITICAL) == 1
    assert manager._get_priority_queue(EscalationLevel.HIGH) == 3
    assert manager._get_priority_queue(EscalationLevel.MEDIUM) == 7
    assert manager._get_priority_queue(EscalationLevel.LOW) == 10


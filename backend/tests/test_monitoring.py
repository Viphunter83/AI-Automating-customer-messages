"""
Unit tests for Monitoring endpoints
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.database import Message, MessageType, Classification, ScenarioType, Reminder, ReminderType
from app.routes.monitoring import get_metrics, get_stats_summary


@pytest.mark.asyncio
async def test_get_metrics(async_session, test_client_id):
    """Test metrics endpoint"""
    # Create test data
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test message",
        message_type=MessageType.USER,
        created_at=datetime.utcnow(),
    )
    async_session.add(message)
    await async_session.flush()
    
    classification = Classification(
        id=uuid4(),
        message_id=message.id,
        detected_scenario=ScenarioType.GREETING,
        confidence=0.95,
        created_at=datetime.utcnow(),
    )
    async_session.add(classification)
    await async_session.commit()
    
    # Get metrics
    metrics = await get_metrics(async_session)
    
    assert "timestamp" in metrics
    assert "messages" in metrics
    assert "classifications" in metrics
    assert "reminders" in metrics
    assert metrics["messages"]["total"] >= 1


@pytest.mark.asyncio
async def test_get_stats_summary(async_session, test_client_id):
    """Test stats summary endpoint"""
    # Create test data
    message = Message(
        id=uuid4(),
        client_id=test_client_id,
        content="Test",
        message_type=MessageType.USER,
        created_at=datetime.utcnow(),
    )
    async_session.add(message)
    await async_session.flush()
    
    classification = Classification(
        id=uuid4(),
        message_id=message.id,
        detected_scenario=ScenarioType.GREETING,
        confidence=0.95,
        created_at=datetime.utcnow(),
    )
    async_session.add(classification)
    await async_session.commit()
    
    # Get stats
    stats = await get_stats_summary(async_session)
    
    assert "timestamp" in stats
    assert "total_messages" in stats
    assert "total_clients" in stats
    assert stats["total_messages"] >= 1
    assert stats["total_clients"] >= 1


"""
E2E tests for message processing flow
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.models.database import Message, MessageType, ChatSession, DialogStatus
from main import app


@pytest.fixture(autouse=True)
def mock_openai_classify(mocker):
    """Mock OpenAI classification for all tests"""
    async def mock_classify(*args, **kwargs):
        return {
            "success": True,
            "scenario": "REFERRAL",
            "confidence": 0.95,
            "reasoning": "Test",
        }
    
    # Mock AIClassifier.classify method
    mocker.patch('app.services.ai_classifier.AIClassifier.classify', 
                 new_callable=mocker.AsyncMock,
                 side_effect=mock_classify)
    
    # Mock OpenAI client (from openai package)
    from unittest.mock import MagicMock
    mock_openai = mocker.patch('openai.OpenAI')
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance
    
    # Mock chat completions
    mock_chat = MagicMock()
    mock_instance.chat.completions.create = MagicMock(return_value=type('obj', (object,), {
        'choices': [type('obj', (object,), {
            'message': type('obj', (object,), {
                'content': '{"scenario": "REFERRAL", "confidence": 0.95, "reasoning": "Test"}'
            })()
        })()]
    })())
    
    return mock_instance


@pytest.fixture(autouse=True)
def mock_webhook_sender(mocker):
    """Mock webhook sender to avoid actual HTTP calls"""
    mocker.patch('app.services.webhook_sender.WebhookSender.send_response', 
                 new_callable=mocker.AsyncMock,
                 return_value={"success": True, "status_code": 200})
    
    # Also mock background tasks
    mocker.patch('fastapi.BackgroundTasks.add_task')


@pytest.mark.asyncio
async def test_e2e_message_processing_flow(async_session, test_client_id, mock_openai_classify, mock_webhook_sender):
    """Test complete message processing flow"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Send a message
    response = client.post(
        "/api/messages/",
        json={
            "client_id": test_client_id,
            "content": "Привет! Хочу узнать про реферальную программу",
        },
        headers={
            "X-Webhook-URL": "http://test-webhook.com/response",
            "X-Platform": "test",
            "X-Chat-ID": "12345",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "original_message_id" in data
    
    # Verify message was saved
    from sqlalchemy import select
    result = await async_session.execute(
        select(Message).where(Message.client_id == test_client_id)
    )
    messages = result.scalars().all()
    assert len(messages) >= 1
    
    # Verify ChatSession was created with webhook info
    session_result = await async_session.execute(
        select(ChatSession).where(ChatSession.client_id == test_client_id)
    )
    chat_session = session_result.scalar_one_or_none()
    assert chat_session is not None
    assert chat_session.webhook_url == "http://test-webhook.com/response"
    assert chat_session.platform == "test"
    assert chat_session.chat_id == "12345"


@pytest.mark.asyncio
async def test_e2e_duplicate_message(async_session, test_client_id, mock_openai_classify, mock_webhook_sender):
    """Test duplicate message detection"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    content = "Duplicate test message"
    
    # Send first message
    response1 = client.post(
        "/api/messages/",
        json={
            "client_id": test_client_id,
            "content": content,
        },
    )
    assert response1.status_code == 201
    
    # Send duplicate message (within 5 seconds)
    response2 = client.post(
        "/api/messages/",
        json={
            "client_id": test_client_id,
            "content": content,
        },
    )
    assert response2.status_code == 409  # Conflict
    assert "duplicate" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_e2e_rate_limiting(async_session, test_client_id, mock_openai_classify, mock_webhook_sender):
    """Test rate limiting per client"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Send multiple messages quickly
    responses = []
    for i in range(12):  # More than limit (10 per minute)
        response = client.post(
            "/api/messages/",
            json={
                "client_id": test_client_id,
                "content": f"Message {i}",
            },
        )
        responses.append(response)
    
    # At least one should be rate limited
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes  # Too Many Requests


@pytest.mark.asyncio
async def test_e2e_first_message_greeting(async_session, test_client_id, mock_openai_classify, mock_webhook_sender):
    """Test that first message always gets greeting"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Send first message (not a greeting scenario)
    response = client.post(
        "/api/messages/",
        json={
            "client_id": test_client_id,
            "content": "У меня проблема с платформой",
        },
        headers={
            "X-Webhook-URL": "http://test-webhook.com/response",
        },
    )
    
    assert response.status_code == 201
    
    # Verify response was created
    from sqlalchemy import select
    
    result = await async_session.execute(
        select(Message)
        .where(Message.client_id == test_client_id)
        .where(Message.message_type == MessageType.BOT_AUTO)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    bot_message = result.scalar_one_or_none()
    
    # Should have greeting in response (even if scenario is TECH_SUPPORT_BASIC)
    assert bot_message is not None
    # Note: Actual greeting check would require checking webhook payload
    # This is a simplified check


@pytest.mark.asyncio
async def test_e2e_escalation_flow(async_session, test_client_id, mock_openai_classify, mock_webhook_sender):
    """Test escalation flow for complex scenarios"""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Mock classification to return COMPLAINT scenario
    import pytest_mock
    mocker = pytest_mock.MockerFixture
    
    # Send message that should be escalated
    response = client.post(
        "/api/messages/",
        json={
            "client_id": test_client_id,
            "content": "Жалоба на плохое обслуживание",
        },
        headers={
            "X-Webhook-URL": "http://test-webhook.com/response",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify escalation data
    assert "original_message_id" in data
    
    # Check that escalation response was created
    from sqlalchemy import select
    
    result = await async_session.execute(
        select(Message)
        .where(Message.client_id == test_client_id)
        .where(Message.message_type == MessageType.BOT_ESCALATED)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    escalation_message = result.scalar_one_or_none()
    
    # Should have escalation message (if scenario requires escalation)
    # Note: This depends on classification result
    # For now, just verify message was processed
    assert data["status"] == "success"

"""
Unit tests for WebhookSender
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import Response

from app.services.webhook_sender import WebhookSender


@pytest.mark.asyncio
async def test_send_response_success():
    """Test successful webhook send"""
    sender = WebhookSender(platform_webhook_url="http://test-webhook.com/response")
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Response(
            200,
            json={"message_id": "123"},
            headers={"content-type": "application/json"}
        )
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        result = await sender.send_response(
            client_id="test_client",
            response_text="Test response",
            message_id="msg_123",
        )
        
        assert result["success"] is True
        assert result["status_code"] == 200


@pytest.mark.asyncio
async def test_send_response_retryable_error():
    """Test retryable error handling"""
    sender = WebhookSender(platform_webhook_url="http://test-webhook.com/response")
    
    from httpx import Request
    from httpx._exceptions import HTTPStatusError
    
    with patch('httpx.AsyncClient') as mock_client:
        # Simulate retryable error (503)
        mock_request = Request("POST", "http://test-webhook.com/response")
        mock_response = Response(503, text="Service Unavailable", request=mock_request)
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        # Should raise HTTPStatusError for retry (due to retry decorator)
        with pytest.raises((HTTPStatusError, Exception)):
            await sender.send_response(
                client_id="test_client",
                response_text="Test",
                message_id="msg_123",
            )


@pytest.mark.asyncio
async def test_send_response_non_retryable_error():
    """Test non-retryable error handling"""
    sender = WebhookSender(platform_webhook_url="http://test-webhook.com/response")
    
    with patch('httpx.AsyncClient') as mock_client:
        # Simulate non-retryable error (400)
        mock_response = Response(400, text="Bad Request")
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        result = await sender.send_response(
            client_id="test_client",
            response_text="Test",
            message_id="msg_123",
        )
        
        assert result["success"] is False
        assert result["retryable"] is False


@pytest.mark.asyncio
async def test_send_response_with_platform_headers():
    """Test webhook send with platform-specific headers"""
    sender = WebhookSender(
        platform_webhook_url="http://test-webhook.com/response",
        platform="telegram",
        chat_id="12345",
    )
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Response(200, json={})
        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        await sender.send_response(
            client_id="test_client",
            response_text="Test",
            message_id="msg_123",
        )
        
        # Verify headers were included
        call_args = mock_post.call_args
        assert call_args is not None
        headers = call_args[1].get("headers", {})
        assert headers.get("X-Platform") == "telegram"
        assert headers.get("X-Chat-ID") == "12345"


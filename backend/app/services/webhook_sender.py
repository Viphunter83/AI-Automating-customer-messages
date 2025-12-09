import logging
from typing import Dict, Optional

import httpx
from httpx import HTTPStatusError, NetworkError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = logging.getLogger(__name__)


class WebhookSender:
    """Send responses back to the chat platform via webhook"""

    def __init__(
        self,
        platform_webhook_url: Optional[str] = None,
        platform: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        """
        Initialize WebhookSender

        Args:
            platform_webhook_url: URL where to send responses
                                  (should be provided by the customer)
            platform: Platform identifier (e.g., "telegram")
            chat_id: Platform-specific chat ID (for headers)
        """
        settings = get_settings()
        self.platform_webhook_url = (
            platform_webhook_url
            or getattr(settings, "platform_webhook_url", None)
            or "http://localhost:9000/webhook/response"
        )
        self.platform = platform
        self.chat_id = chat_id
        self.timeout = 30

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,  # Re-raise exception after retries exhausted
    )
    async def send_response(
        self,
        client_id: str,
        response_text: str,
        message_id: str,
        classification: Dict = None,
    ) -> Dict[str, any]:
        """
        Send bot response back to platform
        
        Implements idempotency check to prevent duplicate webhook calls.

        Args:
            client_id: Client identifier
            response_text: Response text to send
            message_id: ID of the bot response message
            classification: Classification info for tracking

        Returns:
            {
                "success": bool,
                "platform_message_id": str|None,
                "error": str|None,
                "skipped": bool (if already sent)
            }
        """
        # Check idempotency first (prevent duplicate webhook calls)
        try:
            from app.utils.redis_cache import get_redis_cache
            redis_cache = await get_redis_cache()
            sent_key = f"webhook_sent:{message_id}"
            already_sent = await redis_cache.get(sent_key)
            
            if already_sent:
                logger.info(
                    f"Webhook for message {message_id} already sent, skipping duplicate call"
                )
                # Increment duplicate counter for monitoring
                try:
                    duplicate_key = "metrics:webhook_duplicates"
                    current_count = await redis_cache.get(duplicate_key)
                    count = int(current_count) if current_count else 0
                    await redis_cache.set(duplicate_key, str(count + 1), ttl_seconds=86400)  # 24h TTL
                except Exception as e:
                    logger.debug(f"Failed to increment duplicate counter: {e}")
                
                platform_msg_id = already_sent if isinstance(already_sent, str) else str(already_sent)
                return {
                    "success": True,
                    "platform_message_id": platform_msg_id,
                    "error": None,
                    "skipped": True,
                    "reason": "already_sent",
                }
        except Exception as e:
            logger.debug(f"Idempotency check failed for message {message_id}: {e}, continuing with send")
        
        try:
            payload = {
                "client_id": client_id,
                "response_text": response_text,
                "message_id": message_id,
                "classification": classification or {},
                "source": "ai_bot",
            }

            # Prepare headers (include platform-specific headers)
            headers = {}
            if self.chat_id:
                headers["X-Chat-ID"] = self.chat_id
            if self.platform:
                headers["X-Platform"] = self.platform

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.platform_webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )

            # Handle different status codes
            if response.status_code in [200, 201]:
                result = (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else {}
                )
                platform_msg_id = result.get("message_id") or message_id
                logger.info(
                    f"✅ Response sent to platform for client {client_id}, "
                    f"status: {response.status_code}"
                )
                
                # Mark as sent after successful delivery (idempotency)
                try:
                    from app.utils.redis_cache import get_redis_cache
                    redis_cache = await get_redis_cache()
                    sent_key = f"webhook_sent:{message_id}"
                    # Store platform message ID for reference, TTL 1 hour
                    await redis_cache.set(sent_key, str(platform_msg_id), ttl_seconds=3600)
                    logger.debug(f"Marked webhook for message {message_id} as sent")
                except Exception as e:
                    logger.debug(f"Failed to mark webhook as sent: {e}")
                
                return {
                    "success": True,
                    "platform_message_id": platform_msg_id,
                    "error": None,
                    "status_code": response.status_code,
                }
            elif response.status_code in [429, 502, 503, 504]:
                # Retryable errors - these will trigger retry decorator
                error_msg = f"Platform returned {response.status_code} (retryable)"
                logger.warning(
                    f"⚠️ Retryable error for client {client_id}: {error_msg}, "
                    f"response: {response.text[:200]}"
                )
                # Re-raise to trigger retry
                raise httpx.HTTPStatusError(
                    f"Retryable error: {response.status_code}",
                    request=response.request,
                    response=response,
                )
            else:
                # Non-retryable errors (4xx except 429)
                error_msg = f"Platform returned {response.status_code}"
                logger.error(
                    f"❌ Non-retryable error for client {client_id}: {error_msg}, "
                    f"response: {response.text[:200]}"
                )
                return {
                    "success": False,
                    "platform_message_id": None,
                    "error": error_msg,
                    "status_code": response.status_code,
                    "retryable": False,
                }

        except httpx.TimeoutException as e:
            logger.warning(f"⚠️ Webhook timeout for client {client_id} (will retry)")
            # Re-raise to trigger retry
            raise

        except HTTPStatusError as e:
            # This is raised for retryable status codes
            logger.warning(
                f"⚠️ HTTP error for client {client_id}: {e.response.status_code} (will retry)"
            )
            raise

        except NetworkError as e:
            # Network errors are retryable
            logger.warning(
                f"⚠️ Network error for client {client_id}: {str(e)} (will retry)"
            )
            raise

        except Exception as e:
            # Unexpected errors - log and return error response
            logger.error(
                f"❌ Unexpected webhook error for client {client_id}: "
                f"{type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            # Don't retry unexpected errors
            return {
                "success": False,
                "platform_message_id": None,
                "error": f"Unexpected error: {str(e)}",
                "retryable": False,
            }

import logging
from typing import Dict, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings

logger = logging.getLogger(__name__)

class WebhookSender:
    """Send responses back to the chat platform via webhook"""
    
    def __init__(self, platform_webhook_url: Optional[str] = None):
        """
        Initialize WebhookSender
        
        Args:
            platform_webhook_url: URL where to send responses
                                  (should be provided by the customer)
        """
        settings = get_settings()
        self.platform_webhook_url = platform_webhook_url or getattr(settings, 'platform_webhook_url', None) or "http://localhost:9000/webhook/response"
        self.timeout = 30
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
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
        
        Args:
            client_id: Client identifier
            response_text: Response text to send
            message_id: ID of the bot response message
            classification: Classification info for tracking
        
        Returns:
            {
                "success": bool,
                "platform_message_id": str|None,
                "error": str|None
            }
        """
        try:
            payload = {
                "client_id": client_id,
                "response_text": response_text,
                "message_id": message_id,
                "classification": classification or {},
                "source": "ai_bot",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.platform_webhook_url,
                    json=payload,
                    timeout=self.timeout,
                )
            
            if response.status_code in [200, 201]:
                result = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                logger.info(
                    f"✅ Response sent to platform for client {client_id}, "
                    f"status: {response.status_code}"
                )
                return {
                    "success": True,
                    "platform_message_id": result.get("message_id"),
                    "error": None,
                }
            else:
                logger.error(
                    f"❌ Platform responded with {response.status_code}: "
                    f"{response.text[:200]}"
                )
                return {
                    "success": False,
                    "platform_message_id": None,
                    "error": f"Platform returned {response.status_code}",
                }
        
        except httpx.TimeoutException:
            logger.error(f"❌ Webhook timeout for client {client_id}")
            return {
                "success": False,
                "platform_message_id": None,
                "error": "Webhook timeout",
            }
        
        except Exception as e:
            logger.error(f"❌ Webhook error: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "platform_message_id": None,
                "error": str(e),
            }


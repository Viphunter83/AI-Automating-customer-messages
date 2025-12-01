"""
Message Delivery Service
Handles delivery of responses via webhooks and WebSocket notifications
"""
import asyncio
import logging
import random
from typing import Dict, Optional

from fastapi import BackgroundTasks

from app.config import get_settings
from app.services.message_processing_service import ProcessedMessage
from app.services.message_response_service import MessageResponse
from app.services.webhook_sender import WebhookSender
from app.services.websocket_notifier import notify_all_operators

logger = logging.getLogger(__name__)
settings = get_settings()


class DeliveryResult:
    """Result of message delivery"""
    def __init__(
        self,
        webhook_sent: bool = False,
        webhook_result: Optional[Dict] = None,
        websocket_notified: bool = False,
    ):
        self.webhook_sent = webhook_sent
        self.webhook_result = webhook_result
        self.websocket_notified = websocket_notified


class MessageDeliveryService:
    """Service for delivering messages via webhooks and WebSocket"""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        platform: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.webhook_url = webhook_url
        self.platform = platform
        self.chat_id = chat_id
        self.webhook_sender = WebhookSender(
            platform_webhook_url=webhook_url,
            platform=platform,
            chat_id=chat_id,
        ) if webhook_url else WebhookSender(
            platform=platform,
            chat_id=chat_id,
        )

    def prepare_webhook_data(
        self,
        processed_message: ProcessedMessage,
        message_response: MessageResponse,
    ) -> Dict:
        """
        Prepare data for webhook delivery
        
        Returns:
            Dict with webhook payload
        """
        classification_data = None
        if processed_message.classification:
            classification_data = {
                "scenario": processed_message.scenario,
                "confidence": processed_message.confidence,
                "id": str(processed_message.classification.id),
                "reasoning": processed_message.classification.reasoning,
            }

        escalation_data = None
        if processed_message.requires_escalation:
            escalation_data = {
                "priority": processed_message.priority.value,
                "escalation_reason": (
                    processed_message.escalation_reason.value
                    if processed_message.escalation_reason
                    else None
                ),
                "is_first_message": processed_message.is_first_message,
                "priority_queue": processed_message.priority_queue,
            }

        return {
            "client_id": processed_message.original_message.client_id,
            "response_text": message_response.response_text,
            "message_id": str(message_response.response_message.id),
            "classification": classification_data,
            "requires_escalation": processed_message.requires_escalation,
            "escalation_data": escalation_data,
            "response_data": {
                "original_message_id": str(processed_message.original_message.id),
                "response_message_id": str(message_response.response_message.id),
                "response_text": message_response.response_text,
                "response_type": message_response.response_message.message_type.value,
                "is_first_message": processed_message.is_first_message,
                "priority": processed_message.priority.value,
                "escalation_reason": (
                    processed_message.escalation_reason.value
                    if processed_message.escalation_reason
                    else None
                ),
            },
        }

    async def send_webhook_async(
        self, webhook_data: Dict
    ) -> Dict:
        """
        Send webhook asynchronously (for background tasks)
        
        Returns:
            Webhook result dict
        """
        try:
            # Add delay before sending response (simulate "typing...")
            if settings.delays_enabled and settings.response_delay_seconds > 0:
                delay = settings.response_delay_seconds
                # Add some randomness (±1 second) for more natural feel
                delay += random.uniform(-1.0, 1.0)
                delay = max(1.0, delay)  # Minimum 1 second
                logger.debug(
                    f"⏳ Delaying response by {delay:.1f} seconds for better UX"
                )
                await asyncio.sleep(delay)

            webhook_result = await self.webhook_sender.send_response(
                client_id=webhook_data["client_id"],
                response_text=webhook_data["response_text"],
                message_id=webhook_data["message_id"],
                classification=webhook_data.get("classification"),
            )
            logger.info(f"📤 Webhook send result: {webhook_result}")
            return webhook_result
        except Exception as webhook_error:
            logger.error(
                f"❌ Webhook send failed (non-critical): {str(webhook_error)}"
            )
            return {
                "success": False,
                "error": str(webhook_error),
                "note": "Message was saved successfully, but webhook failed",
            }

    async def notify_operators_async(
        self, webhook_data: Dict
    ) -> None:
        """
        Notify operators via WebSocket asynchronously
        """
        if not webhook_data.get("requires_escalation"):
            return

        try:
            escalation_data = webhook_data.get("escalation_data")
            if escalation_data:
                await notify_all_operators(
                    {
                        "type": "escalation",
                        "client_id": webhook_data["client_id"],
                        "message": f"New escalation from {webhook_data['client_id']}",
                        "scenario": webhook_data.get("classification", {}).get(
                            "scenario", "UNKNOWN"
                        ),
                        "priority": escalation_data.get("priority", "low"),
                        "priority_queue": escalation_data.get("priority_queue", 10),
                        "escalation_reason": escalation_data.get(
                            "escalation_reason"
                        ),
                        "is_first_message": escalation_data.get(
                            "is_first_message", False
                        ),
                    }
                )
        except Exception as ws_error:
            logger.error(
                f"❌ WebSocket notification failed (non-critical): {str(ws_error)}"
            )

    def schedule_delivery(
        self,
        background_tasks: BackgroundTasks,
        processed_message: ProcessedMessage,
        message_response: MessageResponse,
    ) -> DeliveryResult:
        """
        Schedule delivery of message via background tasks
        
        This method schedules webhook and WebSocket delivery in background,
        allowing the API to return immediately without blocking.
        
        Returns:
            DeliveryResult with scheduling information
        """
        webhook_data = self.prepare_webhook_data(
            processed_message, message_response
        )

        # Schedule webhook delivery in background
        background_tasks.add_task(
            self.send_webhook_async,
            webhook_data,
        )

        # Schedule WebSocket notification in background
        background_tasks.add_task(
            self.notify_operators_async,
            webhook_data,
        )

        logger.info(
            f"📤 Scheduled delivery for client {processed_message.original_message.client_id}"
        )

        return DeliveryResult(
            webhook_sent=True,
            webhook_result={"success": True, "scheduled": True},
            websocket_notified=True,
        )

    async def deliver_sync(
        self,
        processed_message: ProcessedMessage,
        message_response: MessageResponse,
    ) -> DeliveryResult:
        """
        Deliver message synchronously (for testing or when background tasks unavailable)
        
        Returns:
            DeliveryResult with delivery status
        """
        webhook_data = self.prepare_webhook_data(
            processed_message, message_response
        )

        # Send webhook synchronously
        webhook_result = await self.send_webhook_async(webhook_data)

        # Notify operators synchronously
        await self.notify_operators_async(webhook_data)

        return DeliveryResult(
            webhook_sent=True,
            webhook_result=webhook_result,
            websocket_notified=True,
        )


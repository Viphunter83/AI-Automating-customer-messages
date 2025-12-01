"""
Message Response Service
Handles creation of bot responses based on processed messages
"""
import logging
from typing import Dict, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Message, MessageType
from app.services.message_processing_service import ProcessedMessage
from app.services.reminder_service import ReminderService, ReminderType
from app.services.response_manager import ResponseManager

logger = logging.getLogger(__name__)


class MessageResponse:
    """Result of response creation"""
    def __init__(
        self,
        response_message: Message,
        response_text: str,
        scenario_response_message: Optional[Message] = None,
    ):
        self.response_message = response_message
        self.response_text = response_text
        self.scenario_response_message = scenario_response_message


class MessageResponseService:
    """Service for creating bot responses"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.response_manager = ResponseManager(session)
        self.reminder_service = ReminderService(session)

    async def create_response(
        self, processed_message: ProcessedMessage, client_id: str
    ) -> MessageResponse:
        """
        Create bot response based on processed message
        
        Returns:
            MessageResponse object with response message and text
        """
        scenario = processed_message.scenario
        requires_escalation = processed_message.requires_escalation
        scenario_msg = None  # Initialize to avoid NameError

        # For escalated scenarios, send "escalated" message to client
        # Scenario-specific response is saved for operator context
        if requires_escalation:
            # Send escalation notification to client
            response_msg, response_text = await self.response_manager.create_bot_response(
                scenario="ESCALATED",
                client_id=client_id,
                original_message_id=str(processed_message.original_message.id),
                params={},
                message_type=MessageType.BOT_ESCALATED,
            )

            # Also create scenario-specific response for operator context
            scenario_msg, _ = await self.response_manager.create_bot_response(
                scenario=scenario,
                client_id=client_id,
                original_message_id=str(processed_message.original_message.id),
                params={
                    "referral_link": f"https://example.com/ref/{client_id}"
                },
                message_type=MessageType.BOT_ESCALATED,
            )

            if scenario_msg:
                logger.debug(
                    f"Created scenario response for operator context: {scenario_msg.id}"
                )

            logger.info(f"📤 Created escalation response for client {client_id}")
        else:
            # Normal auto response
            response_msg, response_text = await self.response_manager.create_bot_response(
                scenario=scenario,
                client_id=client_id,
                original_message_id=str(processed_message.original_message.id),
                params={
                    "referral_link": f"https://example.com/ref/{client_id}"
                },
                message_type=MessageType.BOT_AUTO,
            )

        if not response_msg:
            logger.error("❌ Failed to create response, using fallback")
            response_msg, response_text = await self.response_manager.create_fallback_response(
                client_id, reason="response_creation_error"
            )

        if not response_msg:
            raise RuntimeError("Failed to create bot response after fallback")

        logger.info(f"✅ Created response: {response_msg.id}")

        return MessageResponse(
            response_message=response_msg,
            response_text=response_text,
            scenario_response_message=scenario_msg if requires_escalation else None,
        )

    async def create_reminders(
        self,
        client_id: str,
        message_id: str,
        requires_escalation: bool,
        scenario: str,
    ) -> None:
        """
        Create reminders for client if needed
        
        Reminders are not created for:
        - Escalated messages
        - FAREWELL scenario
        - UNKNOWN scenario
        """
        if requires_escalation or scenario in ["FAREWELL", "UNKNOWN"]:
            logger.debug(f"Skipping reminders for scenario {scenario}")
            return

        await self.reminder_service.create_reminder(
            client_id=client_id,
            message_id=message_id,
            reminder_type=ReminderType.REMINDER_15MIN,
        )

        await self.reminder_service.create_reminder(
            client_id=client_id,
            message_id=message_id,
            reminder_type=ReminderType.REMINDER_30MIN,
        )

        logger.debug(f"Created reminders for message {message_id}")

    async def cancel_pending_reminders(
        self, client_id: str, after_message_id: str
    ) -> int:
        """
        Cancel pending reminders for messages created after this one
        
        Returns:
            Number of cancelled reminders
        """
        cancelled = await self.reminder_service.cancel_client_reminders(
            client_id=client_id,
            after_message_id=after_message_id,
        )
        if cancelled > 0:
            logger.debug(
                f"Cancelled {cancelled} pending reminders for {client_id}"
            )
        return cancelled

    async def finalize_message_processing(
        self, processed_message: ProcessedMessage
    ) -> None:
        """
        Finalize message processing:
        - Mark message as processed
        - Create reminders
        - Cancel old reminders
        """
        # Mark original as processed
        processed_message.original_message.is_processed = True

        # Create reminders if needed
        await self.create_reminders(
            client_id=processed_message.original_message.client_id,
            message_id=str(processed_message.original_message.id),
            requires_escalation=processed_message.requires_escalation,
            scenario=processed_message.scenario,
        )

        # Cancel pending reminders for messages created after this one
        await self.cancel_pending_reminders(
            client_id=processed_message.original_message.client_id,
            after_message_id=str(processed_message.original_message.id),
        )


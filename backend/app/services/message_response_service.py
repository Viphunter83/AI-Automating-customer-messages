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
        is_first_message = processed_message.is_first_message
        scenario_msg = None  # Initialize to avoid NameError

        # If this is the first message, always send greeting first (per TZ requirement)
        greeting_msg = None
        if is_first_message and scenario != "GREETING":
            # Send automatic greeting for first-time clients
            greeting_msg, greeting_text = await self.response_manager.create_bot_response(
                scenario="GREETING",
                client_id=client_id,
                original_message_id=str(processed_message.original_message.id),
                params={},
                message_type=MessageType.BOT_AUTO,
            )
            if greeting_msg:
                logger.info(f"✅ Sent automatic greeting for first-time client {client_id}")

        # For escalated scenarios, send appropriate response
        # Special handling for TECH_SUPPORT_BASIC: send scenario template first (with screenshot request)
        # Other scenarios: send escalation notification
        if requires_escalation:
            # For TECH_SUPPORT_BASIC, send scenario template first (includes screenshot request)
            # This follows TZ requirement: first send instructions + screenshot request, then escalate
            if scenario == "TECH_SUPPORT_BASIC":
                # Send TECH_SUPPORT_BASIC template (includes screenshot request)
                response_msg, response_text = await self.response_manager.create_bot_response(
                    scenario="TECH_SUPPORT_BASIC",
                    client_id=client_id,
                    original_message_id=str(processed_message.original_message.id),
                    params={},
                    message_type=MessageType.BOT_ESCALATED,  # Mark as escalated for operator notification
                )
                
                # If first message, combine greeting with tech support response
                if is_first_message and not greeting_msg:
                    greeting_msg, greeting_text = await self.response_manager.create_bot_response(
                        scenario="GREETING",
                        client_id=client_id,
                        original_message_id=str(processed_message.original_message.id),
                        params={},
                        message_type=MessageType.BOT_AUTO,
                    )
                
                if is_first_message and greeting_msg:
                    # Combine greeting with tech support response
                    combined_text = f"{greeting_text}\n\n{response_text}"
                    response_msg.content = combined_text
                    response_text = combined_text
                    logger.info(f"✅ Combined greeting with TECH_SUPPORT_BASIC response for first-time client")
                
                logger.info(f"📤 Created TECH_SUPPORT_BASIC response (with screenshot request) for client {client_id}")
            else:
                # For other escalated scenarios, send escalation notification
                response_msg, response_text = await self.response_manager.create_bot_response(
                    scenario="ESCALATED",
                    client_id=client_id,
                    original_message_id=str(processed_message.original_message.id),
                    params={},
                    message_type=MessageType.BOT_ESCALATED,
                )
                
                # If first message, combine greeting with escalation message
                if is_first_message and not greeting_msg:
                    greeting_msg, greeting_text = await self.response_manager.create_bot_response(
                        scenario="GREETING",
                        client_id=client_id,
                        original_message_id=str(processed_message.original_message.id),
                        params={},
                        message_type=MessageType.BOT_AUTO,
                    )
                
                if is_first_message and greeting_msg:
                    # Combine greeting with escalation message
                    combined_text = f"{greeting_msg.content}\n\n{response_text}"
                    response_msg.content = combined_text
                    response_text = combined_text
                    logger.info(f"✅ Combined greeting with escalation response for first-time client")

                # Note: scenario_msg is created for operator context only (stored in DB)
                # It should NOT be sent to client - only ESCALATED message is sent
                # The scenario-specific template is used for operator reference in the dashboard
                logger.info(f"📤 Created escalation response for client {client_id}")

                # Create scenario-specific response for operator context (NOT sent to client)
                # This is stored in DB for operator reference but not delivered via webhook
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
                        f"Created scenario response for operator context only (not sent to client): {scenario_msg.id}"
                    )
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
            
            # If this is first message and scenario is not GREETING, combine greeting with response
            if is_first_message and greeting_msg and scenario != "GREETING":
                # Combine greeting text with scenario response text
                combined_text = f"{greeting_msg.content}\n\n{response_text}"
                # Update response message content
                response_msg.content = combined_text
                response_text = combined_text
                logger.info(f"✅ Combined greeting with {scenario} response for first-time client")

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
        
        # Add reminder for next day (per TZ requirement)
        await self.reminder_service.create_reminder(
            client_id=client_id,
            message_id=message_id,
            reminder_type=ReminderType.REMINDER_1DAY,
        )

        logger.debug(f"Created reminders (15min, 30min, 1day) for message {message_id}")

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


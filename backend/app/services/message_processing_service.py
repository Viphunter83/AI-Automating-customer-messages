"""
Message Processing Service
Handles the core logic of processing incoming messages
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    Classification,
    EscalationReason,
    Message,
    MessageType,
    PriorityLevel,
    ScenarioType,
)
from app.services.ai_classifier import AIClassifier
from app.services.dialog_auto_close import DialogAutoCloseService
from app.services.escalation_manager import EscalationManager
from app.services.mass_outage_detector import MassOutageDetector
from app.services.text_processor import TextProcessor

logger = logging.getLogger(__name__)


class ProcessedMessage:
    """Result of message processing"""
    def __init__(
        self,
        original_message: Message,
        classification: Optional[Classification],
        scenario: str,
        confidence: float,
        requires_escalation: bool,
        priority: PriorityLevel,
        escalation_reason: Optional[EscalationReason],
        is_first_message: bool,
        processed_text: str,
        priority_queue: int = 10,
    ):
        self.original_message = original_message
        self.classification = classification
        self.scenario = scenario
        self.confidence = confidence
        self.requires_escalation = requires_escalation
        self.priority = priority
        self.escalation_reason = escalation_reason
        self.is_first_message = is_first_message
        self.processed_text = processed_text
        self.priority_queue = priority_queue


class MessageProcessingService:
    """Service for processing incoming messages"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.text_processor = TextProcessor()
        self.ai_classifier = AIClassifier()
        self.dialog_service = DialogAutoCloseService(session)

    async def check_duplicate(
        self, client_id: str, content: str, time_window_seconds: int = 5
    ) -> Optional[Message]:
        """
        Check for duplicate messages
        
        Returns:
            Duplicate message if found, None otherwise
        """
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window_seconds)
        
        result = await self.session.execute(
            select(Message)
            .where(
                Message.client_id == client_id,
                Message.content == content,
                Message.created_at >= cutoff_time,
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        
        return result.scalar_one_or_none()

    async def check_rate_limit(
        self, client_id: str, limit_per_minute: int
    ) -> bool:
        """
        Check if client has exceeded rate limit
        
        Returns:
            True if within limit, False if exceeded
        """
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        result = await self.session.execute(
            select(func.count(Message.id)).where(
                Message.client_id == client_id,
                Message.created_at >= one_minute_ago,
            )
        )
        count = result.scalar_one()
        return count < limit_per_minute

    async def determine_first_message(self, client_id: str) -> bool:
        """
        Determine if this is the first message from client
        Uses SELECT FOR UPDATE to prevent race conditions
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.client_id == client_id)
            .with_for_update()  # Wait for locks, don't skip
        )
        existing_messages = result.scalars().all()
        return len(existing_messages) == 0

    async def save_original_message(
        self, client_id: str, content: str, is_first_message: bool
    ) -> Message:
        """Save original message to database"""
        message = Message(
            id=uuid4(),
            client_id=client_id,
            content=content,
            message_type=MessageType.USER,
            is_processed=False,
            is_first_message=is_first_message,
        )
        self.session.add(message)
        await self.session.flush()
        
        # Update dialog activity
        await self.dialog_service.update_activity(client_id)
        
        logger.debug(
            f"✅ Saved original message: {message.id} "
            f"(first_message={is_first_message})"
        )
        return message

    async def process_text(self, text: str) -> Optional[str]:
        """
        Process and clean text
        
        Returns:
            Processed text or None if detected as noise
        """
        processed = self.text_processor.process(text)
        if not processed:
            logger.warning("Processed text is empty (noise detected)")
        return processed

    async def classify_message(
        self, processed_text: str, client_id: str
    ) -> Dict:
        """
        Classify message using AI or mass outage detection
        
        Returns:
            Classification result dict
        """
        # Check for mass outage first
        mass_outage_detector = MassOutageDetector(self.session)
        mass_outage_result = await mass_outage_detector.detect_mass_outage(
            current_message=processed_text,
            current_client_id=client_id,
        )

        if mass_outage_result.get("is_mass_outage"):
            logger.warning(
                f"🚨 Mass outage detected! Overriding classification to MASS_OUTAGE. "
                f"Similar messages: {mass_outage_result.get('similar_messages_count')}"
            )
            return {
                "success": True,
                "scenario": "MASS_OUTAGE",
                "confidence": 0.95,
                "reasoning": f"Mass outage detected: {mass_outage_result.get('similar_messages_count')} similar messages",
                "model": "mass_outage_detector",
            }

        # Normal AI classification
        return await self.ai_classifier.classify(
            message=processed_text, client_id=client_id
        )

    async def save_classification(
        self,
        message: Message,
        scenario: str,
        confidence: float,
        ai_model: str,
        reasoning: Optional[str],
    ) -> Classification:
        """Save classification to database"""
        classification = Classification(
            id=uuid4(),
            message_id=message.id,
            detected_scenario=ScenarioType[scenario],
            confidence=confidence,
            ai_model=ai_model,
            reasoning=reasoning,
        )
        self.session.add(classification)
        await self.session.flush()
        logger.debug(f"✅ Saved classification: {classification.id}")
        return classification

    async def evaluate_escalation(
        self,
        message_id: str,
        scenario: str,
        confidence: float,
        client_id: str,
        content: str,
    ) -> Dict:
        """
        Evaluate if message should be escalated
        
        Returns:
            Escalation result dict with should_escalate, level, reasons, etc.
        """
        escalation_manager = EscalationManager(self.session)
        escalation_result = await escalation_manager.evaluate_escalation(
            message_id=message_id,
            scenario=scenario,
            confidence=confidence,
            client_id=client_id,
        )

        # Check scenario-specific escalation rules
        escalation_scenarios = [
            "SCHEDULE_CHANGE",
            "COMPLAINT",
            "MISSING_TRAINER",
            "CROSS_EXTENSION",
            "UNKNOWN",
        ]
        requires_escalation = (
            scenario in escalation_scenarios
            or (
                scenario == "REFERRAL"
                and any(char.isdigit() for char in content)
            )
            or escalation_result.get("should_escalate", False)
        )

        # Set priority and escalation reason
        priority_level_str = escalation_result.get("level", "low")
        try:
            priority_level = PriorityLevel(priority_level_str)
        except ValueError:
            logger.warning(
                f"Invalid priority level '{priority_level_str}', defaulting to 'low'"
            )
            priority_level = PriorityLevel.LOW

        escalation_reason = None
        reasons = escalation_result.get("reasons")
        if reasons and isinstance(reasons, list) and len(reasons) > 0:
            try:
                escalation_reason = EscalationReason(reasons[0])
            except (ValueError, IndexError):
                logger.warning(
                    f"Invalid escalation reason '{reasons[0] if reasons else None}'"
                )
                escalation_reason = None

        priority_queue = escalation_result.get("priority_queue", 10)
        
        return {
            "requires_escalation": requires_escalation,
            "priority": priority_level,
            "escalation_reason": escalation_reason,
            "priority_queue": priority_queue,
        }

    async def process_message(
        self, client_id: str, content: str, skip_duplicate_check: bool = False
    ) -> ProcessedMessage:
        """
        Main method to process a message
        
        Args:
            client_id: Client ID
            content: Message content
            skip_duplicate_check: If True, skip duplicate check (already done in endpoint)
        
        Returns:
            ProcessedMessage object with all processing results
        """
        # Check for duplicate (can be skipped if already checked in endpoint)
        if not skip_duplicate_check:
            duplicate = await self.check_duplicate(client_id, content)
            if duplicate:
                raise ValueError("DUPLICATE_MESSAGE")

        # Determine if first message
        is_first_message = await self.determine_first_message(client_id)

        # Save original message
        original_message = await self.save_original_message(
            client_id, content, is_first_message
        )

        # Process text
        processed_text = await self.process_text(content)
        if not processed_text:
            # Empty text - return early with fallback
            return ProcessedMessage(
                original_message=original_message,
                classification=None,
                scenario="UNKNOWN",
                confidence=0.0,
                requires_escalation=True,
                priority=PriorityLevel.LOW,
                escalation_reason=None,
                is_first_message=is_first_message,
                processed_text="",
                priority_queue=10,
            )

        # Classify message
        classification_result = await self.classify_message(
            processed_text, client_id
        )

        if not classification_result.get("success"):
            logger.error(
                f"❌ Classification failed: {classification_result.get('error')}"
            )
            return ProcessedMessage(
                original_message=original_message,
                classification=None,
                scenario="UNKNOWN",
                confidence=0.0,
                requires_escalation=True,
                priority=PriorityLevel.LOW,
                escalation_reason=EscalationReason.SYSTEM_ERROR,
                is_first_message=is_first_message,
                processed_text=processed_text,
                priority_queue=10,
            )

        scenario = classification_result.get("scenario")
        confidence = classification_result.get("confidence")

        # Save classification
        classification = await self.save_classification(
            original_message,
            scenario,
            confidence,
            classification_result.get("model", "openai_4o_mini"),
            classification_result.get("reasoning"),
        )

        # Evaluate escalation
        escalation_info = await self.evaluate_escalation(
            str(original_message.id),
            scenario,
            confidence,
            client_id,
            content,
        )

        # Update message with priority and escalation reason
        original_message.priority = escalation_info["priority"]
        original_message.escalation_reason = escalation_info["escalation_reason"]
        await self.session.flush()

        return ProcessedMessage(
            original_message=original_message,
            classification=classification,
            scenario=scenario,
            confidence=confidence,
            requires_escalation=escalation_info["requires_escalation"],
            priority=escalation_info["priority"],
            escalation_reason=escalation_info["escalation_reason"],
            is_first_message=is_first_message,
            processed_text=processed_text,
            priority_queue=escalation_info["priority_queue"],
        )


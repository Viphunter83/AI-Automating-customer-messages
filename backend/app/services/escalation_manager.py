import logging
import re
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Classification, Message, MessageType, ScenarioType

logger = logging.getLogger(__name__)


class EscalationLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    REPEATED_FAILED = "repeated_failed"
    COMPLAINT = "complaint"
    UNKNOWN_SCENARIO = "unknown_scenario"
    OPERATOR_MARKED = "operator_marked"
    SYSTEM_ERROR = "system_error"


class EscalationManager:
    """Manage message escalation with priority levels"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.confidence_threshold = 0.85

    def analyze_emotion(self, text: str) -> Dict[str, any]:
        """
        Analyze emotional tone of message
        
        Returns:
            {
                "is_negative": bool,
                "score": float (0-1, higher = more negative),
                "indicators": List[str]
            }
        """
        text_lower = text.lower()
        emotion_score = 0.0
        indicators = []
        
        # Негативные индикаторы из реальных данных
        negative_patterns = {
            r"!{2,}": 0.2,  # Множественные восклицательные знаки
            r"\?{2,}": 0.15,  # Множественные вопросительные знаки
            r"что происходит": 0.4,
            r"не предупредили": 0.5,
            r"недоволен": 0.5,
            r"плохо": 0.4,
            r"плох": 0.4,
            r"жалоб": 0.6,
            r"претензи": 0.6,
            r"некачественн": 0.5,
            r"не понравилось": 0.4,
            r"ужасн": 0.5,
            r"проблем": 0.3,
            r"не работает": 0.3,
            r"не могу": 0.2,
            r"не получил": 0.3,
            r"не пришло": 0.3,
        }
        
        for pattern, weight in negative_patterns.items():
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                emotion_score += weight * min(matches, 3)  # Cap at 3 matches
                indicators.append(pattern)
        
        # Эмодзи как индикаторы эмоций
        emoji_patterns = {
            r"😔|😢|😠|😡|😤": 0.3,  # Негативные эмодзи
            r"😊|😃|😄|🙂": -0.2,  # Позитивные эмодзи (снижают негатив)
        }
        
        for pattern, weight in emoji_patterns.items():
            if re.search(pattern, text):
                emotion_score += weight
        
        # Нормализация score (0-1)
        emotion_score = max(0.0, min(1.0, emotion_score))
        
        return {
            "is_negative": emotion_score > 0.5,
            "score": emotion_score,
            "indicators": indicators[:5]  # Первые 5 индикаторов
        }

    async def evaluate_escalation(
        self, message_id: str, scenario: str, confidence: float, client_id: str, 
        message_content: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Evaluate if message should be escalated and at what priority

        Returns:
            {
                "should_escalate": bool,
                "level": "low|medium|high|critical",
                "reason": str,
                "priority_queue": int (1-10, where 1 is highest)
            }
        """
        reasons = []
        base_level = EscalationLevel.LOW

        # Check 1: Low confidence
        if confidence < self.confidence_threshold:
            reasons.append(EscalationReason.LOW_CONFIDENCE)
            base_level = EscalationLevel.MEDIUM

        # Check 2: Unknown scenario
        if scenario == "UNKNOWN":
            reasons.append(EscalationReason.UNKNOWN_SCENARIO)
            base_level = EscalationLevel.HIGH

        # Check 3: Repeated failures from same client
        recent_failures = await self._get_recent_failures(client_id, hours=2)
        if recent_failures >= 2:
            reasons.append(EscalationReason.REPEATED_FAILED)
            base_level = (
                EscalationLevel.HIGH if len(reasons) > 1 else EscalationLevel.MEDIUM
            )

        # Check 3.5: Repeated requests in short time (new trigger)
        recent_requests = await self._get_recent_requests(client_id, minutes=10)
        if recent_requests >= 3:
            reasons.append(EscalationReason.REPEATED_FAILED)
            base_level = EscalationLevel.HIGH
            logger.warning(
                f"⚠️ Repeated requests trigger: client {client_id} sent {recent_requests} "
                f"messages in last 10 minutes - escalating"
            )

        # Check 4: Check if client has complaints
        if await self._has_recent_escalations(client_id, hours=1):
            reasons.append(EscalationReason.COMPLAINT)
            base_level = EscalationLevel.CRITICAL
        
        # Check 5: Analyze emotional tone (новое на основе реальных данных)
        emotion_data = None
        if message_content:
            emotion_data = self.analyze_emotion(message_content)
            if emotion_data["is_negative"]:
                reasons.append(EscalationReason.COMPLAINT)
                # Повысить приоритет если негативные эмоции
                if base_level == EscalationLevel.LOW:
                    base_level = EscalationLevel.MEDIUM
                elif base_level == EscalationLevel.MEDIUM:
                    base_level = EscalationLevel.HIGH
                elif base_level == EscalationLevel.HIGH:
                    base_level = EscalationLevel.CRITICAL
                logger.info(
                    f"⚠️ Negative emotion detected (score: {emotion_data['score']:.2f}) "
                    f"for client {client_id}, escalating"
                )

        return {
            "should_escalate": len(reasons) > 0 or confidence < 0.7,
            "level": base_level.value,
            "reasons": [r.value for r in reasons],
            "priority_queue": self._get_priority_queue(base_level),
            "confidence": confidence,
            "emotion_analysis": emotion_data,
        }

    async def _get_recent_requests(self, client_id: str, minutes: int = 10) -> int:
        """Count recent messages from client (for repeated requests trigger)"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        result = await self.session.execute(
            select(Message).where(
                and_(
                    Message.client_id == client_id,
                    Message.created_at >= cutoff_time,
                    Message.message_type == MessageType.USER,
                )
            )
        )

        return len(result.scalars().all())

    async def _get_recent_failures(self, client_id: str, hours: int = 2) -> int:
        """Count classifications with low confidence for client"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        result = await self.session.execute(
            select(Classification)
            .join(Message)
            .where(
                and_(
                    Message.client_id == client_id,
                    Classification.created_at >= cutoff_time,
                    Classification.confidence < 0.70,
                )
            )
        )

        return len(result.scalars().all())

    async def _has_recent_escalations(self, client_id: str, hours: int = 1) -> bool:
        """Check if client has recent escalations"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        result = await self.session.execute(
            select(Message).where(
                and_(
                    Message.client_id == client_id,
                    Message.message_type == MessageType.BOT_ESCALATED,
                    Message.created_at >= cutoff_time,
                )
            )
        )

        return len(result.scalars().all()) > 0

    def _get_priority_queue(self, level: EscalationLevel) -> int:
        """Get priority queue position (1 is highest)"""
        priority_map = {
            EscalationLevel.LOW: 10,
            EscalationLevel.MEDIUM: 7,
            EscalationLevel.HIGH: 3,
            EscalationLevel.CRITICAL: 1,
        }
        return priority_map.get(level, 10)

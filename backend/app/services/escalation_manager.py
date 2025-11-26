import logging
from typing import Dict, List, Optional
from enum import Enum
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Message, MessageType, Classification, ScenarioType
from datetime import datetime, timedelta
import uuid

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
    
    async def evaluate_escalation(
        self,
        message_id: str,
        scenario: str,
        confidence: float,
        client_id: str
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
            base_level = EscalationLevel.HIGH if len(reasons) > 1 else EscalationLevel.MEDIUM
        
        # Check 4: Check if client has complaints
        if await self._has_recent_escalations(client_id, hours=1):
            reasons.append(EscalationReason.COMPLAINT)
            base_level = EscalationLevel.CRITICAL
        
        return {
            "should_escalate": len(reasons) > 0 or confidence < 0.7,
            "level": base_level.value,
            "reasons": [r.value for r in reasons],
            "priority_queue": self._get_priority_queue(base_level),
            "confidence": confidence,
        }
    
    async def _get_recent_failures(
        self,
        client_id: str,
        hours: int = 2
    ) -> int:
        """Count classifications with low confidence for client"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.session.execute(
            select(Classification)
            .join(Message)
            .where(
                and_(
                    Message.client_id == client_id,
                    Classification.created_at >= cutoff_time,
                    Classification.confidence < 0.70
                )
            )
        )
        
        return len(result.scalars().all())
    
    async def _has_recent_escalations(
        self,
        client_id: str,
        hours: int = 1
    ) -> bool:
        """Check if client has recent escalations"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.session.execute(
            select(Message)
            .where(
                and_(
                    Message.client_id == client_id,
                    Message.message_type == MessageType.BOT_ESCALATED,
                    Message.created_at >= cutoff_time
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


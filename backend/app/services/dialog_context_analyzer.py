"""
Dialog Context Analyzer
Analyzes dialog history to provide context-aware responses
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Message, MessageType

logger = logging.getLogger(__name__)


class DialogContextAnalyzer:
    """Analyze dialog history for context-aware responses"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_dialog_context(
        self, client_id: str, limit: int = 10
    ) -> Dict[str, any]:
        """
        Get context from recent dialog history
        
        Returns:
            {
                "message_count": int,
                "last_scenario": Optional[str],
                "recent_topics": List[str],
                "has_escalation": bool,
                "last_operator_response": Optional[str],
                "is_continuation": bool,  # Is this a continuation of previous topic?
            }
        """
        # Get recent messages
        result = await self.session.execute(
            select(Message)
            .where(Message.client_id == client_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        messages = result.scalars().all()
        
        if not messages:
            return {
                "message_count": 0,
                "last_scenario": None,
                "recent_topics": [],
                "has_escalation": False,
                "last_operator_response": None,
                "is_continuation": False,
            }
        
        # Analyze messages
        message_count = len(messages)
        has_escalation = any(
            msg.message_type == MessageType.BOT_ESCALATED 
            for msg in messages
        )
        
        # Get last operator response
        last_operator_response = None
        for msg in messages:
            if msg.message_type == MessageType.OPERATOR:
                last_operator_response = msg.content[:200]  # Preview
                break
        
        # Get last scenario from classifications
        from app.models.database import Classification
        last_classification_result = await self.session.execute(
            select(Classification)
            .join(Message)
            .where(Message.client_id == client_id)
            .order_by(desc(Classification.created_at))
            .limit(1)
        )
        last_classification = last_classification_result.scalar_one_or_none()
        last_scenario = last_classification.detected_scenario.value if last_classification else None
        
        # Determine if this is continuation
        # If last message was from client and recent (within 1 hour), likely continuation
        is_continuation = False
        if len(messages) > 1:
            last_client_msg = messages[0]  # Most recent
            if (last_client_msg.message_type == MessageType.USER and
                (datetime.utcnow() - last_client_msg.created_at).total_seconds() < 3600):
                is_continuation = True
        
        # Extract recent topics (simple keyword extraction)
        recent_topics = []
        for msg in messages[:5]:  # Last 5 messages
            content_lower = msg.content.lower()
            if "отсутствие" in content_lower or "пропуск" in content_lower:
                recent_topics.append("absence")
            elif "расписание" in content_lower or "перенос" in content_lower:
                recent_topics.append("schedule")
            elif "тренер" in content_lower:
                recent_topics.append("trainer")
            elif "ссылка" in content_lower or "пароль" in content_lower:
                recent_topics.append("technical")
        
        return {
            "message_count": message_count,
            "last_scenario": last_scenario,
            "recent_topics": list(set(recent_topics)),  # Unique topics
            "has_escalation": has_escalation,
            "last_operator_response": last_operator_response,
            "is_continuation": is_continuation,
        }
    
    async def should_combine_with_previous(
        self, client_id: str, current_scenario: str
    ) -> bool:
        """
        Determine if current response should reference previous messages
        
        Returns:
            True if should combine/reference previous context
        """
        context = await self.get_dialog_context(client_id)
        
        # If continuation and same scenario, reference previous
        if context["is_continuation"] and context["last_scenario"] == current_scenario:
            return True
        
        # If recent escalation, reference it
        if context["has_escalation"]:
            return True
        
        return False








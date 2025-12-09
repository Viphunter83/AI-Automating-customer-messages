import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Classification, Message, MessageType, ScenarioType

logger = logging.getLogger(__name__)


class MassOutageDetector:
    """Detect mass platform outages by analyzing similar messages"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.similarity_threshold = 0.7  # Messages are similar if >70% match
        self.time_window_minutes = 10  # Analyze messages from last 10 minutes (TZ requirement)
        self.mass_threshold = 5  # Need at least 5 similar messages to trigger (TZ requirement)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1)"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    async def detect_mass_outage(
        self, current_message: str, current_client_id: str
    ) -> Dict[str, any]:
        """
        Detect if current message indicates a mass outage

        Args:
            current_message: The message to analyze
            current_client_id: Client ID of current message

        Returns:
            {
                "is_mass_outage": bool,
                "similar_messages_count": int,
                "similarity_score": float,
                "detected_at": datetime
            }
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.time_window_minutes)

        # Get recent messages from different clients
        result = await self.session.execute(
            select(Message)
            .where(
                and_(
                    Message.created_at >= cutoff_time,
                    Message.message_type
                    == MessageType.USER,  # Use enum instead of string
                    Message.client_id != current_client_id,  # Exclude current client
                )
            )
            .order_by(Message.created_at.desc())
            .limit(100)  # Analyze last 100 messages
        )
        recent_messages = result.scalars().all()

        if len(recent_messages) < self.mass_threshold:
            return {
                "is_mass_outage": False,
                "similar_messages_count": len(recent_messages),
                "similarity_score": 0.0,
                "detected_at": datetime.utcnow(),
            }

        # Find similar messages
        similar_count = 0
        total_similarity = 0.0

        for msg in recent_messages:
            similarity = self._calculate_similarity(current_message, msg.content)
            if similarity >= self.similarity_threshold:
                similar_count += 1
                total_similarity += similarity

        avg_similarity = total_similarity / similar_count if similar_count > 0 else 0.0

        is_mass_outage = similar_count >= self.mass_threshold

        if is_mass_outage:
            logger.warning(
                f"🚨 MASS_OUTAGE detected! {similar_count} similar messages in last "
                f"{self.time_window_minutes} minutes (avg similarity: {avg_similarity:.2f})"
            )

        return {
            "is_mass_outage": is_mass_outage,
            "similar_messages_count": similar_count,
            "similarity_score": avg_similarity,
            "detected_at": datetime.utcnow(),
        }

    async def get_mass_outage_stats(self) -> Dict[str, any]:
        """Get statistics about potential mass outages"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.time_window_minutes)

        # Get recent messages grouped by content similarity
        result = await self.session.execute(
            select(
                Message.content,
                func.count(Message.id).label("count"),
                func.count(func.distinct(Message.client_id)).label("unique_clients"),
            )
            .where(
                and_(
                    Message.created_at >= cutoff_time,
                    Message.message_type
                    == MessageType.USER,  # Use enum instead of string
                )
            )
            .group_by(Message.content)
            .having(func.count(Message.id) >= 5)  # At least 5 similar messages
            .order_by(func.count(Message.id).desc())
            .limit(10)
        )

        potential_outages = result.all()

        return {
            "potential_outages": [
                {
                    "content": row.content[:100],  # First 100 chars
                    "message_count": row.count,
                    "unique_clients": row.unique_clients,
                }
                for row in potential_outages
            ],
            "time_window_minutes": self.time_window_minutes,
            "checked_at": datetime.utcnow(),
        }

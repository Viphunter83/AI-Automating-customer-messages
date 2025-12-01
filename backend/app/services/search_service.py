import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import Classification, Message, OperatorFeedback, ScenarioType

logger = logging.getLogger(__name__)


class SearchService:
    """Search and filter messages and dialogs"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_messages(
        self,
        query: str,
        client_id: Optional[str] = None,
        scenario: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, any]:
        """
        Full-text search on messages

        Args:
            query: Search text
            client_id: Filter by client
            scenario: Filter by scenario
            min_confidence: Minimum confidence threshold
            limit: Results per page
            offset: Pagination offset
        """
        conditions = []

        # Text search
        if query:
            conditions.append(Message.content.ilike(f"%{query}%"))

        # Client filter
        if client_id:
            conditions.append(Message.client_id == client_id)

        # Build base query
        query_obj = select(Message)

        if conditions:
            query_obj = query_obj.where(and_(*conditions))

        # Scenario filter (requires join)
        if scenario:
            try:
                scenario_enum = ScenarioType[scenario]
                query_obj = query_obj.join(Classification).where(
                    Classification.detected_scenario == scenario_enum,
                    Classification.confidence >= min_confidence,
                )
            except KeyError:
                logger.warning(f"Invalid scenario: {scenario}")

        # Count total
        count_query = select(func.count(Message.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        if scenario:
            try:
                scenario_enum = ScenarioType[scenario]
                count_query = count_query.join(Classification).where(
                    Classification.detected_scenario == scenario_enum,
                    Classification.confidence >= min_confidence,
                )
            except KeyError:
                pass

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get results
        query_obj = query_obj.order_by(desc(Message.created_at))
        query_obj = query_obj.limit(limit).offset(offset)

        result = await self.session.execute(query_obj)
        messages = result.scalars().unique().all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(messages),
            "messages": [
                {
                    "id": str(m.id),
                    "client_id": m.client_id,
                    "content": m.content,
                    "message_type": str(m.message_type.value),
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
        }

    async def search_dialogs(
        self,
        min_messages: int = 1,
        has_feedback: Optional[bool] = None,
        hours: int = 24,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Find dialogs matching criteria

        Returns dialogs with statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Get distinct clients with message counts
        result = await self.session.execute(
            select(
                Message.client_id,
                func.count(Message.id).label("message_count"),
                func.min(Message.created_at).label("first_message"),
                func.max(Message.created_at).label("last_message"),
            )
            .where(Message.created_at >= cutoff_time)
            .group_by(Message.client_id)
            .having(func.count(Message.id) >= min_messages)
            .order_by(desc(func.max(Message.created_at)))
            .limit(limit)
        )

        rows = result.all()
        dialogs = []

        # Collect all client_ids
        client_ids = [row.client_id for row in rows]

        if not client_ids:
            return dialogs

        # Batch load all classifications for all clients (prevent N+1)
        # Use JOIN to get client_id directly without separate queries
        class_result = await self.session.execute(
            select(Classification, Message.client_id)
            .join(Message, Classification.message_id == Message.id)
            .where(Message.client_id.in_(client_ids))
        )
        all_classifications_data = class_result.all()
        classifications_by_client = {}
        for c, client_id in all_classifications_data:
            if client_id not in classifications_by_client:
                classifications_by_client[client_id] = []
            classifications_by_client[client_id].append(c)

        # Batch load all feedbacks for all clients (prevent N+1)
        # Use JOIN to get client_id directly without separate queries
        feedback_result = await self.session.execute(
            select(OperatorFeedback, Message.client_id)
            .join(Message, OperatorFeedback.message_id == Message.id)
            .where(Message.client_id.in_(client_ids))
        )
        all_feedbacks_data = feedback_result.all()
        feedbacks_by_client = {}
        for f, client_id in all_feedbacks_data:
            if client_id not in feedbacks_by_client:
                feedbacks_by_client[client_id] = []
            feedbacks_by_client[client_id].append(f)

        for row in rows:
            client_id = row.client_id
            msg_count = row.message_count
            first_msg = row.first_message
            last_msg = row.last_message

            # Get pre-loaded classifications and feedbacks
            classifications = classifications_by_client.get(client_id, [])
            feedbacks = feedbacks_by_client.get(client_id, [])

            # Filter by feedback if requested
            if has_feedback is not None:
                if has_feedback and len(feedbacks) == 0:
                    continue
                if not has_feedback and len(feedbacks) > 0:
                    continue

            # Calculate stats
            avg_confidence = (
                sum(c.confidence for c in classifications) / len(classifications)
                if classifications
                else 0
            )

            dialogs.append(
                {
                    "client_id": client_id,
                    "message_count": msg_count,
                    "first_message_at": first_msg.isoformat(),
                    "last_message_at": last_msg.isoformat(),
                    "avg_confidence": avg_confidence,
                    "feedback_count": len(feedbacks),
                    "scenarios": list(
                        set(str(c.detected_scenario.value) for c in classifications)
                    ),
                }
            )

        return dialogs

    async def autocomplete_clients(self, prefix: str, limit: int = 10) -> List[str]:
        """Autocomplete client IDs"""
        result = await self.session.execute(
            select(func.distinct(Message.client_id))
            .where(Message.client_id.ilike(f"{prefix}%"))
            .limit(limit)
        )

        return result.scalars().all()

import logging
import csv
import json
from typing import List, Dict, Optional
from io import StringIO, BytesIO
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Message, Classification, OperatorFeedback
from datetime import datetime

logger = logging.getLogger(__name__)

class ExportService:
    """Export data in various formats"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def export_dialog_csv(
        self,
        client_id: str
    ) -> str:
        """Export client dialog as CSV"""
        
        # Get messages
        msg_result = await self.session.execute(
            select(Message).where(Message.client_id == client_id)
            .order_by(Message.created_at)
        )
        messages = msg_result.scalars().all()
        
        # Get classifications
        class_result = await self.session.execute(
            select(Classification)
            .join(Message)
            .where(Message.client_id == client_id)
        )
        classifications_dict = {str(c.message_id): c for c in class_result.scalars().all()}
        
        # Build CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Timestamp', 'Message Type', 'Content', 'Scenario', 'Confidence', 'Reasoning'
        ])
        
        for msg in messages:
            classification = classifications_dict.get(str(msg.id))
            writer.writerow([
                msg.created_at.isoformat(),
                str(msg.message_type.value),
                msg.content,
                str(classification.detected_scenario.value) if classification else 'N/A',
                f"{classification.confidence:.2%}" if classification else 'N/A',
                classification.reasoning or '' if classification else ''
            ])
        
        return output.getvalue()
    
    async def export_dialog_json(
        self,
        client_id: str
    ) -> Dict:
        """Export client dialog as JSON"""
        
        msg_result = await self.session.execute(
            select(Message).where(Message.client_id == client_id)
            .order_by(Message.created_at)
        )
        messages = msg_result.scalars().all()
        
        class_result = await self.session.execute(
            select(Classification)
            .join(Message)
            .where(Message.client_id == client_id)
        )
        classifications_dict = {str(c.message_id): c for c in class_result.scalars().all()}
        
        feedback_result = await self.session.execute(
            select(OperatorFeedback)
            .join(Message)
            .where(Message.client_id == client_id)
        )
        feedbacks_dict = {str(f.message_id): f for f in feedback_result.scalars().all()}
        
        return {
            "client_id": client_id,
            "exported_at": datetime.utcnow().isoformat(),
            "message_count": len(messages),
            "messages": [
                {
                    "id": str(msg.id),
                    "timestamp": msg.created_at.isoformat(),
                    "type": str(msg.message_type.value),
                    "content": msg.content,
                    "classification": (
                        {
                            "scenario": str(classifications_dict[str(msg.id)].detected_scenario.value),
                            "confidence": classifications_dict[str(msg.id)].confidence,
                            "reasoning": classifications_dict[str(msg.id)].reasoning
                        } if str(msg.id) in classifications_dict else None
                    ),
                    "feedback": (
                        {
                            "type": feedbacks_dict[str(msg.id)].feedback_type,
                            "suggested": str(feedbacks_dict[str(msg.id)].suggested_scenario.value) if feedbacks_dict[str(msg.id)].suggested_scenario else None,
                            "comment": feedbacks_dict[str(msg.id)].comment
                        } if str(msg.id) in feedbacks_dict else None
                    )
                }
                for msg in messages
            ]
        }
    
    async def export_analytics_report(
        self,
        hours: int = 24
    ) -> Dict:
        """Generate analytics report"""
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Message stats
        msg_result = await self.session.execute(
            select(Message).where(Message.created_at >= cutoff_time)
        )
        messages = msg_result.scalars().all()
        
        # Classification stats
        class_result = await self.session.execute(
            select(Classification).join(Message)
            .where(Message.created_at >= cutoff_time)
        )
        classifications = class_result.scalars().all()
        
        # Feedback stats
        feedback_result = await self.session.execute(
            select(OperatorFeedback).join(Message)
            .where(Message.created_at >= cutoff_time)
        )
        feedbacks = feedback_result.scalars().all()
        
        correct_feedback = sum(1 for f in feedbacks if f.feedback_type == "correct")
        incorrect_feedback = sum(1 for f in feedbacks if f.feedback_type == "incorrect")
        
        # Group by scenario
        scenario_counts = {}
        for c in classifications:
            scenario = str(c.detected_scenario.value)
            scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
        
        # Group by message type
        type_counts = {}
        for m in messages:
            msg_type = str(m.message_type.value)
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
        
        return {
            "period": {
                "hours": hours,
                "start": cutoff_time.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "messages": {
                "total": len(messages),
                "by_type": type_counts
            },
            "classifications": {
                "total": len(classifications),
                "avg_confidence": sum(c.confidence for c in classifications) / len(classifications) if classifications else 0,
                "by_scenario": scenario_counts
            },
            "feedback": {
                "total": len(feedbacks),
                "correct": correct_feedback,
                "incorrect": incorrect_feedback,
                "accuracy_rate": correct_feedback / len(feedbacks) if feedbacks else 0
            }
        }


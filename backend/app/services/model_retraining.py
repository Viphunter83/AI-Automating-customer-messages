import logging
from typing import Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import OperatorFeedback, Classification, Message, ResponseTemplate, ScenarioType
from app.utils.prompts import RESPONSE_TEMPLATES
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ModelRetrainingService:
    """Manage model retraining based on operator feedback"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_feedback_summary(
        self,
        hours: int = 24
    ) -> Dict[str, any]:
        """
        Get summary of feedback from last N hours
        
        Returns:
            {
                "total_feedback": 10,
                "correct": 8,
                "incorrect": 2,
                "accuracy_rate": 0.80,
                "scenarios": {
                    "GREETING": {"correct": 5, "incorrect": 1},
                    "REFERRAL": {"correct": 3, "incorrect": 1}
                }
            }
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get all feedback
        result = await self.session.execute(
            select(OperatorFeedback).where(
                OperatorFeedback.created_at >= cutoff_time
            )
        )
        feedbacks = result.scalars().all()
        
        if not feedbacks:
            return {
                "total_feedback": 0,
                "correct": 0,
                "incorrect": 0,
                "accuracy_rate": 0.0,
                "scenarios": {},
            }
        
        # Calculate stats
        correct_count = sum(1 for f in feedbacks if f.feedback_type == "correct")
        incorrect_count = sum(1 for f in feedbacks if f.feedback_type == "incorrect")
        
        # Group by scenario
        scenario_stats = {}
        for feedback in feedbacks:
            if feedback.classification_id:
                result = await self.session.execute(
                    select(Classification).where(
                        Classification.id == feedback.classification_id
                    )
                )
                classification = result.scalar_one_or_none()
                
                if classification:
                    scenario = str(classification.detected_scenario.value)
                    if scenario not in scenario_stats:
                        scenario_stats[scenario] = {"correct": 0, "incorrect": 0}
                    
                    if feedback.feedback_type == "correct":
                        scenario_stats[scenario]["correct"] += 1
                    elif feedback.feedback_type == "incorrect":
                        scenario_stats[scenario]["incorrect"] += 1
        
        return {
            "total_feedback": len(feedbacks),
            "correct": correct_count,
            "incorrect": incorrect_count,
            "accuracy_rate": correct_count / len(feedbacks) if feedbacks else 0,
            "scenarios": scenario_stats,
        }
    
    async def get_misclassified_messages(
        self,
        limit: int = 50
    ) -> List[Dict]:
        """Get messages that were incorrectly classified (optimized to prevent N+1 queries)"""
        
        # Load feedbacks with eager loading of related objects
        result = await self.session.execute(
            select(OperatorFeedback)
            .where(OperatorFeedback.feedback_type == "incorrect")
            .order_by(OperatorFeedback.created_at.desc())
            .limit(limit)
        )
        feedbacks = result.scalars().all()
        
        if not feedbacks:
            return []
        
        # Batch load all messages and classifications in one query each
        message_ids = [f.message_id for f in feedbacks if f.message_id]
        classification_ids = [f.classification_id for f in feedbacks if f.classification_id]
        
        # Load all messages at once
        messages_result = await self.session.execute(
            select(Message).where(Message.id.in_(message_ids))
        )
        messages_dict = {str(m.id): m for m in messages_result.scalars().all()}
        
        # Load all classifications at once
        classifications_dict = {}
        if classification_ids:
            classifications_result = await self.session.execute(
                select(Classification).where(Classification.id.in_(classification_ids))
            )
            classifications_dict = {str(c.id): c for c in classifications_result.scalars().all()}
        
        messages = []
        for feedback in feedbacks:
            message = messages_dict.get(str(feedback.message_id))
            classification = classifications_dict.get(str(feedback.classification_id)) if feedback.classification_id else None
            
            if message and classification:
                messages.append({
                    "message_id": str(message.id),
                    "content": message.content,
                    "detected_scenario": str(classification.detected_scenario.value),
                    "confidence": classification.confidence,
                    "suggested_scenario": str(feedback.suggested_scenario.value) if feedback.suggested_scenario else None,
                    "comment": feedback.comment,
                    "timestamp": classification.created_at.isoformat(),
                })
        
        return messages
    
    async def generate_retraining_data(
        self,
        feedback_type: str = "incorrect"
    ) -> Dict[str, any]:
        """
        Generate data for retraining the model
        
        Returns prompts and labels for fine-tuning
        """
        result = await self.session.execute(
            select(OperatorFeedback)
            .where(OperatorFeedback.feedback_type == feedback_type)
            .order_by(OperatorFeedback.created_at.desc())
            .limit(100)
        )
        feedbacks = result.scalars().all()
        
        training_samples = []
        
        for feedback in feedbacks:
            msg_result = await self.session.execute(
                select(Message).where(Message.id == feedback.message_id)
            )
            message = msg_result.scalar_one_or_none()
            
            if message:
                # Get previous classification
                prev_scenario = None
                if feedback.classification_id:
                    class_result = await self.session.execute(
                        select(Classification).where(Classification.id == feedback.classification_id)
                    )
                    prev_class = class_result.scalar_one_or_none()
                    if prev_class:
                        prev_scenario = str(prev_class.detected_scenario.value)
                
                training_samples.append({
                    "input": message.content,
                    "correct_label": str(feedback.suggested_scenario.value) if feedback.suggested_scenario else "UNKNOWN",
                    "previous_label": prev_scenario or "",
                    "feedback": feedback.comment or "",
                    "timestamp": feedback.created_at.isoformat(),
                })
        
        return {
            "model": "openai_4o_mini",
            "samples_count": len(training_samples),
            "samples": training_samples,
        }
    
    async def update_keywords_from_feedback(self) -> Dict[str, any]:
        """
        Extract and update keywords based on feedback patterns
        
        Identifies which words/phrases led to incorrect classifications
        """
        incorrect_msgs = await self.get_misclassified_messages(limit=100)
        
        # Group by suggested scenario
        keyword_map = {}
        
        for msg in incorrect_msgs:
            scenario = msg.get("suggested_scenario", "UNKNOWN")
            if scenario not in keyword_map:
                keyword_map[scenario] = []
            
            # Extract keywords from message
            words = msg["content"].lower().split()
            keyword_map[scenario].extend(words)
        
        # Calculate keyword frequency
        keyword_freq = {}
        for scenario, words in keyword_map.items():
            if scenario not in keyword_freq:
                keyword_freq[scenario] = {}
            
            for word in words:
                if len(word) > 3:  # Only words longer than 3 chars
                    keyword_freq[scenario][word] = keyword_freq[scenario].get(word, 0) + 1
        
        return {
            "updated_at": datetime.utcnow().isoformat(),
            "keyword_frequency": keyword_freq,
        }


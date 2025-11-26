from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import OperatorFeedbackCreate, OperatorFeedbackResponse
from app.models.database import OperatorFeedback
from app.database import get_session
from uuid import uuid4, UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

@router.post("/", response_model=OperatorFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_data: OperatorFeedbackCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Оператор отправляет фидбэк о правильности классификации.
    
    Expected JSON:
    {
        "message_id": "uuid",
        "classification_id": "uuid",
        "feedback_type": "correct|incorrect|needs_escalation",
        "suggested_scenario": "REFERRAL|null",
        "comment": "Комментарий оператора",
        "operator_id": "op_123"
    }
    """
    try:
        # Convert string UUIDs to UUID objects
        message_uuid = UUID(feedback_data.message_id)
        classification_uuid = UUID(feedback_data.classification_id) if feedback_data.classification_id else None
        
        feedback = OperatorFeedback(
            id=uuid4(),
            message_id=message_uuid,
            classification_id=classification_uuid,
            operator_id=feedback_data.operator_id,
            feedback_type=feedback_data.feedback_type,
            suggested_scenario=feedback_data.suggested_scenario,
            comment=feedback_data.comment,
        )
        
        session.add(feedback)
        await session.commit()
        
        logger.info(f"Feedback submitted: {feedback.id} by operator: {feedback_data.operator_id}")
        
        # TODO: Здесь можно запустить переобучение модели (в следующем промпте)
        
        return OperatorFeedbackResponse(
            id=str(feedback.id),
            message_id=str(feedback.message_id),
            feedback_type=feedback.feedback_type,
            suggested_scenario=feedback.suggested_scenario,
            comment=feedback.comment,
            operator_id=feedback.operator_id,
            created_at=feedback.created_at,
        )
    
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


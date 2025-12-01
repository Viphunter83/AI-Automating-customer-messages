"""
Monitoring and metrics endpoints
Provides basic system health and performance metrics
"""
import logging
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.database import Classification, Message, Reminder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ai-support-backend",
    }


@router.get("/metrics")
async def get_metrics(session: AsyncSession = Depends(get_session)) -> Dict:
    """
    Get system metrics for monitoring
    
    Returns:
        Dictionary with various system metrics
    """
    now = datetime.utcnow()
    last_hour = now - timedelta(hours=1)
    last_24h = now - timedelta(hours=24)
    
    metrics = {
        "timestamp": now.isoformat(),
        "messages": {},
        "classifications": {},
        "reminders": {},
        "performance": {},
    }
    
    try:
        # Message metrics
        total_messages = await session.execute(select(func.count(Message.id)))
        metrics["messages"]["total"] = total_messages.scalar() or 0
        
        messages_last_hour = await session.execute(
            select(func.count(Message.id)).where(Message.created_at >= last_hour)
        )
        metrics["messages"]["last_hour"] = messages_last_hour.scalar() or 0
        
        messages_last_24h = await session.execute(
            select(func.count(Message.id)).where(Message.created_at >= last_24h)
        )
        metrics["messages"]["last_24h"] = messages_last_24h.scalar() or 0
        
        # Classification metrics
        total_classifications = await session.execute(
            select(func.count(Classification.id))
        )
        metrics["classifications"]["total"] = total_classifications.scalar() or 0
        
        avg_confidence = await session.execute(
            select(func.avg(Classification.confidence))
            .where(Classification.created_at >= last_24h)
        )
        metrics["classifications"]["avg_confidence_24h"] = (
            float(avg_confidence.scalar()) if avg_confidence.scalar() else 0.0
        )
        
        # Reminder metrics
        pending_reminders = await session.execute(
            select(func.count(Reminder.id)).where(
                Reminder.sent_at.is_(None),
                Reminder.is_cancelled == False,
            )
        )
        metrics["reminders"]["pending"] = pending_reminders.scalar() or 0
        
        failed_reminders = await session.execute(
            select(func.count(Reminder.id)).where(
                Reminder.failed_attempts > 0,
                Reminder.sent_at.is_(None),
                Reminder.is_cancelled == False,
            )
        )
        metrics["reminders"]["failed"] = failed_reminders.scalar() or 0
        
        # Performance metrics (basic)
        metrics["performance"]["messages_per_hour"] = metrics["messages"]["last_hour"]
        metrics["performance"]["messages_per_day"] = metrics["messages"]["last_24h"]
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}", exc_info=True)
        metrics["error"] = str(e)
    
    return metrics


@router.get("/stats/summary")
async def get_stats_summary(session: AsyncSession = Depends(get_session)) -> Dict:
    """
    Get summary statistics for dashboard
    
    Returns:
        Summary statistics dictionary
    """
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    
    stats = {
        "timestamp": now.isoformat(),
        "total_messages": 0,
        "total_clients": 0,
        "messages_24h": 0,
        "avg_confidence_24h": 0.0,
        "pending_reminders": 0,
        "failed_reminders": 0,
    }
    
    try:
        # Total messages
        total_messages = await session.execute(select(func.count(Message.id)))
        stats["total_messages"] = total_messages.scalar() or 0
        
        # Unique clients
        unique_clients = await session.execute(
            select(func.count(func.distinct(Message.client_id)))
        )
        stats["total_clients"] = unique_clients.scalar() or 0
        
        # Messages in last 24h
        messages_24h = await session.execute(
            select(func.count(Message.id)).where(Message.created_at >= last_24h)
        )
        stats["messages_24h"] = messages_24h.scalar() or 0
        
        # Average confidence in last 24h
        avg_confidence = await session.execute(
            select(func.avg(Classification.confidence))
            .where(Classification.created_at >= last_24h)
        )
        stats["avg_confidence_24h"] = (
            float(avg_confidence.scalar()) if avg_confidence.scalar() else 0.0
        )
        
        # Pending reminders
        pending = await session.execute(
            select(func.count(Reminder.id)).where(
                Reminder.sent_at.is_(None),
                Reminder.is_cancelled == False,
            )
        )
        stats["pending_reminders"] = pending.scalar() or 0
        
        # Failed reminders
        failed = await session.execute(
            select(func.count(Reminder.id)).where(
                Reminder.failed_attempts > 0,
                Reminder.sent_at.is_(None),
                Reminder.is_cancelled == False,
            )
        )
        stats["failed_reminders"] = failed.scalar() or 0
        
    except Exception as e:
        logger.error(f"Error calculating stats: {e}", exc_info=True)
        stats["error"] = str(e)
    
    return stats


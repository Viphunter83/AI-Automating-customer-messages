import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.config import get_settings
from app.database import engine
from app.services.ai_classifier import AIClassifier
from app.services.reminder_scheduler import ReminderScheduler
from app.services.webhook_sender import WebhookSender

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    settings = get_settings()
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/health/db")
async def health_check_db():
    """Database health check"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()  # Ensure query executes

        # Check connection pool status
        pool = engine.pool
        pool_status = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }

        return {"status": "healthy", "database": "ok", "pool": pool_status}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


@router.get("/health/openai")
async def health_check_openai():
    """OpenAI API health check"""
    try:
        ai_classifier = AIClassifier()

        # Try a simple classification request with timeout
        test_result = await asyncio.wait_for(
            ai_classifier.classify("test", client_id="health_check"), timeout=5.0
        )

        if test_result.get("success"):
            return {
                "status": "healthy",
                "openai_api": "ok",
                "model": test_result.get("model", "unknown"),
            }
        else:
            return {
                "status": "degraded",
                "openai_api": "error",
                "error": test_result.get("error", "Unknown error"),
            }
    except asyncio.TimeoutError:
        logger.warning("OpenAI API health check timed out")
        return {
            "status": "degraded",
            "openai_api": "timeout",
            "error": "API request timed out",
        }
    except Exception as e:
        logger.error(f"OpenAI API health check failed: {e}")
        return {"status": "degraded", "openai_api": "error", "error": str(e)}


@router.get("/health/webhook")
async def health_check_webhook():
    """Webhook service health check"""
    try:
        webhook_sender = WebhookSender()

        # Check if webhook URL is configured
        webhook_url = webhook_sender.platform_webhook_url

        if not webhook_url or webhook_url == "http://localhost:9000/webhook/response":
            return {
                "status": "degraded",
                "webhook": "not_configured",
                "message": "Webhook URL not configured, using default",
            }

        return {
            "status": "healthy",
            "webhook": "configured",
            "url": webhook_url.split("@")[-1]
            if "@" in webhook_url
            else webhook_url[:50] + "..."
            if len(webhook_url) > 50
            else webhook_url,
        }
    except Exception as e:
        logger.error(f"Webhook health check failed: {e}")
        return {"status": "degraded", "webhook": "error", "error": str(e)}


@router.get("/health/scheduler")
async def health_check_scheduler():
    """Reminder scheduler health check"""
    try:
        # Note: This requires access to app.state, which might not be available in all contexts
        # For now, we'll just check if scheduler can be instantiated
        scheduler = ReminderScheduler()

        return {
            "status": "healthy",
            "scheduler": "available",
            "note": "Scheduler status requires app context",
        }
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        return {"status": "degraded", "scheduler": "error", "error": str(e)}


@router.get("/health/full")
async def health_check_full():
    """Comprehensive health check for all dependencies"""
    checks: Dict[str, Any] = {}
    overall_status = "healthy"

    # Database check
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"

    # OpenAI API check
    try:
        ai_classifier = AIClassifier()
        test_result = await asyncio.wait_for(
            ai_classifier.classify("test", client_id="health_check"), timeout=5.0
        )
        if test_result.get("success"):
            checks["openai"] = {"status": "healthy"}
        else:
            checks["openai"] = {"status": "degraded", "error": test_result.get("error")}
            if overall_status == "healthy":
                overall_status = "degraded"
    except Exception as e:
        checks["openai"] = {"status": "degraded", "error": str(e)}
        if overall_status == "healthy":
            overall_status = "degraded"

    # Webhook check
    try:
        webhook_sender = WebhookSender()
        if (
            webhook_sender.platform_webhook_url
            and webhook_sender.platform_webhook_url
            != "http://localhost:9000/webhook/response"
        ):
            checks["webhook"] = {"status": "healthy", "configured": True}
        else:
            checks["webhook"] = {"status": "degraded", "configured": False}
            if overall_status == "healthy":
                overall_status = "degraded"
    except Exception as e:
        checks["webhook"] = {"status": "degraded", "error": str(e)}
        if overall_status == "healthy":
            overall_status = "degraded"

    return {
        "status": overall_status,
        "checks": checks,
        "app_name": get_settings().app_name,
        "version": get_settings().app_version,
    }

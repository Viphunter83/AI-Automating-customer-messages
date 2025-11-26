from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.config import get_settings
from app.database import engine

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
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
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


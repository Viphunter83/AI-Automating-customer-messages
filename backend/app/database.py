from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from app.config import get_settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()

# Lazy initialization of engine
_engine: Optional[AsyncEngine] = None
_async_session_maker: Optional[sessionmaker] = None

def get_engine() -> AsyncEngine:
    """Get or create database engine"""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            future=True,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=40,
        )
    return _engine

def get_async_session_maker() -> sessionmaker:
    """Get or create session maker"""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_maker

# Dependency for FastAPI
async def get_session() -> AsyncSession:
    async with get_async_session_maker()() as session:
        yield session

async def init_db():
    """Initialize database tables"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

async def close_db():
    """Close database connections"""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
    logger.info("Database connections closed")


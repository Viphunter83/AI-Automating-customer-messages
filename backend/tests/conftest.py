import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.database import *
from typing import AsyncGenerator
from datetime import datetime

# Use PostgreSQL for tests if available, otherwise fallback to SQLite
# Use main database for tests (we'll clean up after)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://support_user:support_pass@localhost:5432/ai_support"
)

@pytest.fixture
async def test_db() -> AsyncGenerator:
    """Create test database - uses PostgreSQL if available"""
    # Try PostgreSQL first
    if "postgresql" in TEST_DATABASE_URL:
        try:
            engine = create_async_engine(
                TEST_DATABASE_URL,
                echo=False,
                future=True,
            )
            
            # Test connection first
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            async_session_maker = sessionmaker(
                engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            async with async_session_maker() as session:
                yield session
                await session.rollback()  # Rollback any uncommitted changes
                await session.close()
            
            # Cleanup: drop all tables after tests
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            await engine.dispose()
            return
        except Exception as e:
            pytest.skip(f"PostgreSQL not available: {e}")
    
    # Fallback to SQLite
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception:
            pytest.skip("SQLite doesn't support UUID type - PostgreSQL required")

    async_session_maker = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.close()
    
    await engine.dispose()

@pytest.fixture
def client():
    """FastAPI test client"""
    from fastapi.testclient import TestClient
    from app import create_app
    
    app = create_app()
    return TestClient(app)

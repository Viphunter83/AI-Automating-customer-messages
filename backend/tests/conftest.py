import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.database import *
from typing import AsyncGenerator

@pytest.fixture
async def test_db() -> AsyncGenerator:
    """Create test database"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
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


import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.database import ResponseTemplate, ScenarioType
from app.services.response_manager import ResponseManager
import uuid

@pytest.mark.asyncio
async def test_initialize_default_templates(test_db):
    """Test initialization of default templates"""
    # test_db fixture is automatically unwrapped by pytest-asyncio
    # It yields the session directly, so use it as-is
    session = test_db
    manager = ResponseManager(session)
    await manager.initialize_default_templates()
    
    # Check that templates were created
    from sqlalchemy import select
    result = await session.execute(select(ResponseTemplate))
    templates = result.scalars().all()
    
    assert len(templates) >= 3  # GREETING, REFERRAL, TECH_SUPPORT_BASIC
    assert any(t.scenario_name == ScenarioType.GREETING for t in templates)

@pytest.mark.asyncio
async def test_get_response_template(test_db):
    """Test getting a response template"""
    # test_db fixture is automatically unwrapped by pytest-asyncio
    # It yields the session directly, so use it as-is
    session = test_db
    manager = ResponseManager(session)
    await manager.initialize_default_templates()
    
    template = await manager.get_response_template("GREETING")
    
    assert template is not None
    assert template.scenario_name == ScenarioType.GREETING
    assert "Здравствуйте" in template.template_text

@pytest.mark.asyncio
async def test_personalize_response(test_db):
    """Test response personalization"""
    # test_db fixture is automatically unwrapped by pytest-asyncio
    # It yields the session directly, so use it as-is
    session = test_db
    manager = ResponseManager(session)
    
    template = "Привет {name}! Ваша ссылка: {link}"
    params = {"name": "John", "link": "https://example.com"}
    
    result = await manager.personalize_response(template, params)
    
    assert result == "Привет John! Ваша ссылка: https://example.com"

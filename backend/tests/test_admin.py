import pytest
from httpx import AsyncClient
from app import create_app
from app.models.database import ResponseTemplate, ScenarioType

@pytest.fixture
def app():
    return create_app()

@pytest.mark.asyncio
async def test_list_templates(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/admin/templates")
        assert response.status_code in [200, 404]  # 404 if no templates yet
        data = response.json()
        assert isinstance(data, list) or "detail" in data

@pytest.mark.asyncio
async def test_get_template(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/admin/templates/GREETING")
        assert response.status_code in [200, 404]  # 404 if template doesn't exist

@pytest.mark.asyncio
async def test_get_feedback_summary(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/admin/feedback/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_feedback" in data
        assert "accuracy_rate" in data

@pytest.mark.asyncio
async def test_get_stats_classifications(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/admin/stats/classifications")
        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data

@pytest.mark.asyncio
async def test_get_stats_messages(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/admin/stats/messages")
        assert response.status_code == 200
        data = response.json()
        assert "total_messages" in data
        assert "unique_clients" in data

@pytest.mark.asyncio
async def test_list_keywords(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/admin/keywords")
        assert response.status_code == 200
        data = response.json()
        assert "keywords" in data

@pytest.mark.asyncio
async def test_get_misclassified(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/admin/feedback/misclassified")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "count" in data











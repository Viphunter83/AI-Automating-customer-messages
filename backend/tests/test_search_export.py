import pytest
from httpx import AsyncClient
from app import create_app

@pytest.fixture
def app():
    return create_app()

@pytest.mark.asyncio
async def test_search_messages(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/search/messages?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "messages" in data

@pytest.mark.asyncio
async def test_search_dialogs(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/search/dialogs")
        assert response.status_code == 200
        data = response.json()
        assert "dialogs" in data
        assert "count" in data

@pytest.mark.asyncio
async def test_autocomplete_clients(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/search/clients/autocomplete?prefix=client")
        assert response.status_code == 200
        data = response.json()
        assert "clients" in data

@pytest.mark.asyncio
async def test_export_report(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/search/export/report?hours=24")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "classifications" in data
        assert "feedback" in data
        assert "period" in data

@pytest.mark.asyncio
async def test_export_dialog_json(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Use a test client ID
        response = await client.get("/api/search/export/dialog/client_001.json")
        assert response.status_code == 200
        data = response.json()
        assert "client_id" in data
        assert "messages" in data


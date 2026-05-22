import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from src.main import app
from src.interfaces.http import routes
from src.domain.entities.analysis import Analysis, AnalysisStatus


# Override DB and publisher dependencies so tests run without real infra
async def _mock_session():
    yield AsyncMock()


async def _mock_publisher():
    return AsyncMock()


app.dependency_overrides[routes.get_db_session] = _mock_session
app.dependency_overrides[routes.get_publisher] = _mock_publisher


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_analysis_rejects_invalid_mime():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/analyses",
            files={"file": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")},
        )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_create_analysis_rejects_empty_file():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/analyses",
            files={"file": ("empty.png", b"", "image/png")},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_status_rejects_invalid_status():
    analysis_id = str(uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            f"/analyses/{analysis_id}/status",
            json={"status": "INVALID_STATUS"},
        )
    assert response.status_code == 400

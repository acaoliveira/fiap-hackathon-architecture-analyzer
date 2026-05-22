import pytest
from httpx import AsyncClient, ASGITransport, Response
from unittest.mock import AsyncMock, patch

from src.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_analysis_proxies_to_upload_service():
    mock_response = Response(202, json={"analysis_id": "abc-123", "status": "RECEIVED"})
    with patch("src.main.http_client") as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/analyses",
                files={"file": ("diagram.png", b"fake-image-data", "image/png")},
            )
    assert response.status_code == 202
    assert response.json()["analysis_id"] == "abc-123"


@pytest.mark.asyncio
async def test_get_analysis_status_proxies_to_upload_service():
    analysis_id = "abc-123"
    mock_response = Response(200, json={"analysis_id": analysis_id, "status": "PROCESSING"})
    with patch("src.main.http_client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_response)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/analyses/{analysis_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "PROCESSING"


@pytest.mark.asyncio
async def test_get_report_proxies_to_report_service():
    analysis_id = "abc-123"
    mock_response = Response(200, json={"analysis_id": analysis_id, "summary": "Test"})
    with patch("src.main.http_client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_response)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/analyses/{analysis_id}/report")
    assert response.status_code == 200

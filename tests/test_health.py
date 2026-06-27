import pytest


@pytest.mark.asyncio
async def test_liveness(client):
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "alive"
    assert "request_id" in body["meta"]
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_readiness_without_database(client):
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SERVICE_UNAVAILABLE"

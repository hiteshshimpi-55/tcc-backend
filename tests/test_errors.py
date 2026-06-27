import pytest


@pytest.mark.asyncio
async def test_validation_error_envelope(client):
    response = await client.post("/api/v1/agents/invoke", json={"thread_id": "t1"})
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"]
    assert "request_id" in body["meta"]
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_not_found_envelope(client):
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NOT_FOUND"

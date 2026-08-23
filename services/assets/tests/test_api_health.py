async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

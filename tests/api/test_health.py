from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "commerce-os-api",
        "version": "0.1.0",
    }
    assert response.headers["x-request-id"]

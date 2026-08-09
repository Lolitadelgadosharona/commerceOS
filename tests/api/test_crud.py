from fastapi.testclient import TestClient


def test_minimum_crud_foundation(client: TestClient) -> None:
    organization_response = client.post(
        "/api/v1/organizations", json={"name": "Example Commerce", "slug": "example-commerce"}
    )
    assert organization_response.status_code == 201
    organization_id = organization_response.json()["id"]

    project_response = client.post(
        "/api/v1/projects",
        json={
            "organization_id": organization_id,
            "name": "Foundation",
            "slug": "foundation",
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    customer_response = client.post(
        "/api/v1/customers",
        json={"organization_id": organization_id, "display_name": "Test Buyer"},
    )
    assert customer_response.status_code == 201
    customer_id = customer_response.json()["id"]

    venture_response = client.post(
        "/api/v1/venture-opportunities",
        json={
            "organization_id": organization_id,
            "project_id": project_id,
            "name": "Category opportunity",
        },
    )
    assert venture_response.status_code == 201

    sale_response = client.post(
        "/api/v1/sales-opportunities",
        json={
            "organization_id": organization_id,
            "project_id": project_id,
            "customer_id": customer_id,
            "name": "Wholesale deal",
        },
    )
    assert sale_response.status_code == 201

    listed = client.get("/api/v1/sales-opportunities")
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "Wholesale deal"

    updated = client.patch(
        f"/api/v1/sales-opportunities/{sale_response.json()['id']}",
        json={"stage": "qualified"},
    )
    assert updated.status_code == 200
    assert updated.json()["stage"] == "qualified"


def test_consistent_not_found_error(client: TestClient) -> None:
    response = client.get("/api/v1/customers/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["request_id"]


def test_consistent_validation_error(client: TestClient) -> None:
    response = client.post("/api/v1/organizations", json={"name": "Invalid", "slug": "Not Valid"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["details"][0]["field"] == "body.slug"

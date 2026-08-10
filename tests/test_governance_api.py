from fastapi.testclient import TestClient


def test_governance_api_exposes_users_roles_permissions_and_audit(client: TestClient) -> None:
    organization = client.post(
        "/api/v1/organizations", json={"name": "Governance API", "slug": "governance-api"}
    ).json()
    user_response = client.post(
        "/api/v1/users",
        json={
            "organization_id": organization["id"],
            "email": "owner@example.com",
            "display_name": "Owner",
            "password": "correct horse battery staple",
        },
    )
    assert user_response.status_code == 201
    user = user_response.json()
    assert "password" not in user
    headers = {"X-Actor-ID": user["id"]}
    role_response = client.post(
        "/api/v1/roles",
        headers=headers,
        json={"organization_id": organization["id"], "name": "owner"},
    )
    assert role_response.status_code == 201
    permission_response = client.post(
        "/api/v1/permissions",
        json={
            "key": "approval.decide",
            "resource": "approval",
            "action": "decide",
            "is_human_approval_permission": True,
        },
    )
    assert permission_response.status_code == 201
    assert (
        client.post(
            f"/api/v1/roles/{role_response.json()['id']}/permissions",
            headers=headers,
            json={"permission_id": permission_response.json()["id"]},
        ).status_code
        == 204
    )
    logs = client.get("/api/v1/audit-logs", params={"organization_id": organization["id"]})
    assert logs.status_code == 200
    assert {entry["action"] for entry in logs.json()} >= {
        "user.created",
        "role.created",
        "role.permission_granted",
    }

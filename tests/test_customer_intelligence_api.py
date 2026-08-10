from fastapi.testclient import TestClient


def test_customer_intelligence_api_flow(client: TestClient) -> None:
    organization = client.post(
        "/api/v1/organizations", json={"name": "Insight API", "slug": "insight-api"}
    ).json()
    customer = client.post(
        "/api/v1/customers",
        json={"organization_id": organization["id"], "display_name": "Customer"},
    ).json()
    source_response = client.post(
        "/api/v1/signal-sources",
        json={
            "organization_id": organization["id"],
            "source_type": "support",
            "name": "Support inbox",
        },
    )
    assert source_response.status_code == 201
    source = source_response.json()
    signal_response = client.post(
        "/api/v1/customer-signals",
        json={
            "organization_id": organization["id"],
            "signal_source_id": source["id"],
            "source_type": "support",
            "source_reference": "ticket-123",
            "customer_id": customer["id"],
            "signal_type": "quality_concern",
            "content_reference": "object://support/ticket-123",
            "sentiment": "negative",
            "severity": "high",
            "confidence": 0.92,
        },
    )
    assert signal_response.status_code == 201
    signal = signal_response.json()
    cluster_response = client.post(
        "/api/v1/customer-clusters",
        json={
            "organization_id": organization["id"],
            "name": "Quality concerns",
            "description": "Explicit test grouping",
            "signal_ids": [signal["id"]],
            "trend_direction": "stable",
        },
    )
    assert cluster_response.status_code == 201
    cluster = cluster_response.json()
    insight_response = client.post(
        "/api/v1/customer-insights",
        json={
            "organization_id": organization["id"],
            "cluster_id": cluster["id"],
            "signal_ids": [signal["id"]],
            "title": "Review product quality evidence",
            "summary": "One selected support record contains a quality concern.",
            "impact_level": "high",
            "recommended_action": "Ask Build to inspect the referenced evidence.",
        },
    )
    assert insight_response.status_code == 201
    insight = insight_response.json()
    assert insight["evidence_count"] == 1
    assert (
        client.get(
            "/api/v1/customer-signals", params={"organization_id": organization["id"]}
        ).json()[0]["id"]
        == signal["id"]
    )
    assert (
        client.get(
            "/api/v1/customer-clusters", params={"organization_id": organization["id"]}
        ).json()[0]["id"]
        == cluster["id"]
    )
    assert (
        client.patch(
            f"/api/v1/customer-insights/{insight['id']}", json={"status": "validated"}
        ).json()["status"]
        == "validated"
    )

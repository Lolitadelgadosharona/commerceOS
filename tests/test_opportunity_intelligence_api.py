from fastapi.testclient import TestClient


def test_opportunity_intelligence_api_flow(client: TestClient) -> None:
    organization = client.post(
        "/api/v1/organizations", json={"name": "Opportunity API", "slug": "opportunity-api"}
    ).json()
    opportunity_response = client.post(
        "/api/v1/opportunities",
        json={
            "organization_id": organization["id"],
            "title": "Pet memorial emotional products",
            "description": "Observed demand for remembrance products.",
            "category": "Pet memorial",
            "market": "Pet owners",
            "geography": "United States",
            "trigger_type": "customer_pain",
            "timing_window": "Evergreen",
            "confidence_score": 0.75,
        },
    )
    assert opportunity_response.status_code == 201
    opportunity = opportunity_response.json()
    evidence = client.post(
        "/api/v1/opportunity-evidence",
        json={
            "organization_id": organization["id"],
            "opportunity_id": opportunity["id"],
            "source_type": "market_report",
            "source_reference": "report:pet-memorial-2026",
            "evidence_summary": "Manually supplied market-report evidence.",
            "confidence_score": 0.7,
        },
    )
    assert evidence.status_code == 201
    candidate = client.post(
        "/api/v1/product-candidates",
        json={
            "organization_id": organization["id"],
            "opportunity_id": opportunity["id"],
            "product_name": "Personalized memorial frame",
            "category": "Memorial gifts",
            "customer_need": "A respectful tangible remembrance.",
            "estimated_margin": 0.45,
            "risk_level": "medium",
        },
    )
    assert candidate.status_code == 201
    score = client.post(
        "/api/v1/opportunity-scores",
        json={
            "organization_id": organization["id"],
            "opportunity_id": opportunity["id"],
            "demand_score": 80,
            "pain_score": 90,
            "trend_score": 60,
            "margin_score": 70,
            "competition_score": 50,
            "ip_risk_score": 20,
            "dispute_risk_score": 10,
        },
    )
    assert score.status_code == 200
    assert score.json()["overall_score"] == 74.25
    risk = client.post(
        "/api/v1/opportunity-risks",
        json={
            "organization_id": organization["id"],
            "opportunity_id": opportunity["id"],
            "risk_type": "brand",
            "severity": "medium",
            "description": "Tone must remain respectful.",
        },
    )
    assert risk.status_code == 201
    for endpoint in (
        "opportunities",
        "opportunity-evidence",
        "product-candidates",
        "opportunity-scores",
        "opportunity-risks",
    ):
        response = client.get(f"/api/v1/{endpoint}", params={"organization_id": organization["id"]})
        assert response.status_code == 200
        assert len(response.json()) == 1

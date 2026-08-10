from fastapi.testclient import TestClient


def test_product_intelligence_api_flow(client: TestClient) -> None:
    organization = client.post(
        "/api/v1/organizations", json={"name": "Product API", "slug": "product-api"}
    ).json()
    opportunity = client.post(
        "/api/v1/opportunities",
        json={
            "organization_id": organization["id"],
            "title": "Cooling demand",
            "description": "Heat-driven demand",
            "category": "Cooling",
            "market": "Consumers",
            "geography": "Europe",
            "trigger_type": "weather_event",
            "timing_window": "Summer",
            "status": "qualified",
            "confidence_score": 0.8,
        },
    ).json()
    client.post(
        "/api/v1/opportunity-scores",
        json={
            "organization_id": organization["id"],
            "opportunity_id": opportunity["id"],
            "demand_score": 80,
            "pain_score": 80,
            "trend_score": 80,
            "margin_score": 80,
            "competition_score": 50,
            "ip_risk_score": 20,
            "dispute_risk_score": 20,
        },
    )
    response = client.post(
        "/api/v1/product-hypotheses",
        json={
            "organization_id": organization["id"],
            "opportunity_id": opportunity["id"],
            "name": "Portable cooler",
            "description": "A product hypothesis",
            "customer_problem": "Excess heat",
            "solution_description": "Portable cooling",
            "target_customer": "Urban renters",
            "target_market": "Europe",
            "status": "evaluating",
            "confidence_score": 0.8,
        },
    )
    assert response.status_code == 201
    product = response.json()
    economics = client.post(
        "/api/v1/product-economics",
        json={
            "organization_id": organization["id"],
            "product_id": product["id"],
            "selling_price": "100.00",
            "estimated_product_cost": "30.00",
            "estimated_shipping_cost": "10.00",
            "payment_cost": "3.00",
            "estimated_marketing_cost": "20.00",
            "currency": "usd",
        },
    )
    assert economics.status_code == 200
    assert economics.json()["contribution_margin"] == "37.00"
    supplier = client.post(
        "/api/v1/supplier-candidates",
        json={
            "organization_id": organization["id"],
            "product_id": product["id"],
            "source_type": "manual",
            "supplier_reference": "supplier:sample",
            "estimated_cost": "30.00",
            "minimum_order_quantity": 10,
            "lead_time": "21 days",
            "quality_notes": "Unverified sample",
            "risk_level": "medium",
        },
    )
    assert supplier.status_code == 201
    risk = client.post(
        "/api/v1/product-risks",
        json={
            "organization_id": organization["id"],
            "product_id": product["id"],
            "risk_type": "quality",
            "severity": "high",
            "description": "Sample inspection required",
        },
    )
    assert risk.status_code == 201
    score = client.post(
        "/api/v1/product-investment-scores",
        json={
            "organization_id": organization["id"],
            "product_id": product["id"],
            "competition_score": 40,
        },
    )
    assert score.status_code == 200
    assert 0 <= score.json()["overall_score"] <= 100
    for endpoint in (
        "product-hypotheses",
        "product-economics",
        "supplier-candidates",
        "product-risks",
        "product-investment-scores",
    ):
        result = client.get(f"/api/v1/{endpoint}", params={"organization_id": organization["id"]})
        assert result.status_code == 200
        assert len(result.json()) == 1

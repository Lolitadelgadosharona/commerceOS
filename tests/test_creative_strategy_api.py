from commerce_os.build.models import Product
from commerce_os.governance.models import Organization
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_creative_strategy_api_flow(client: TestClient, db_session: Session) -> None:
    organization = Organization(name="Creative API", slug="creative-api")
    db_session.add(organization)
    db_session.flush()
    brand = Brand(
        organization_id=organization.id, name="Creative API Brand", slug="creative-api-brand"
    )
    db_session.add(brand)
    db_session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Care Kit",
        description="Product",
        category="Care",
        status="approved",
    )
    db_session.add(product)
    db_session.commit()
    base = {"organization_id": str(organization.id)}
    strategy = client.post(
        "/api/v1/creative-strategies",
        json=base
        | {
            "product_id": str(product.id),
            "target_audience": "Care-focused households",
            "marketing_objective": "Increase trust",
            "core_message": "Verified reusable care",
            "emotional_angle": "Confidence",
            "creative_direction": "Evidence-led storytelling",
        },
    )
    assert strategy.status_code == 201
    strategy_id = strategy.json()["id"]
    assert (
        client.patch(
            f"/api/v1/creative-strategies/{strategy_id}", params=base, json={"status": "approved"}
        ).status_code
        == 200
    )
    hypothesis = client.post(
        "/api/v1/creative-hypotheses",
        json=base
        | {
            "strategy_id": strategy_id,
            "hypothesis": "Comparison reduces hesitation",
            "expected_behavior": "More informed engagement",
            "success_metric": "qualified_engagement",
            "confidence_score": 0.75,
        },
    )
    assert hypothesis.status_code == 201
    assert (
        client.post(
            "/api/v1/creative-briefs",
            json=base
            | {
                "strategy_id": strategy_id,
                "platform": "instagram",
                "audience": "Care-focused households",
                "hook": "See verified reuse",
                "story_structure": "Problem, proof, solution",
                "proof_points": "Product Truth facts",
                "cta": "Learn more",
                "content_format": "carousel",
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/creative-channel-fits",
            json=base
            | {
                "product_id": str(product.id),
                "channel": "instagram",
                "suitability_score": 85,
                "reason": "Visual education fit",
            },
        ).status_code
        == 201
    )
    experiment = client.post(
        "/api/v1/creative-experiments",
        json=base
        | {
            "hypothesis_id": hypothesis.json()["id"],
            "variant_name": "Comparison A",
            "test_objective": "Measure hesitation",
            "metric": "qualified_engagement",
        },
    )
    assert experiment.status_code == 201
    assert (
        client.patch(
            f"/api/v1/creative-experiments/{experiment.json()['id']}",
            params=base,
            json={"status": "running"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/creative-experiments/{experiment.json()['id']}",
            params=base,
            json={"status": "completed", "result": "Observed result"},
        ).status_code
        == 200
    )
    for endpoint in (
        "creative-strategies",
        "creative-hypotheses",
        "creative-briefs",
        "creative-channel-fits",
        "creative-experiments",
    ):
        response = client.get(f"/api/v1/{endpoint}", params=base)
        assert response.status_code == 200 and len(response.json()) == 1

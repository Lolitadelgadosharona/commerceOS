import pytest
from commerce_os.build.models import Product
from commerce_os.decision.channel_models import ChannelStrategyStatus
from commerce_os.decision.channel_schemas import (
    CandidateCreate,
    PathCreate,
    ScoreCreate,
    StepCreate,
    StrategyCreate,
)
from commerce_os.decision.channel_services import (
    ChannelStrategyService,
    ConversionPathService,
)
from commerce_os.decision.errors import DecisionStateError
from commerce_os.governance.models import Organization
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def foundation(db_session: Session, slug: str = "channel") -> tuple[Organization, Product]:
    organization = Organization(name="Channel Test", slug=slug)
    db_session.add(organization)
    db_session.flush()
    brand = Brand(organization_id=organization.id, name="Channel Brand", slug=f"{slug}-brand")
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
    return organization, product


def test_deterministic_scoring_preserves_missing_evidence(db_session: Session) -> None:
    org, product = foundation(db_session)
    service = ChannelStrategyService(db_session)
    strategy = service.create(
        StrategyCreate(
            organization_id=org.id,
            product_id=product.id,
            market="care",
            geography="US",
            audience="Care-focused households",
            business_model="b2c",
            objective="Qualified purchases",
        )
    )
    candidate = service.create_candidate(
        CandidateCreate(
            organization_id=org.id,
            strategy_id=strategy.id,
            channel="instagram",
            distribution_mode="organic",
            suitability_score=80,
            confidence_score=0.7,
            recommendation="recommended",
            reason="Strong visual fit",
        )
    )
    score = service.score(
        ScoreCreate(
            organization_id=org.id,
            candidate_id=candidate.id,
            target_customer_fit=80,
            content_cost=20,
        )
    )
    assert score.overall_score == 80
    assert score.evidence_coverage == pytest.approx(2 / 11, abs=0.0001)
    assert score.historical_performance_confidence is None
    with pytest.raises(DecisionStateError):
        service.score(ScoreCreate(organization_id=org.id, candidate_id=candidate.id))


@pytest.mark.parametrize(
    ("business_model", "steps"),
    [
        (
            "b2c",
            [
                ("content", "growth"),
                ("product_page", "growth"),
                ("checkout", "operations"),
                ("order", "operations"),
            ],
        ),
        (
            "b2b",
            [
                ("community_interaction", "growth"),
                ("lead_form", "operations"),
                ("qualification", "operations"),
                ("quote", "operations"),
                ("order", "operations"),
            ],
        ),
    ],
)
def test_b2c_and_b2b_conversion_path_validation(
    db_session: Session, business_model: str, steps: list[tuple[str, str]]
) -> None:
    org, product = foundation(db_session, f"channel-{business_model}")
    strategy = ChannelStrategyService(db_session).create(
        StrategyCreate(
            organization_id=org.id,
            product_id=product.id,
            market="care",
            geography="US",
            audience="Buyers",
            business_model=business_model,
            objective="Conversion",
        )
    )
    paths = ConversionPathService(db_session)
    path = paths.create(PathCreate(organization_id=org.id, strategy_id=strategy.id, name="Primary"))
    for sequence, (step_type, owner) in enumerate(steps, 1):
        paths.add_step(
            StepCreate(
                organization_id=org.id,
                path_id=path.id,
                sequence=sequence,
                step_type=step_type,
                responsible_domain=owner,
                human_required=step_type == "quote",
            )
        )
    assert paths.validate(path).status == "validated"


def test_api_exclusion_reddit_separation_and_lifecycle(
    client: TestClient, db_session: Session
) -> None:
    org, product = foundation(db_session, "channel-api")
    base = {"organization_id": str(org.id)}
    response = client.post(
        "/api/v1/channel-strategies",
        json=base
        | {
            "product_id": str(product.id),
            "market": "care",
            "geography": "US",
            "audience": "Households",
            "business_model": "b2c",
            "objective": "Purchases",
        },
    )
    assert response.status_code == 201
    strategy_id = response.json()["id"]
    excluded = client.post(
        "/api/v1/channel-candidates",
        json=base
        | {
            "strategy_id": strategy_id,
            "channel": "reddit",
            "distribution_mode": "community",
            "suitability_score": 25,
            "confidence_score": 0.6,
            "recommendation": "excluded",
            "exclusion_reason": "Intelligence evidence does not imply acquisition fit",
        },
    )
    assert excluded.status_code == 201
    score = client.post(
        "/api/v1/channel-opportunity-scores",
        json=base | {"candidate_id": excluded.json()["id"], "product_fit": 50},
    )
    assert score.status_code == 201 and score.json()["evidence_coverage"] < 0.1
    assert (
        client.patch(
            f"/api/v1/channel-strategies/{strategy_id}",
            params=base,
            json={"status": "recommended"},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/channel-strategies/{strategy_id}",
            params=base,
            json={"status": "approved"},
        ).json()["status"]
        == ChannelStrategyStatus.APPROVED
    )
    assert client.get("/api/v1/channel-candidates", params=base).status_code == 200

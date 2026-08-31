from datetime import UTC, datetime

from commerce_os.governance.models import Organization
from commerce_os.intelligence.market_models import (
    MarketDataSource,
    MarketSignal,
    MarketSignalCluster,
    MarketSignalClusterMembership,
    MarketSignalOpportunityLink,
)
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def seed(session: Session, slug: str) -> tuple[Organization, MarketOpportunity]:
    organization = Organization(name=slug.title(), slug=slug)
    session.add(organization)
    session.flush()
    opportunity = MarketOpportunity(
        organization_id=organization.id,
        title="Cooling demand",
        description="Observed demand supported by market evidence.",
        category="home",
        market="consumer",
        geography="US",
        trigger_type="trend_shift",
        timing_window="90 days",
        status="evaluating",
        confidence_score=0.72,
    )
    session.add(opportunity)
    session.commit()
    return organization, opportunity


def test_signal_projection_cluster_membership_and_cross_tenant_isolation(
    client: TestClient, db_session: Session
) -> None:
    owner, opportunity = seed(db_session, "provenance-owner")
    other, _ = seed(db_session, "provenance-other")
    source = MarketDataSource(
        organization_id=owner.id,
        name="Manual source",
        platform="manual",
        source_type="research",
        access_method="manual",
        reliability_score=0.8,
        status="active",
    )
    db_session.add(source)
    db_session.flush()
    signal = MarketSignal(
        organization_id=owner.id,
        source_id=source.id,
        region="US",
        category="home",
        signal_type="demand",
        title="Cooling searches rising",
        description="A normalized observation.",
        trend_direction="rising",
        confidence_score=0.75,
        observed_at=datetime(2026, 8, 31, tzinfo=UTC),
        status="validated",
    )
    cluster = MarketSignalCluster(
        organization_id=owner.id,
        name="Cooling",
        category="home",
        confidence=0.7,
        impact_score=65,
    )
    db_session.add_all([signal, cluster])
    db_session.flush()
    db_session.add_all(
        [
            MarketSignalOpportunityLink(
                organization_id=owner.id,
                signal_id=signal.id,
                opportunity_id=opportunity.id,
            ),
            MarketSignalClusterMembership(
                organization_id=owner.id,
                cluster_id=cluster.id,
                signal_id=signal.id,
            ),
        ]
    )
    db_session.commit()

    links = client.get(
        f"/api/v1/market-signals/{signal.id}/opportunities",
        params={"organization_id": str(owner.id)},
    )
    assert links.status_code == 200
    assert links.json()[0]["opportunity"]["id"] == str(opportunity.id)
    assert (
        client.get(
            f"/api/v1/market-signals/{signal.id}/opportunities",
            params={"organization_id": str(other.id)},
        ).status_code
        == 403
    )
    members = client.get(
        f"/api/v1/market-clusters/{cluster.id}/signals",
        params={"organization_id": str(owner.id)},
    )
    assert members.status_code == 200
    assert members.json()[0]["signal"]["id"] == str(signal.id)


def test_hypothesis_detail_provenance_unknown_zero_and_committee_packet(
    client: TestClient, db_session: Session
) -> None:
    owner, opportunity = seed(db_session, "packet-owner")
    other, _ = seed(db_session, "packet-other")
    base = {"organization_id": str(owner.id)}
    hypothesis = client.post(
        "/api/v1/product-hypotheses",
        json=base
        | {
            "opportunity_id": str(opportunity.id),
            "name": "Cooling mat",
            "description": "A product thesis.",
            "customer_problem": "Heat discomfort.",
            "solution_description": "Passive cooling surface.",
            "target_customer": "Pet owners",
            "target_market": "US",
            "confidence_score": 0.7,
        },
    )
    assert hypothesis.status_code == 201
    hypothesis_id = hypothesis.json()["id"]
    detail = client.get(f"/api/v1/product-hypotheses/{hypothesis_id}", params=base)
    assert detail.status_code == 200
    assert (
        client.get(
            f"/api/v1/product-hypotheses/{hypothesis_id}",
            params={"organization_id": str(other.id)},
        ).status_code
        == 404
    )
    economics = client.post(
        "/api/v1/product-economics",
        json=base
        | {
            "product_id": hypothesis_id,
            "selling_price": "50.00",
            "estimated_product_cost": "15.00",
            "estimated_shipping_cost": "0.00",
            "payment_cost": "2.00",
            "estimated_marketing_cost": "10.00",
            "currency": "USD",
        },
    )
    assert economics.status_code == 200
    economics_id = economics.json()["id"]
    known_zero = client.post(
        "/api/v1/product-economic-inputs",
        json=base
        | {
            "product_economics_id": economics_id,
            "metric": "estimated_shipping_cost",
            "value": "0",
            "classification": "quoted",
            "source": "supplier quote",
            "confidence": 0.9,
        },
    )
    unknown = client.post(
        "/api/v1/product-economic-inputs",
        json=base
        | {
            "product_economics_id": economics_id,
            "metric": "customer_acquisition_cost",
            "value": None,
            "classification": "unknown",
            "source": "not researched",
        },
    )
    assert known_zero.status_code == unknown.status_code == 201
    assert known_zero.json()["value"] == "0.0000"
    assert unknown.json()["value"] is None
    invalid = client.post(
        "/api/v1/product-economic-inputs",
        json=base
        | {
            "product_economics_id": economics_id,
            "metric": "payment_cost",
            "value": "0",
            "classification": "unknown",
            "source": "invalid",
        },
    )
    assert invalid.status_code == 422

    packet = client.get(f"/api/v1/opportunities/{opportunity.id}/committee-packet", params=base)
    assert packet.status_code == 200
    body = packet.json()
    assert body["product_theses"][0]["hypothesis"]["id"] == hypothesis_id
    assert body["product_theses"][0]["product_truth_relationship_status"] == (
        "no_canonical_relationship"
    )
    assert body["approval"] is None
    assert body["decision_quality_warnings"]
    assert (
        client.get(
            f"/api/v1/opportunities/{opportunity.id}/committee-packet",
            params={"organization_id": str(other.id)},
        ).status_code
        == 404
    )

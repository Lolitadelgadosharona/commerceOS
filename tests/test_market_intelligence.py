from datetime import UTC, datetime

import pytest
from commerce_os.governance.models import Organization
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.market_models import MarketSignalOpportunityLink
from commerce_os.intelligence.market_schemas import (
    MarketEvidenceCreate,
    MarketSignalCreate,
    MarketSourceCreate,
)
from commerce_os.intelligence.market_services import MarketIntelligenceService
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def organization(session: Session, slug: str) -> Organization:
    entity = Organization(name=f"Market {slug}", slug=slug)
    session.add(entity)
    session.commit()
    return entity


def opportunity(session: Session, organization_id) -> MarketOpportunity:
    entity = MarketOpportunity(
        organization_id=organization_id,
        title="Observed demand shift",
        description="Existing opportunity created independently of market signals.",
        category="home",
        market="consumer",
        geography="US",
        trigger_type="trend_shift",
        timing_window="30 days",
        status="observed",
        confidence_score=0.6,
    )
    session.add(entity)
    session.commit()
    return entity


def test_signal_lifecycle_evidence_ownership_and_tenant_isolation(db_session: Session) -> None:
    owner = organization(db_session, "signals")
    other = organization(db_session, "signals-other")
    service = MarketIntelligenceService(db_session)
    source = service.create_source(
        MarketSourceCreate(
            organization_id=owner.id,
            name="Manual trend observations",
            platform="google_trends",
            source_type="trend",
            access_method="manual",
            reliability_score=0.8,
        )
    )
    with pytest.raises(IntelligenceValidationError):
        service.create_signal(
            MarketSignalCreate(
                organization_id=owner.id,
                source_id=source.id,
                region="US",
                category="home",
                signal_type="demand",
                title="Demand increasing",
                description="Manual observation.",
                trend_direction="rising",
                confidence_score=0.7,
                observed_at=datetime.now(UTC),
            )
        )
    service.transition_source(source, "active")
    signal = service.create_signal(
        MarketSignalCreate(
            organization_id=owner.id,
            source_id=source.id,
            region="US",
            category="home",
            signal_type="demand",
            title="Demand increasing",
            description="Manual observation.",
            trend_direction="rising",
            confidence_score=0.7,
            observed_at=datetime.now(UTC),
        )
    )
    assert service.transition_signal(signal, "validated").status == "validated"
    evidence = service.add_evidence(
        MarketEvidenceCreate(
            organization_id=owner.id,
            signal_id=signal.id,
            evidence_type="reference",
            content_reference="internal://market-observation/1",
            strength_score=0.75,
            captured_at=datetime.now(UTC),
        )
    )
    assert evidence.organization_id == owner.id
    with pytest.raises(IntelligenceScopeError):
        service.add_evidence(
            MarketEvidenceCreate(
                organization_id=other.id,
                signal_id=signal.id,
                evidence_type="reference",
                content_reference="internal://cross-tenant",
                strength_score=0.5,
                captured_at=datetime.now(UTC),
            )
        )


def test_market_api_clustering_bounds_and_opportunity_separation(
    client: TestClient, db_session: Session
) -> None:
    owner = organization(db_session, "market-api")
    existing_opportunity = opportunity(db_session, owner.id)
    base = {"organization_id": str(owner.id)}
    source = client.post(
        "/api/v1/market-sources",
        json=base
        | {
            "name": "Manual Reddit observations",
            "platform": "reddit",
            "source_type": "community",
            "access_method": "manual",
            "reliability_score": 0.65,
        },
    )
    assert source.status_code == 201
    source_id = source.json()["id"]
    client.patch(f"/api/v1/market-sources/{source_id}", params=base, json={"status": "active"})
    signal_payload = base | {
        "source_id": source_id,
        "region": "US",
        "category": "pets",
        "signal_type": "customer_pain",
        "title": "Memorial demand discussion",
        "description": "Supplied normalized observation; no scraping.",
        "trend_direction": "rising",
        "confidence_score": 0.7,
        "observed_at": "2026-08-10T12:00:00Z",
    }
    signal = client.post("/api/v1/market-signals", json=signal_payload)
    assert signal.status_code == 201
    signal_id = signal.json()["id"]
    invalid = client.post(
        "/api/v1/market-signals", json=signal_payload | {"confidence_score": 1.01}
    )
    assert invalid.status_code == 422
    evidence = client.post(
        "/api/v1/market-evidence",
        json=base
        | {
            "signal_id": signal_id,
            "evidence_type": "observation",
            "content_reference": "internal://supplied/2",
            "strength_score": 0.8,
            "captured_at": "2026-08-10T12:01:00Z",
        },
    )
    assert evidence.status_code == 201
    cluster = client.post(
        "/api/v1/market-clusters",
        json=base
        | {
            "name": "Pet memorial interest",
            "category": "pets",
            "confidence": 0.7,
            "impact_score": 65,
        },
    )
    assert cluster.status_code == 201
    membership = client.post(
        f"/api/v1/market-clusters/{cluster.json()['id']}/signals",
        json=base | {"signal_id": signal_id},
    )
    assert membership.status_code == 201
    before = db_session.scalar(select(func.count()).select_from(MarketOpportunity))
    link = client.post(
        f"/api/v1/market-signals/{signal_id}/opportunities",
        json=base | {"opportunity_id": str(existing_opportunity.id)},
    )
    assert link.status_code == 201
    after = db_session.scalar(select(func.count()).select_from(MarketOpportunity))
    assert before == after == 1
    assert db_session.scalar(select(func.count()).select_from(MarketSignalOpportunityLink)) == 1
    assert client.post("/api/v1/market-research/execute", json={}).status_code == 404
    for endpoint in ("market-sources", "market-signals", "market-evidence", "market-clusters"):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200

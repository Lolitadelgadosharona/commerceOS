from datetime import UTC, datetime

import pytest
from commerce_os.governance.models import Organization
from commerce_os.intelligence.connector_models import (
    CustomerPainCandidate,
    MarketConnectorDefinition,
    MarketDataRecord,
)
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.intelligence.need_schemas import CustomerBackedAssessmentCreate
from commerce_os.intelligence.need_services import CustomerNeedService
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.intelligence.voice_models import CustomerPainCluster, PainClusterMembership
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):
    org = Organization(name=f"Need {slug}", slug=slug)
    session.add(org)
    session.flush()
    source = MarketConnectorDefinition(
        organization_id=org.id,
        name="source",
        platform="reddit",
        connector_type="reddit",
        status="active",
        configuration_schema={},
    )
    session.add(source)
    session.flush()
    record = MarketDataRecord(
        organization_id=org.id,
        source_id=source.id,
        external_reference="internal://need",
        content_type="post",
        raw_content="need",
        metadata_json={},
        captured_at=datetime.now(UTC),
    )
    session.add(record)
    session.flush()
    pain = CustomerPainCandidate(
        organization_id=org.id,
        source_record_id=record.id,
        pain_category="problem",
        customer_language="need quieter fan",
        confidence_score=0.8,
        status="detected",
    )
    session.add(pain)
    session.flush()
    cluster = CustomerPainCluster(
        organization_id=org.id,
        name="noise",
        category="quality",
        description="noise",
        severity_score=70,
        confidence_score=0.8,
        status="active",
        scoring_evidence={},
    )
    session.add(cluster)
    session.flush()
    session.add(
        PainClusterMembership(
            organization_id=org.id,
            cluster_id=cluster.id,
            pain_candidate_id=pain.id,
            relevance_score=0.9,
        )
    )
    opp = MarketOpportunity(
        organization_id=org.id,
        title="Quiet cooling",
        description="existing",
        category="home",
        market="consumer",
        geography="US",
        trigger_type="customer_need",
        timing_window="90 days",
        status="observed",
        confidence_score=0.7,
    )
    session.add(opp)
    session.commit()
    return org, cluster, opp


def test_customer_need_mapping_assessment_and_boundaries(
    client: TestClient, db_session: Session
) -> None:
    org, cluster, opp = foundation(db_session, "api")
    base = {"organization_id": str(org.id)}
    need = client.post(
        "/api/v1/customer-needs",
        json=base
        | {
            "name": "Quiet cooling",
            "description": "Lower noise",
            "category": "quality",
            "confidence_score": 0.8,
        },
    )
    assert need.status_code == 201
    need_id = need.json()["id"]
    mapping = client.post(
        "/api/v1/pain-need-mappings",
        json=base
        | {
            "pain_cluster_id": str(cluster.id),
            "need_id": need_id,
            "mapping_strength": 0.9,
            "evidence_count": 1,
        },
    )
    assert mapping.status_code == 201
    solution = client.post(
        "/api/v1/product-solution-hypotheses",
        json=base
        | {
            "need_id": need_id,
            "product_category": "fan",
            "solution_description": "Quiet fan hypothesis",
            "fit_score": 85,
            "confidence_score": 0.75,
        },
    )
    assert solution.status_code == 201
    payload = base | {
        "opportunity_id": str(opp.id),
        "need_id": need_id,
        "pain_strength": 80,
        "solution_fit": 85,
        "intent_score": 70,
        "competition_score": 60,
        "margin_score": 75,
        "risk_score": 20,
    }
    assessed = client.post("/api/v1/customer-backed-assessments", json=payload)
    assert assessed.status_code == 201
    assert assessed.json()["overall_score"] == 77.0
    assert (
        client.post(
            "/api/v1/customer-backed-assessments", json=payload | {"risk_score": 101}
        ).status_code
        == 422
    )
    for endpoint in (
        "customer-needs",
        "pain-need-mappings",
        "product-solution-hypotheses",
        "customer-backed-assessments",
    ):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200
    assert client.post("/api/v1/customer-backed-assessments/execute", json={}).status_code in {
        404,
        405,
        422,
    }


def test_tenant_isolation(db_session: Session) -> None:
    owner, _, opp = foundation(db_session, "owner")
    other, _, _ = foundation(db_session, "other")
    with pytest.raises(IntelligenceScopeError):
        CustomerNeedService(db_session).assess(
            CustomerBackedAssessmentCreate(
                organization_id=other.id,
                opportunity_id=opp.id,
                need_id=owner.id,
                pain_strength=50,
                solution_fit=50,
                intent_score=50,
                competition_score=50,
                margin_score=50,
                risk_score=50,
            )
        )

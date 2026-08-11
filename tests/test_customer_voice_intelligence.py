from datetime import UTC, datetime

import pytest
from commerce_os.governance.models import Organization
from commerce_os.intelligence.connector_models import (
    CustomerPainCandidate,
    MarketConnectorDefinition,
    MarketDataRecord,
)
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.intelligence.voice_models import PainClusterMembership, PurchaseIntentSignal
from commerce_os.intelligence.voice_schemas import (
    IntentScoreInputs,
    PainScoreInputs,
    PurchaseIntentCreate,
)
from commerce_os.intelligence.voice_services import CustomerVoiceService
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):
    organization = Organization(name=f"Voice {slug}", slug=slug)
    session.add(organization)
    session.flush()
    source = MarketConnectorDefinition(
        organization_id=organization.id,
        name="Supplied source",
        platform="reddit",
        connector_type="reddit",
        status="active",
        configuration_schema={},
    )
    session.add(source)
    session.flush()
    record = MarketDataRecord(
        organization_id=organization.id,
        source_id=source.id,
        external_reference="internal://voice/1",
        content_type="post",
        raw_content="Supplied source language",
        metadata_json={},
        captured_at=datetime.now(UTC),
        source_platform="reddit",
        external_id=f"record-{slug}",
        content="I need a quieter fan urgently",
    )
    session.add(record)
    session.flush()
    candidate = CustomerPainCandidate(
        organization_id=organization.id,
        source_record_id=record.id,
        pain_category="problem",
        customer_language="I need a quieter fan urgently",
        confidence_score=0.8,
        status="detected",
    )
    session.add(candidate)
    session.commit()
    return organization, record, candidate


def cluster_payload(organization_id: str) -> dict[str, object]:
    return {
        "organization_id": organization_id,
        "name": "Noisy cooling",
        "category": "quality",
        "description": "Customers report excessive fan noise.",
        "confidence_score": 0.8,
        "score_inputs": {"frequency": 80, "emotion": 60, "urgency": 70, "growth": 40},
    }


def test_deterministic_scores_and_boundaries() -> None:
    assert (
        CustomerVoiceService.pain_severity(
            PainScoreInputs(frequency=80, emotion=60, urgency=70, growth=40)
        )
        == 66.0
    )
    assert (
        CustomerVoiceService.intent_score(
            IntentScoreInputs(question_behavior=50, solution_seeking=80, purchase_language=90)
        )
        == 78.5
    )
    with pytest.raises(ValueError):
        PainScoreInputs(frequency=101, emotion=0, urgency=0, growth=0)


def test_cluster_membership_language_and_source_traceability(
    client: TestClient, db_session: Session
) -> None:
    organization, record, candidate = foundation(db_session, "api")
    base = {"organization_id": str(organization.id)}
    cluster = client.post("/api/v1/pain-clusters", json=cluster_payload(str(organization.id)))
    assert cluster.status_code == 201
    assert cluster.json()["severity_score"] == 66.0
    cluster_id = cluster.json()["id"]
    membership = client.post(
        f"/api/v1/pain-clusters/{cluster_id}/members",
        json=base | {"pain_candidate_id": str(candidate.id), "relevance_score": 0.9},
    )
    assert membership.status_code == 201
    language = client.post(
        "/api/v1/customer-language",
        json=base
        | {
            "cluster_id": cluster_id,
            "phrase": "I need a quieter fan",
            "context": "Urgent product-quality complaint",
            "usage_type": "product",
            "frequency": 12,
        },
    )
    assert language.status_code == 201
    intent = client.post(
        "/api/v1/purchase-intent-signals",
        json=base
        | {
            "source_record_id": str(record.id),
            "intent_type": "urgent_need",
            "confidence_score": 0.85,
            "evidence": {"phrase": "need urgently"},
            "score_inputs": {
                "question_behavior": 50,
                "solution_seeking": 80,
                "purchase_language": 90,
            },
        },
    )
    assert intent.status_code == 201
    assert intent.json()["intent_score"] == 78.5
    persisted = db_session.scalar(select(PurchaseIntentSignal))
    assert persisted is not None and persisted.source_record_id == record.id
    persisted_membership = db_session.scalar(select(PainClusterMembership))
    assert persisted_membership is not None
    assert persisted_membership.pain_candidate_id == candidate.id
    for endpoint in ("pain-clusters", "customer-language", "purchase-intent-signals"):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200


def test_tenant_isolation_and_evidence_linkage(db_session: Session) -> None:
    owner, record, _ = foundation(db_session, "owner")
    other, _, _ = foundation(db_session, "other")
    service = CustomerVoiceService(db_session)
    with pytest.raises(IntelligenceScopeError):
        service.create_intent(
            PurchaseIntentCreate(
                organization_id=other.id,
                source_record_id=record.id,
                intent_type="research",
                confidence_score=0.5,
                evidence={"source": "cross-tenant"},
                score_inputs=IntentScoreInputs(
                    question_behavior=50, solution_seeking=50, purchase_language=20
                ),
            )
        )
    assert owner.id != other.id

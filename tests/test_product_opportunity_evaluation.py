from uuid import uuid4

import pytest
from commerce_os.build.models import Product
from commerce_os.intelligence.discovery_models import OpportunityCandidateEvidence
from commerce_os.intelligence.discovery_services import OpportunityDiscoveryService
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.opportunity_models import ProductCandidateEvidence
from commerce_os.intelligence.opportunity_schemas import (
    ProductEvidenceInput,
    ProductOpportunityCandidateCreate,
    ValueRange,
)
from commerce_os.intelligence.opportunity_services import OpportunityService
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.test_opportunity_discovery_engine import candidate_payload, reviewed_signals


def foundation(session: Session):  # type: ignore[no-untyped-def]
    organization, user, signals = reviewed_signals(session)
    discovery = OpportunityDiscoveryService(session)
    opportunity = discovery.create_candidate(
        candidate_payload(organization.id, [signal.id for signal in signals[:3]]), user.id
    )
    opportunity.status = "accepted"
    session.commit()
    evidence = session.scalar(
        select(OpportunityCandidateEvidence).where(
            OpportunityCandidateEvidence.opportunity_candidate_id == opportunity.id
        )
    )
    assert evidence is not None
    return organization, user, opportunity, evidence


def payload(organization_id, opportunity_id, evidence_id):  # type: ignore[no-untyped-def]
    return ProductOpportunityCandidateCreate(
        organization_id=organization_id,
        opportunity_candidate_id=opportunity_id,
        product_name="Mobility Support Harness",
        product_category="pet_mobility",
        customer_problem="Senior dogs need safe mobility assistance.",
        target_customer="Owners of senior dogs",
        product_description="A validation-stage mobility harness direction.",
        value_proposition="Safer daily movement with simpler owner handling.",
        confidence_score=0.78,
        demand_fit_score=82,
        problem_solution_fit=78,
        estimated_price_range=ValueRange(minimum=59, maximum=89, currency="USD"),
        estimated_cost_range=ValueRange(minimum=18, maximum=28, currency="USD"),
        gross_margin_estimate=0.64,
        shipping_complexity="low",
        fulfillment_risk="low",
        ip_risk="low",
        regulatory_risk="medium",
        payment_risk="low",
        dispute_risk="low",
        strengths=["multi-source demand evidence", "low shipping complexity"],
        weaknesses=["supplier quality unvalidated"],
        assumptions=["range estimates require supplier validation"],
        missing_information=["MOQ", "lead time"],
        evidence=[
            ProductEvidenceInput(
                evidence_source="opportunity_evidence",
                source_reference=str(evidence_id),
                evidence_summary="Reviewed customer pain evidence.",
                relevance="Supports the product direction without proving commercial success.",
                confidence=0.8,
            )
        ],
    )


def test_deterministic_evaluation_is_advisory_and_creates_no_product(
    db_session: Session,
) -> None:
    before = db_session.scalar(select(func.count()).select_from(Product))
    organization, user, opportunity, evidence = foundation(db_session)
    service = OpportunityService(db_session)
    candidate = service.evaluate_candidate(
        payload(organization.id, opportunity.id, evidence.id), user.id
    )
    evaluation = service.evaluation(candidate.id, organization.id)
    assert candidate.status == "draft"
    assert evaluation.evaluation_score == 81.9
    assert evaluation.recommendation == "Suitable for further validation"
    assert evaluation.formula_version == "deterministic-product-evaluation-v1"
    assert db_session.scalar(select(func.count()).select_from(Product)) == before


def test_requires_accepted_opportunity_and_traceable_same_tenant_evidence(
    db_session: Session,
) -> None:
    organization, user, opportunity, evidence = foundation(db_session)
    opportunity.status = "draft"
    db_session.commit()
    service = OpportunityService(db_session)
    with pytest.raises(IntelligenceValidationError, match="human-accepted"):
        service.evaluate_candidate(payload(organization.id, opportunity.id, evidence.id), user.id)
    opportunity.status = "accepted"
    db_session.commit()
    invalid = payload(organization.id, opportunity.id, uuid4())
    with pytest.raises(IntelligenceScopeError, match="evidence"):
        service.evaluate_candidate(invalid, user.id)


def test_evidence_append_only_tenant_isolation_and_governance_review(
    db_session: Session,
) -> None:
    organization, user, opportunity, evidence = foundation(db_session)
    service = OpportunityService(db_session)
    candidate = service.evaluate_candidate(
        payload(organization.id, opportunity.id, evidence.id), user.id
    )
    item = service.evidence(candidate.id, organization.id)[0]
    item.relevance = "replacement"
    with pytest.raises(ValueError, match="append-only"):
        db_session.commit()
    db_session.rollback()
    with pytest.raises(IntelligenceScopeError):
        service.evidence(candidate.id, uuid4())
    with pytest.raises(IntelligenceValidationError, match="approved governance"):
        service.review(candidate, "accept", None, user.id)
    rejected = service.review(candidate, "reject", None, user.id)
    assert rejected.status == "rejected"
    assert db_session.scalar(select(func.count()).select_from(ProductCandidateEvidence)) == 1


def test_dashboard_and_authenticated_api(db_session: Session, client: TestClient) -> None:
    organization, user, opportunity, evidence = foundation(db_session)
    request = payload(organization.id, opportunity.id, evidence.id)
    response = client.post(
        "/api/v1/product-candidates",
        json=request.model_dump(mode="json"),
        headers={"X-Actor-ID": str(user.id)},
    )
    assert response.status_code == 201
    candidate = response.json()
    evaluation = client.get(
        f"/api/v1/product-candidates/{candidate['id']}/evaluation",
        params={"organization_id": str(organization.id)},
    )
    evidence_response = client.get(
        f"/api/v1/product-candidates/{candidate['id']}/evidence",
        params={"organization_id": str(organization.id)},
    )
    dashboard = client.get(
        "/api/v1/product-evaluation-dashboard",
        params={"organization_id": str(organization.id)},
    )
    assert evaluation.status_code == evidence_response.status_code == dashboard.status_code == 200
    assert evaluation.json()["recommendation"] == "Suitable for further validation"
    assert dashboard.json()["validation_queue"][0]["id"] == candidate["id"]

from uuid import UUID

from commerce_os.build.models import Product, ProductTruth
from commerce_os.finance.models import RevenueObservation
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.models import (
    ApprovalRequest,
    ApprovalStatus,
    Organization,
    Project,
    User,
)
from commerce_os.intelligence.opportunity_models import (
    CandidateStatus,
    MarketOpportunity,
    OpportunityEvidence,
    OpportunityEvidenceSource,
    OpportunityStatus,
    ProductCandidate,
    RiskLevel,
    TriggerType,
)
from commerce_os.operations.models import Brand, SalesOpportunity
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def foundation(
    session: Session, slug: str
) -> tuple[Organization, Project, User, MarketOpportunity, Product]:
    organization = Organization(name=f"E2E {slug}", slug=f"e2e-{slug}")
    session.add(organization)
    session.flush()
    project = Project(
        organization_id=organization.id, name="Cooling launch", slug=f"cooling-{slug}"
    )
    user = User(
        organization_id=organization.id,
        email=f"{slug}@example.com",
        display_name="Operator",
        status="active",
        principal_type="human",
    )
    brand = Brand(organization_id=organization.id, name="Generic", slug=f"generic-{slug}")
    session.add_all([project, user, brand])
    session.flush()
    opportunity = MarketOpportunity(
        organization_id=organization.id,
        title="Seasonal pet cooling mat",
        description="Supplied evidence indicates seasonal comfort needs",
        category="pet",
        market="consumer",
        geography="US",
        trigger_type=TriggerType.SEASONAL_EVENT,
        timing_window="summer",
        status=OpportunityStatus.QUALIFIED,
        confidence_score=0.8,
    )
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Cooling mat",
        description="Draft product",
        category="pet",
        status="draft",
    )
    session.add_all([opportunity, product])
    session.commit()
    return organization, project, user, opportunity, product


def test_incomplete_opportunity_blocks_and_retains_traceability(
    client: TestClient, db_session: Session
) -> None:
    organization, _, _, opportunity, _ = foundation(db_session, "blocked")
    response = client.get(
        f"/api/v1/opportunities/{opportunity.id}/investment-memo",
        params={"organization_id": organization.id},
    )
    assert response.status_code == 200 and response.json()["recommended_decision"] == "hold"
    assert "Market evidence is required" in response.json()["missing_evidence"]
    readiness = client.get(
        f"/api/v1/opportunities/{opportunity.id}/launch-readiness",
        params={"organization_id": organization.id},
    )
    assert readiness.json()["overall_status"] == "missing" and readiness.json()["blocking_reasons"]


def test_review_activation_plan_dashboard_and_authority_boundaries(
    client: TestClient, db_session: Session
) -> None:
    organization, project, user, opportunity, product = foundation(db_session, "activation")
    evidence = OpportunityEvidence(
        organization_id=organization.id,
        opportunity_id=opportunity.id,
        source_type=OpportunityEvidenceSource.CUSTOMER_SIGNAL,
        source_reference="supplied:signal-1",
        evidence_summary="Owners report heat discomfort",
        confidence_score=0.85,
    )
    candidate = ProductCandidate(
        organization_id=organization.id,
        opportunity_id=opportunity.id,
        product_name="Cooling mat",
        category="pet",
        customer_need="Comfort",
        estimated_margin=0.4,
        risk_level=RiskLevel.LOW,
        status=CandidateStatus.SELECTED,
    )
    db_session.add_all([evidence, candidate])
    db_session.commit()
    review = client.post(
        f"/api/v1/opportunities/{opportunity.id}/request-investment-review",
        json={
            "organization_id": str(organization.id),
            "requester_id": str(user.id),
            "project_id": str(project.id),
            "reason": "Review supplied evidence",
        },
    )
    assert review.status_code == 201
    approval = db_session.get(ApprovalRequest, UUID(review.json()["approval_request_id"]))
    assert approval is not None
    assert approval.status == ApprovalStatus.PENDING and approval.approver_id is None
    assert db_session.scalar(select(func.count()).select_from(DecisionQueueItem)) == 1
    blocked = client.post(
        f"/api/v1/opportunities/{opportunity.id}/activate-approved-project",
        json={
            "organization_id": str(organization.id),
            "approval_request_id": str(approval.id),
            "project_id": str(project.id),
            "product_id": str(product.id),
        },
    )
    assert blocked.status_code == 409
    approval.status = ApprovalStatus.APPROVED
    approval.approver_id = user.id
    db_session.commit()
    finance_before = db_session.scalar(select(func.count()).select_from(RevenueObservation))
    sales_before = db_session.scalar(select(func.count()).select_from(SalesOpportunity))
    truth_before = db_session.scalar(select(func.count()).select_from(ProductTruth))
    activated = client.post(
        f"/api/v1/opportunities/{opportunity.id}/activate-approved-project",
        json={
            "organization_id": str(organization.id),
            "approval_request_id": str(approval.id),
            "project_id": str(project.id),
            "product_id": str(product.id),
        },
    )
    assert (
        activated.status_code == 201
        and activated.json()["task_ids"]
        and activated.json()["blocker_ids"]
    )
    overview = client.get(
        f"/api/v1/projects/{project.id}/daily-action-plan",
        params={"organization_id": organization.id},
    )
    assert (
        overview.status_code == 200
        and overview.json()["launches"][0]["launch_readiness"] == "blocked"
    )
    duplicate = client.post(
        f"/api/v1/opportunities/{opportunity.id}/activate-approved-project",
        json={
            "organization_id": str(organization.id),
            "approval_request_id": str(approval.id),
            "project_id": str(project.id),
            "product_id": str(product.id),
        },
    )
    assert duplicate.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(RevenueObservation)) == finance_before
    assert db_session.scalar(select(func.count()).select_from(SalesOpportunity)) == sales_before
    assert db_session.scalar(select(func.count()).select_from(ProductTruth)) == truth_before
    assert client.post(
        f"/api/v1/projects/{project.id}/execution-overview", json={}
    ).status_code in {404, 405, 422}

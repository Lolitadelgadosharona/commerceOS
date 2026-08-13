from datetime import UTC, datetime

import pytest
from commerce_os.ai_runtime.schemas import AIRequestCreate
from commerce_os.ai_runtime.services import AIRuntimeService
from commerce_os.build.creative_asset_schemas import CreativeAssetVersionCreate
from commerce_os.build.creative_asset_services import CreativeAssetService
from commerce_os.build.creative_production_schemas import (
    CreativeAIProvenanceCreate,
    CreativeProductionRequestCreate,
    CreativeProductionWorkCreate,
    CreativeQualityReviewCreate,
    ProductionArtifactCreate,
)
from commerce_os.build.creative_production_services import CreativeProductionService
from commerce_os.build.errors import BuildScopeError, BuildStateError
from commerce_os.build.models import Product
from commerce_os.decision.creative_models import CreativeBrief, CreativeStrategy
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import (
    ApprovalRequest,
    ApprovalStatus,
    AuditLog,
    Organization,
    Project,
)
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):  # type: ignore[no-untyped-def]
    organization = Organization(name=f"Creative {slug}", slug=f"creative-{slug}")
    session.add(organization)
    session.flush()
    project = Project(organization_id=organization.id, name="Launch", slug=f"launch-{slug}")
    brand = Brand(organization_id=organization.id, name="Brand", slug=f"brand-{slug}")
    session.add_all([project, brand])
    session.flush()
    product = Product(
        organization_id=organization.id,
        name="Product",
        description="Approved product fixture",
        category="home",
        brand_id=brand.id,
        status="approved",
    )
    session.add(product)
    session.flush()
    strategy = CreativeStrategy(
        organization_id=organization.id,
        product_id=product.id,
        target_audience="Careful buyers",
        marketing_objective="Explain value",
        core_message="Evidence-backed value",
        emotional_angle="Confidence",
        creative_direction="Clear demonstration",
        status="approved",
    )
    session.add(strategy)
    session.flush()
    brief = CreativeBrief(
        organization_id=organization.id,
        product_id=product.id,
        strategy_id=strategy.id,
        platform="instagram",
        audience="Careful buyers",
        hook="Show the problem",
        story_structure="Problem and proof",
        proof_points="Approved Product Truth only",
        cta="Learn more",
        content_format="image",
        objective="Create a review candidate",
        key_message="Evidence-backed value",
        proof_requirements="Approved claims",
        cta_strategy="Human review",
        confidence=0.8,
    )
    session.add(brief)
    session.commit()
    user = AuthenticationService(session).create_user(
        organization_id=organization.id,
        email=f"creative-{slug}@example.com",
        display_name="Creative Reviewer",
        password="correct horse battery staple",
    )
    ai_request = AIRuntimeService(session).create_request(
        AIRequestCreate(
            organization_id=organization.id,
            purpose="Draft a creative concept",
            context_type="creative_brief",
            context_reference=str(brief.id),
        ),
        user.id,
    )
    return organization, project, product, brief, user, ai_request


def request_payload(organization, project, brief):  # type: ignore[no-untyped-def]
    return CreativeProductionRequestCreate(
        organization_id=organization.id,
        project_id=project.id,
        creative_brief_id=brief.id,
        format="image",
        channel="instagram",
        audience="Careful buyers",
        objective="Produce a human-reviewed candidate",
    )


def approved_request(session: Session, entities):  # type: ignore[no-untyped-def]
    organization, project, _, brief, user, _ = entities
    service = CreativeProductionService(session)
    request = service.create_request(request_payload(organization, project, brief), user.id)
    request = service.transition_request(request, "submitted", user.id)
    request = service.transition_request(request, "review", user.id)
    with pytest.raises(BuildStateError, match="Governance approval"):
        service.transition_request(request, "approved", user.id)
    approval = ApprovalRequest(
        organization_id=organization.id,
        project_id=project.id,
        requester_id=user.id,
        object_type="creative_production_request",
        object_id=request.id,
        requested_action="approve_creative_production",
        reason="Approve production workflow only",
        status=ApprovalStatus.APPROVED,
        approver_id=user.id,
        decision_time=datetime.now(UTC),
        decision_reason="Fixture approval",
    )
    session.add(approval)
    session.commit()
    return service.transition_request(request, "approved", user.id, approval.id)


def test_production_lifecycle_requires_governance_approval(db_session: Session) -> None:
    entities = foundation(db_session, "lifecycle")
    request = approved_request(db_session, entities)
    assert request.status == "approved"
    assert request.approval_state == "approved"
    actions = set(db_session.scalars(select(AuditLog.action)))
    assert "creative.production_request.approved" in actions


def test_work_ai_provenance_and_authority_boundary(db_session: Session) -> None:
    entities = foundation(db_session, "ai")
    organization, _, _, _, user, ai_request = entities
    request = approved_request(db_session, entities)
    service = CreativeProductionService(db_session)
    work = service.create_work(
        CreativeProductionWorkCreate(
            organization_id=organization.id,
            production_request_id=request.id,
            work_type="storyboard",
            title="Problem and proof storyboard",
            content_metadata={"frames": 4, "execution": "none"},
        ),
        user.id,
    )
    link = service.link_ai_provenance(
        CreativeAIProvenanceCreate(
            organization_id=organization.id,
            production_request_id=request.id,
            production_work_id=work.id,
            ai_request_id=ai_request.id,
            output_classification="draft",
            output_metadata={"artifact": "metadata-only"},
            provenance_note="No provider call was made.",
        ),
        user.id,
    )
    assert link.output_classification == "draft"
    with pytest.raises(ValidationError):
        CreativeAIProvenanceCreate(
            organization_id=organization.id,
            production_request_id=request.id,
            production_work_id=work.id,
            ai_request_id=ai_request.id,
            output_classification="publish",  # type: ignore[arg-type]
            provenance_note="Forbidden",
        )


def test_artifact_quality_version_and_distribution_boundary(db_session: Session) -> None:
    entities = foundation(db_session, "artifact")
    organization, _, product, _, user, _ = entities
    request = approved_request(db_session, entities)
    service = CreativeProductionService(db_session)
    artifact = service.create_artifact(
        ProductionArtifactCreate(
            organization_id=organization.id,
            production_request_id=request.id,
            product_id=product.id,
            asset_type="image",
            source="production-work:fixture",
            metadata={"binary_storage": "not_required"},
        ),
        user.id,
    )
    with pytest.raises(BuildStateError, match="quality review"):
        service.transition_artifact(artifact, "approved", user.id)
    review = service.review_quality(
        CreativeQualityReviewCreate(
            organization_id=organization.id,
            asset_id=artifact.id,
            brand_consistency_score=90,
            claim_safety_score=95,
            product_accuracy_score=92,
            channel_suitability_score=85,
            customer_relevance_score=88,
            recommendation="Approve candidate for distribution planning.",
        ),
        user.id,
    )
    artifact = service.transition_artifact(artifact, "approved", user.id)
    artifact = service.transition_artifact(artifact, "ready_for_distribution", user.id)
    first = CreativeAssetService(db_session).create_version(
        CreativeAssetVersionCreate(
            organization_id=organization.id,
            asset_id=artifact.id,
            variation_reason="Initial reviewed candidate",
            experiment_group="control",
        )
    )
    second = CreativeAssetService(db_session).create_version(
        CreativeAssetVersionCreate(
            organization_id=organization.id,
            asset_id=artifact.id,
            variation_reason="Alternative layout",
            experiment_group="variant-a",
        )
    )
    assert review.score == 90
    assert artifact.review_status == "ready_for_distribution"
    assert (first.version_number, second.version_number) == (1, 2)


def test_tenant_isolation_and_api_has_no_generation(
    db_session: Session, client: TestClient
) -> None:
    entities = foundation(db_session, "tenant")
    other = foundation(db_session, "other")
    organization, project, _, brief, user, _ = entities
    service = CreativeProductionService(db_session)
    with pytest.raises(BuildScopeError):
        service.create_request(request_payload(other[0], project, brief), other[4].id)
    response = client.post(
        "/api/v1/creative-production-requests",
        headers={"X-Actor-ID": str(user.id)},
        json=request_payload(organization, project, brief).model_dump(mode="json"),
    )
    assert response.status_code == 201
    assert client.post("/api/v1/creative-production-requests/generate", json={}).status_code in {
        404,
        405,
        422,
    }

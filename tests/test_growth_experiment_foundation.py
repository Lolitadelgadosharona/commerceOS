from datetime import UTC, datetime
from decimal import Decimal

import pytest
from commerce_os.build.creative_asset_models import CreativeAsset
from commerce_os.build.models import Product
from commerce_os.decision.creative_models import CreativeStrategy
from commerce_os.decision.creative_router_models import CreativePatternReference
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import (
    ApprovalRequest,
    ApprovalStatus,
    AuditLog,
    Organization,
    Project,
)
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.experiment_models import GrowthLearningObservationLink
from commerce_os.growth.experiment_schemas import (
    DistributionCampaignCreate,
    ExperimentVariantCreate,
    GrowthExperimentCreate,
    GrowthLearningSignalCreate,
    GrowthPerformanceCreate,
)
from commerce_os.growth.experiment_services import GrowthExperimentService
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):  # type: ignore[no-untyped-def]
    organization = Organization(name=f"Growth {slug}", slug=f"growth-{slug}")
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
        marketing_objective="Learn before scaling",
        core_message="Evidence-backed value",
        emotional_angle="Confidence",
        creative_direction="Clear demonstration",
        status="approved",
    )
    asset = CreativeAsset(
        organization_id=organization.id,
        product_id=product.id,
        asset_type="image",
        status="approved",
        source="human-reviewed-fixture",
        asset_metadata={"external_execution": "none"},
        approval_status="approved",
        review_status="ready_for_distribution",
        quality_score=90,
    )
    session.add_all([strategy, asset])
    session.commit()
    user = AuthenticationService(session).create_user(
        organization_id=organization.id,
        email=f"growth-{slug}@example.com",
        display_name="Growth Operator",
        password="correct horse battery staple",
    )
    return organization, project, product, strategy, asset, user


def create_experiment(session: Session, entities):  # type: ignore[no-untyped-def]
    organization, project, _, strategy, _, user = entities
    return GrowthExperimentService(session).create_experiment(
        GrowthExperimentCreate(
            organization_id=organization.id,
            project_id=project.id,
            creative_strategy_id=strategy.id,
            hypothesis="Comparison creative will improve qualified engagement.",
            objective="Measure response without external distribution.",
            audience="Careful buyers",
            channel="instagram",
        ),
        user.id,
    )


def approval(session: Session, entities, entity, object_type: str, action: str):  # type: ignore[no-untyped-def]
    organization, project, _, _, _, user = entities
    item = ApprovalRequest(
        organization_id=organization.id,
        project_id=project.id,
        requester_id=user.id,
        object_type=object_type,
        object_id=entity.id,
        requested_action=action,
        reason="Authorize a metadata-only growth state transition.",
        status=ApprovalStatus.APPROVED,
        approver_id=user.id,
        decision_time=datetime.now(UTC),
        decision_reason="Fixture approval",
    )
    session.add(item)
    session.commit()
    return item


def test_experiment_and_distribution_require_governance_approval(db_session: Session) -> None:
    entities = foundation(db_session, "approval")
    organization, _, _, _, asset, user = entities
    service = GrowthExperimentService(db_session)
    experiment = create_experiment(db_session, entities)
    experiment = service.transition_experiment(experiment, "review", user.id)
    with pytest.raises(GrowthError, match="approved Governance"):
        service.transition_experiment(experiment, "approved", user.id)
    experiment_approval = approval(
        db_session,
        entities,
        experiment,
        "growth_creative_experiment",
        "approve_growth_experiment",
    )
    experiment = service.transition_experiment(
        experiment, "approved", user.id, experiment_approval.id
    )
    experiment = service.transition_experiment(experiment, "active", user.id)
    campaign = service.create_campaign(
        DistributionCampaignCreate(
            organization_id=organization.id,
            experiment_id=experiment.id,
            creative_asset_id=asset.id,
            channel="instagram",
        ),
        user.id,
    )
    campaign = service.transition_campaign(campaign, "review", user.id)
    with pytest.raises(GrowthError, match="approved Governance"):
        service.transition_campaign(campaign, "approved", user.id)
    campaign_approval = approval(
        db_session,
        entities,
        campaign,
        "distribution_campaign",
        "approve_distribution_campaign",
    )
    campaign = service.transition_campaign(campaign, "approved", user.id, campaign_approval.id)
    campaign = service.transition_campaign(campaign, "active", user.id)
    assert campaign.lifecycle_state == "active"
    assert campaign.approval_state == "approved"
    assert "growth.distribution_campaign.active" in set(db_session.scalars(select(AuditLog.action)))


def test_performance_and_learning_preserve_ownership(db_session: Session) -> None:
    entities = foundation(db_session, "learning")
    organization, _, _, _, asset, user = entities
    service = GrowthExperimentService(db_session)
    experiment = create_experiment(db_session, entities)
    service.create_variant(
        ExperimentVariantCreate(
            organization_id=organization.id,
            experiment_id=experiment.id,
            creative_asset_id=asset.id,
            variant_name="comparison-a",
            hypothesis="Comparison framing increases useful engagement.",
            expected_outcome="Higher click-through without changing financial truth.",
        ),
        user.id,
    )
    observation = service.create_performance(
        GrowthPerformanceCreate(
            organization_id=organization.id,
            experiment_id=experiment.id,
            creative_asset_id=asset.id,
            impressions=1000,
            clicks=80,
            engagement=Decimal("0.12"),
            conversion=Decimal("0.03"),
            confidence=0.8,
        ),
        user.id,
    )
    pattern = CreativePatternReference(
        organization_id=organization.id,
        name="Comparison proof",
        pattern_type="proof_structure",
        description="Compare against the status quo with approved evidence.",
        source_reference=f"growth-observation:{observation.id}",
        performance_notes="Advisory reference; not Finance truth.",
    )
    db_session.add(pattern)
    db_session.commit()
    signal = service.create_learning(
        GrowthLearningSignalCreate(
            organization_id=organization.id,
            source_experiment_id=experiment.id,
            observation_ids=[observation.id],
            pattern_reference_id=pattern.id,
            pattern="Comparison proof correlated with qualified engagement.",
            confidence=0.75,
            recommendation="Review this pattern in the next creative strategy cycle.",
        ),
        user.id,
    )
    assert signal.pattern_reference_id == pattern.id
    assert observation.revenue_observation_id is None
    assert db_session.scalar(select(func.count()).select_from(GrowthLearningObservationLink)) == 1


def test_tenant_isolation_and_api_authentication(db_session: Session, client: TestClient) -> None:
    first = foundation(db_session, "tenant-a")
    second = foundation(db_session, "tenant-b")
    experiment = create_experiment(db_session, first)
    organization, _, _, _, _, outsider = second
    with pytest.raises(GrowthError, match="not found"):
        GrowthExperimentService(db_session).create_variant(
            ExperimentVariantCreate(
                organization_id=organization.id,
                experiment_id=experiment.id,
                creative_asset_id=second[4].id,
                variant_name="cross-tenant",
                hypothesis="Forbidden",
                expected_outcome="Forbidden",
            ),
            outsider.id,
        )
    response = client.post(
        "/api/v1/growth-experiments",
        json={
            "organization_id": str(first[0].id),
            "project_id": str(first[1].id),
            "creative_strategy_id": str(first[3].id),
            "hypothesis": "API contract",
            "objective": "No external execution",
            "audience": "Reviewers",
            "channel": "reddit",
        },
    )
    assert response.status_code == 401
